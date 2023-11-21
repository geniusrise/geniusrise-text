# 🧠 Geniusrise
# Copyright (C) 2023  geniusrise.ai
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from typing import Any, Dict, List, Optional, Union
import json
import os
import sqlite3
import xml.etree.ElementTree as ET
import pandas as pd
import yaml  # type: ignore
from datasets import Dataset, load_from_disk
from pyarrow import feather
from pyarrow import parquet as pq
import uuid
from geniusrise import BatchInput, BatchOutput, State
from geniusrise_text.base import TextBulk


class TextSummarizationBulk(TextBulk):
    """
    A class for bulk text summarization using Hugging Face models.
    """

    def __init__(self, input: BatchInput, output: BatchOutput, state: State, **kwargs) -> None:
        super().__init__(input, output, state, **kwargs)

    def load_dataset(self, dataset_path: str, max_length: int = 512, **kwargs) -> Optional[Dataset]:
        """
        Load a summarization dataset from a directory.
        """
        try:
            if os.path.isfile(os.path.join(dataset_path, "dataset_info.json")):
                dataset = load_from_disk(dataset_path)
            else:
                data = []
                for filename in os.listdir(dataset_path):
                    filepath = os.path.join(dataset_path, filename)
                    if filename.endswith(".jsonl"):
                        with open(filepath, "r") as f:
                            for line in f:
                                example = json.loads(line)
                                data.append(example)
                    elif filename.endswith(".csv"):
                        df = pd.read_csv(filepath)
                        data.extend(df.to_dict("records"))
                    elif filename.endswith(".parquet"):
                        df = pq.read_table(filepath).to_pandas()
                        data.extend(df.to_dict("records"))
                    elif filename.endswith(".json"):
                        with open(filepath, "r") as f:
                            json_data = json.load(f)
                            data.extend(json_data)
                    elif filename.endswith(".xml"):
                        tree = ET.parse(filepath)
                        root = tree.getroot()
                        for record in root.findall("record"):
                            document = record.find("document").text  # type: ignore
                            data.append({"document": document})
                    elif filename.endswith(".yaml") or filename.endswith(".yml"):
                        with open(filepath, "r") as f:
                            yaml_data = yaml.safe_load(f)
                            data.extend(yaml_data)
                    elif filename.endswith(".tsv"):
                        df = pd.read_csv(filepath, sep="\t")
                        data.extend(df.to_dict("records"))
                    elif filename.endswith((".xls", ".xlsx")):
                        df = pd.read_excel(filepath)
                        data.extend(df.to_dict("records"))
                    elif filename.endswith(".db"):
                        conn = sqlite3.connect(filepath)
                        query = "SELECT document FROM dataset_table;"
                        df = pd.read_sql_query(query, conn)
                        data.extend(df.to_dict("records"))
                    elif filename.endswith(".feather"):
                        df = feather.read_feather(filepath)
                        data.extend(df.to_dict("records"))

                if hasattr(self, "map_data") and self.map_data:
                    fn = eval(self.map_data)  # type: ignore
                    data = [fn(d) for d in data]
                else:
                    data = data

                dataset = Dataset.from_pandas(pd.DataFrame(data))
            return dataset

        except Exception as e:
            self.log.exception(f"Error occurred when loading dataset from {dataset_path}. Error: {e}")
            raise

    def summarize(
        self,
        model_name: str,
        tokenizer_name: str,
        model_revision: Optional[str] = None,
        tokenizer_revision: Optional[str] = None,
        model_class: str = "AutoModelForSeq2SeqLM",
        tokenizer_class: str = "AutoTokenizer",
        use_cuda: bool = False,
        precision: str = "float16",
        quantization: int = 0,
        device_map: Union[str, Dict, None] = "auto",
        max_memory={0: "24GB"},
        torchscript: bool = True,
        batch_size: int = 32,
        **kwargs: Any,
    ) -> None:
        """
        Perform bulk text summarization.
        """
        self.model, self.tokenizer = self.load_models(
            model_name=model_name,
            tokenizer_name=tokenizer_name,
            model_revision=model_revision,
            tokenizer_revision=tokenizer_revision,
            model_class=model_class,
            tokenizer_class=tokenizer_class,
            use_cuda=use_cuda,
            precision=precision,
            quantization=quantization,
            device_map=device_map,
            max_memory=max_memory,
            torchscript=torchscript,
            **kwargs,
        )

        dataset_path = self.input.input_folder
        output_path = self.output.output_folder

        # Load dataset
        _dataset = self.load_dataset(dataset_path)
        if _dataset is None:
            self.log.error("Failed to load dataset.")
            return
        dataset = _dataset["text"]

        # Process data in batches
        for i in range(0, len(dataset), batch_size):
            batch = dataset[i : i + batch_size]
            inputs = self.tokenizer(batch, return_tensors="pt", padding=True, truncation=True)

            if next(self.model.parameters()).is_cuda:
                inputs = {k: v.cuda() for k, v in inputs.items()}

            # Generate summaries
            summaries = self.model.generate(**inputs)
            if next(self.model.parameters()).is_cuda:
                summaries = summaries.cpu()

            decoded_summaries = [self.tokenizer.decode(s, skip_special_tokens=True) for s in summaries]

            self._save_summaries(decoded_summaries, batch, output_path, i)

    def _save_summaries(self, summaries: List[str], input_batch: List[str], output_path: str, batch_idx: int) -> None:
        """
        Save the generated summaries to disk.
        """
        data_to_save = [
            {"input": input_text, "summary": summary} for input_text, summary in zip(input_batch, summaries)
        ]
        with open(os.path.join(output_path, f"summaries-{batch_idx}-{str(uuid.uuid4())}.json"), "w") as f:
            json.dump(data_to_save, f)
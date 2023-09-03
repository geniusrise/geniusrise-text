# 🧠 Geniusrise
# Copyright (C) 2023  geniusrise.ai
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
import tempfile
import pytest
import numpy as np
from datasets import load_from_disk
from huggingface.base import HuggingFaceFineTuner
from huggingface.language_model import HuggingFaceLanguageModelingFineTuner
from geniusrise.core import BatchInput, BatchOutput, InMemoryState
from transformers import EvalPrediction
import pandas as pd
import json
import sqlite3
import xml.etree.ElementTree as ET
import yaml
from pyarrow import feather, parquet as pq


# Helper function to create synthetic data in different formats
def create_dataset_in_format(directory, ext):
    os.makedirs(directory, exist_ok=True)
    data = [{"text": f"text_{i}"} for i in range(10)]
    if ext == "huggingface":
        dataset = load_from_disk(directory)
    elif ext == "csv":
        df.to_csv(os.path.join(directory, "data.csv"), index=False)
    elif ext == "jsonl":
        with open(os.path.join(directory, "data.jsonl"), "w") as f:
            for item in data:
                f.write(json.dumps(item) + "\n")
    elif ext == "parquet":
        pq.write_table(feather.Table.from_pandas(df), os.path.join(directory, "data.parquet"))
    elif ext == "json":
        with open(os.path.join(directory, "data.json"), "w") as f:
            json.dump(data, f)
    elif ext == "xml":
        root = ET.Element("root")
        for item in data:
            record = ET.SubElement(root, "record")
            ET.SubElement(record, "text").text = item["text"]
            ET.SubElement(record, "label").text = item["label"]
        tree = ET.ElementTree(root)
        tree.write(os.path.join(directory, "data.xml"))
    elif ext == "yaml":
        with open(os.path.join(directory, "data.yaml"), "w") as f:
            yaml.dump(data, f)
    elif ext == "tsv":
        df.to_csv(os.path.join(directory, "data.tsv"), index=False, sep="\t")
    elif ext == "xlsx":
        df.to_excel(os.path.join(directory, "data.xlsx"), index=False)
    elif ext == "db":
        conn = sqlite3.connect(os.path.join(directory, "data.db"))
        df.to_sql("dataset_table", conn, if_exists="replace", index=False)
        conn.close()
    elif ext == "feather":
        feather.write_feather(df, os.path.join(directory, "data.feather"))


# Fixtures for each file type
@pytest.fixture(
    params=["huggingface", "csv", "json", "jsonl", "parquet", "xml", "yaml", "tsv", "xlsx", "db", "feather"]
)
def dataset_file(request, tmpdir):
    ext = request.param
    create_dataset_in_format(tmpdir, ext)
    return tmpdir, ext


@pytest.fixture
def language_modeling_bolt():
    input_dir = tempfile.mkdtemp()
    output_dir = tempfile.mkdtemp()
    input = BatchInput(input_dir, "geniusrise-test-bucket", "test-🤗-input")
    output = BatchOutput(output_dir, "geniusrise-test-bucket", "test-🤗-output")
    state = InMemoryState()
    return HuggingFaceLanguageModelingFineTuner(
        input=input,
        output=output,
        state=state,
    )


def test_language_modeling_bolt_init(language_modeling_bolt):
    language_modeling_bolt.load_models()
    assert language_modeling_bolt.model is not None
    assert language_modeling_bolt.tokenizer is not None
    assert language_modeling_bolt.input is not None
    assert language_modeling_bolt.output is not None
    assert language_modeling_bolt.state is not None


def test_load_dataset_all_formats(language_modeling_bolt, dataset_file):
    tmpdir, ext = dataset_file
    dataset_path = os.path.join(tmpdir, "train")
    language_modeling_bolt.load_models()
    dataset = language_modeling_bolt.load_dataset(dataset_path)
    assert dataset is not None
    assert len(dataset) == 10


def test_language_modeling_bolt_fine_tune(language_modeling_bolt, dataset_file):
    tmpdir, ext = dataset_file
    language_modeling_bolt.input.input_folder = tmpdir
    language_modeling_bolt.load_models()
    language_modeling_bolt.fine_tune(
        model_name="gpt2",
        tokenizer_name="gpt2",
        num_train_epochs=1,
        per_device_train_batch_size=1,
    )
    output_dir = language_modeling_bolt.output.output_folder
    assert os.path.isfile(os.path.join(output_dir + "/model", "pytorch_model.bin"))
    assert os.path.isfile(os.path.join(output_dir + "/model", "config.json"))
    assert os.path.isfile(os.path.join(output_dir + "/model", "training_args.bin"))


def test_language_modeling_bolt_compute_metrics(language_modeling_bolt):
    logits = np.array([[0.6, 0.4], [0.4, 0.6]])
    labels = np.array([[0, 1], [1, 0]])
    eval_pred = EvalPrediction(predictions=logits, label_ids=labels)
    metrics = language_modeling_bolt.compute_metrics(eval_pred)
    assert "bleu" in metrics

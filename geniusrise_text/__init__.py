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

from .classification import TextClassificationFineTuner
from .classification import TextClassificationAPI
from .classification import TextClassificationBulk

from .embeddings import EmbeddingsAPI
from .embeddings import EmbeddingsBulk

from .instruction import InstructionAPI
from .instruction import InstructionBulk
from .instruction import TextInstructionTuningFineTuner

from .language_model import LanguageModelingFineTuner
from .language_model import LanguageModelBulk
from .language_model import LanguageModelAPI

# TODO: NER API
from .ner import NamedEntityRecognitionBulk
from .ner import NamedEntityRecognitionFineTuner

# TODO: NLI API
from .nli import NLIBulk
from .nli import NLIFineTuner
from .nli import NLIAPI

# TODO: QA API
from .qa import TextQABulk
from .qa import QuestionAnsweringFineTuner
from .qa import QuestionAnsweringAPI

# TODO: summarization API
from .summarization import TextSummarizationBulk
from .summarization import SummarizationFineTuner

# TODO: translation API
from .translation import TextTranslationBulk
from .translation import TranslationFineTuner

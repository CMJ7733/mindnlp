# Copyright 2021 The HuggingFace Team. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Speech2Text model init"""
from typing import TYPE_CHECKING

from . import configuration_speech_to_text, modeling_speech_to_text, tokenization_speech_to_text
from .configuration_speech_to_text import *
from .modeling_speech_to_text import *
from .tokenization_speech_to_text import *
__all__ = []
__all__.extend(configuration_speech_to_text.__all__)
__all__.extend(modeling_speech_to_text.__all__)
__all__.extend(tokenization_speech_to_text.__all__)

_import_structure = {
    "configuration_speech_to_text": ["Speech2TextConfig"],
    "modeling_speech_to_text": [
        "Speech2TextForConditionalGeneration",
        "Speech2TextModel",
        "Speech2TextPreTrainedModel",
    ],
    "tokenization_speech_to_text": ["Speech2TextTokenizer"],
}

# coding=utf-8
# Copyright 2020 The Trax Authors and The HuggingFace Inc. team.
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
# ============================================================================
""" Tokenization class for model Reformer."""


import os
from shutil import copyfile
from typing import Any, Dict, List, Optional, Tuple

import sentencepiece as spm

from mindnlp.utils import logging
from ...tokenization_utils import PreTrainedTokenizer


logger = logging.get_logger(__name__)


SPIECE_UNDERLINE = "▁"

VOCAB_FILES_NAMES = {"vocab_file": "spiece.model"}

PRETRAINED_VOCAB_FILES_MAP = {
    "vocab_file": {
        "google/reformer-crime-and-punishment": (
            "https://hf-mirror.com/google/reformer-crime-and-punishment/resolve/main/spiece.model"
        )
    }
}

PRETRAINED_POSITIONAL_EMBEDDINGS_SIZES = {
    "google/reformer-crime-and-punishment": 524288,
}


class ReformerTokenizer(PreTrainedTokenizer):
    """
    Construct a Reformer tokenizer. Based on [SentencePiece](https://github.com/google/sentencepiece) .

    This tokenizer inherits from [`PreTrainedTokenizer`] which contains most of the main methods. Users should refer to
    this superclass for more information regarding those methods.

    Args:
        vocab_file (`str`):
            [SentencePiece](https://github.com/google/sentencepiece) file (generally has a *.spm* extension) that
            contains the vocabulary necessary to instantiate a tokenizer.
        eos_token (`str`, *optional*, defaults to `"</s>"`):
            The end of sequence token.

            <Tip>

            When building a sequence using special tokens, this is not the token that is used for the end of sequence.
            The token used is the `sep_token`.

            </Tip>

        unk_token (`str`, *optional*, defaults to `"<unk>"`):
            The unknown token. A token that is not in the vocabulary cannot be converted to an ID and is set to be this
            token instead.
        additional_special_tokens (`List[str]`, *optional*, defaults to `[]`):
            Additional special tokens used by the tokenizer.
        sp_model_kwargs (`dict`, *optional*):
            Will be passed to the `SentencePieceProcessor.__init__()` method. The [Python wrapper for
            SentencePiece](https://github.com/google/sentencepiece/tree/master/python) can be used, among other things,
            to set:

            - `enable_sampling`: Enable subword regularization.
            - `nbest_size`: Sampling parameters for unigram. Invalid for BPE-Dropout.

              - `nbest_size = {0,1}`: No sampling is performed.
              - `nbest_size > 1`: samples from the nbest_size results.
              - `nbest_size < 0`: assuming that nbest_size is infinite and samples from the all hypothesis (lattice)
                using forward-filtering-and-backward-sampling algorithm.

            - `alpha`: Smoothing parameter for unigram sampling, and dropout probability of merge operations for
              BPE-dropout.
    """
    vocab_files_names = VOCAB_FILES_NAMES
    pretrained_vocab_files_map = PRETRAINED_VOCAB_FILES_MAP
    max_model_input_sizes = PRETRAINED_POSITIONAL_EMBEDDINGS_SIZES
    model_input_names = ["input_ids", "attention_mask"]

    def __init__(
        self,
        vocab_file,
        eos_token="</s>",
        unk_token="<unk>",
        additional_special_tokens=[],
        sp_model_kwargs: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> None:
        """
        Initializes a new instance of the ReformerTokenizer class.
        
        Args:
            self: The instance of the ReformerTokenizer class.
            vocab_file (str): Path to the vocabulary file.
            eos_token (str, optional): The end-of-sentence token. Defaults to '</s>'.
            unk_token (str, optional): The unknown token. Defaults to '<unk>'.
            additional_special_tokens (List[str], optional): Additional special tokens to be added to the vocabulary. Defaults to an empty list.
            sp_model_kwargs (Optional[Dict[str, Any]], optional): Additional arguments to be passed to the SentencePieceProcessor constructor. Defaults to None.
        
        Returns:
            None
        
        Raises:
            None
        """
        self.sp_model_kwargs = {} if sp_model_kwargs is None else sp_model_kwargs

        self.vocab_file = vocab_file
        self.sp_model = spm.SentencePieceProcessor(**self.sp_model_kwargs)
        self.sp_model.Load(vocab_file)

        super().__init__(
            eos_token=eos_token,
            unk_token=unk_token,
            additional_special_tokens=additional_special_tokens,
            sp_model_kwargs=self.sp_model_kwargs,
            **kwargs,
        )

    @property
    def vocab_size(self):
        """
        Returns the size of the vocabulary used by the ReformerTokenizer.
        
        Args:
            self: The instance of the ReformerTokenizer class.
        
        Returns:
            int: The size of the vocabulary used by the ReformerTokenizer.
        
        Raises:
            None.
        """
        return self.sp_model.get_piece_size()

    def get_vocab(self) -> Dict[str, int]:
        """
        Get the vocabulary of the ReformerTokenizer.
        
        Args:
            self: An instance of the ReformerTokenizer class.
        
        Returns:
            A dictionary of type Dict[str, int] mapping tokens to their corresponding IDs. The IDs are integers.
        
        Raises:
            None.
        
        """
        vocab = {self.convert_ids_to_tokens(i): i for i in range(self.vocab_size)}
        vocab.update(self.added_tokens_encoder)
        return vocab

    def __getstate__(self):
        """
        Method '__getstate__' in the class 'ReformerTokenizer'.
        
        Args:
            self (object): The instance of the ReformerTokenizer class.
                Represents the current instance of the ReformerTokenizer class.
                No restrictions.
        
        Returns:
            None.
            This method returns a dictionary containing the state of the ReformerTokenizer instance with the 'sp_model' key set to None.
        
        Raises:
            None.
        """
        state = self.__dict__.copy()
        state["sp_model"] = None
        return state

    def __setstate__(self, d):
        """
        __setstate__ method in the class ReformerTokenizer.
        
        Args:
            self (object): The instance of the ReformerTokenizer class.
            d (dict): A dictionary containing the state information to be set.
        
        Returns:
            None: This method does not return any value.
        
        Raises:
            N/A: This method does not explicitly raise any exceptions.
        """
        self.__dict__ = d

        # for backward compatibility
        if not hasattr(self, "sp_model_kwargs"):
            self.sp_model_kwargs = {}

        self.sp_model = spm.SentencePieceProcessor(**self.sp_model_kwargs)
        self.sp_model.Load(self.vocab_file)

    def _tokenize(self, text: str) -> List[str]:
        """Take as input a string and return a list of strings (tokens) for words/sub-words"""
        return self.sp_model.encode(text, out_type=str)

    def _convert_token_to_id(self, token):
        """Converts a token (str) in an id using the vocab."""
        return self.sp_model.piece_to_id(token)

    def _convert_id_to_token(self, index):
        """Converts an index (integer) in a token (str) using the vocab."""
        if index < self.sp_model.get_piece_size():
            token = self.sp_model.IdToPiece(index)
        return token

    def convert_tokens_to_string(self, tokens):
        """Converts a sequence of tokens (string) in a single string."""
        current_sub_tokens = []
        out_string = ""
        for token in tokens:
            # make sure that special tokens are not decoded using sentencepiece model
            if token in self.all_special_tokens:
                out_string += self.sp_model.decode(current_sub_tokens) + token
                current_sub_tokens = []
            else:
                current_sub_tokens.append(token)
        out_string += self.sp_model.decode(current_sub_tokens)
        return out_string.strip()

    def save_vocabulary(self, save_directory: str, filename_prefix: Optional[str] = None) -> Tuple[str]:
        """
        Save the vocabulary to a specified directory.
        
        Args:
            self (ReformerTokenizer): The instance of the ReformerTokenizer class.
            save_directory (str): The directory where the vocabulary will be saved.
            filename_prefix (Optional[str], optional): An optional prefix for the filename. Defaults to None.
        
        Returns:
            Tuple[str]: A tuple containing the path to the saved vocabulary file.
        
        Raises:
            OSError: If the save_directory is not a valid directory.
        """
        if not os.path.isdir(save_directory):
            logger.error(f"Vocabulary path ({save_directory}) should be a directory")
            return
        out_vocab_file = os.path.join(
            save_directory, (filename_prefix + "-" if filename_prefix else "") + VOCAB_FILES_NAMES["vocab_file"]
        )

        if os.path.abspath(self.vocab_file) != os.path.abspath(out_vocab_file) and os.path.isfile(self.vocab_file):
            copyfile(self.vocab_file, out_vocab_file)
        elif not os.path.isfile(self.vocab_file):
            with open(out_vocab_file, "wb") as fi:
                content_spiece_model = self.sp_model.serialized_model_proto()
                fi.write(content_spiece_model)

        return (out_vocab_file,)

__all__ = ['ReformerTokenizer']

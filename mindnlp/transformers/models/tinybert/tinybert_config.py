# Copyright 2022 Huawei Technologies Co., Ltd
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ============================================================================
"""
TinyBert Models config
"""

from ...configuration_utils import PretrainedConfig

TINYBERT_SUPPORT_LIST = ['tinybert_4L_zh', 'tinybert_6L_zh']


class TinyBertConfig(PretrainedConfig):
    """
    Configuration class to store the configuration of a `BertModel`.

    Args:
        vocab_size_or_config_json_file: Vocabulary size of `inputs_ids` in `BertModel`.
        hidden_size: Size of the encoder layers and the pooler layer.
        num_hidden_layers: Number of hidden layers in the Transformer encoder.
        num_attention_heads: Number of attention heads for each attention layer in
            the Transformer encoder.
        intermediate_size: The size of the "intermediate" (i.e., feed-forward)
            layer in the Transformer encoder.
        hidden_act: The non-linear activation function (function or string) in the
            encoder and pooler. If string, "gelu", "relu" and "swish" are supported.
        hidden_dropout_prob: The dropout probabilitiy for all fully connected
            layers in the embeddings, encoder, and pooler.
        attention_probs_dropout_prob: The dropout ratio for the attention
            probabilities.
        max_position_embeddings: The maximum sequence length that this model might
            ever be used with. Typically set this to something large just in case
            (e.g., 512 or 1024 or 2048).
        type_vocab_size: The vocabulary size of the `token_type_ids` passed into
            `BertModel`.
        initializer_range: The sttdev of the truncated_normal_initializer for
            initializing all weight matrices.
    """
    def __init__(self,
                 vocab_size=21128,
                 hidden_size=768,
                 num_hidden_layers=12,
                 num_attention_heads=12,
                 intermediate_size=3072,
                 hidden_act="gelu",
                 hidden_dropout_prob=0.1,
                 attention_probs_dropout_prob=0.1,
                 max_position_embeddings=512,
                 type_vocab_size=2,
                 initializer_range=0.02,
                 pre_trained='',
                 training='',
                 **kwargs):
        """
        Initializes a new instance of the TinyBertConfig class.
        
        Args:
            vocab_size (int, optional): The size of the vocabulary. Defaults to 21128.
            hidden_size (int, optional): The size of the hidden layers. Defaults to 768.
            num_hidden_layers (int, optional): The number of hidden layers. Defaults to 12.
            num_attention_heads (int, optional): The number of attention heads. Defaults to 12.
            intermediate_size (int, optional): The size of the intermediate layer. Defaults to 3072.
            hidden_act (str, optional): The activation function for the hidden layers. Defaults to 'gelu'.
            hidden_dropout_prob (float, optional): The dropout probability for the hidden layers. Defaults to 0.1.
            attention_probs_dropout_prob (float, optional): The dropout probability for the attention probabilities. Defaults to 0.1.
            max_position_embeddings (int, optional): The maximum number of tokens in a sequence. Defaults to 512.
            type_vocab_size (int, optional): The size of the type vocabulary. Defaults to 2.
            initializer_range (float, optional): The range of the initializer. Defaults to 0.02.
            pre_trained (str, optional): The path to a pre-trained model. Defaults to ''.
            training (str, optional): The training option. Defaults to ''.
            **kwargs: Additional keyword arguments.
        
        Returns:
            None
        
        Raises:
            None
        """
        super().__init__()
        self.vocab_size = vocab_size
        self.hidden_size = hidden_size
        self.num_hidden_layers = num_hidden_layers
        self.num_attention_heads = num_attention_heads
        self.hidden_act = hidden_act
        self.intermediate_size = intermediate_size
        self.hidden_dropout_prob = hidden_dropout_prob
        self.attention_probs_dropout_prob = attention_probs_dropout_prob
        self.max_position_embeddings = max_position_embeddings
        self.type_vocab_size = type_vocab_size
        self.initializer_range = initializer_range
        self.pre_trained = pre_trained
        self.training = training

__all__ = ['TinyBertConfig']

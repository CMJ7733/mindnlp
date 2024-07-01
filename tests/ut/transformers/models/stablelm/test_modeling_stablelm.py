# coding=utf-8
# Copyright 2024 The HuggingFace Inc. team. All rights reserved.
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
"""Testing suite for the PyTorch StableLm model."""

import unittest
import pytest

from parameterized import parameterized
import numpy as np
from mindnlp.transformers import StableLmConfig
from mindnlp.utils import is_mindspore_available
from mindnlp.engine import set_seed
from mindnlp.utils.testing_utils import (
    is_flaky,
    require_mindspore,
    slow,
)

from ...generation.test_utils import GenerationTesterMixin
from ...test_configuration_common import ConfigTester
from ...test_modeling_common import ModelTesterMixin, ids_tensor
# from ...test_pipeline_mixin import PipelineTesterMixin


if is_mindspore_available():
    import mindspore
    from mindspore import ops

    from mindnlp.transformers import (
        AutoTokenizer,
        StableLmForCausalLM,
        StableLmForSequenceClassification,
        StableLmForTokenClassification,
        StableLmModel,
    )
    from mindnlp.transformers.models.stablelm.modeling_stablelm import (
        StableLmDynamicNTKScalingRotaryEmbedding,
        StableLmLinearScalingRotaryEmbedding,
        StableLmRotaryEmbedding,
    )


# Copied from transformers.tests.models.persimmon.test_modeling_persimmon.PersimmonModelTester with Persimmon -> StableLm
class StableLmModelTester:
    # Ignore copy
    def __init__(
        self,
        parent,
        batch_size=13,
        seq_length=7,
        is_training=True,
        use_input_mask=True,
        use_token_type_ids=False,
        use_labels=True,
        vocab_size=99,
        hidden_size=64,
        num_hidden_layers=2,
        num_attention_heads=4,
        num_key_value_heads=4,
        intermediate_size=37,
        hidden_act="gelu",
        hidden_dropout_prob=0.1,
        attention_probs_dropout_prob=0.1,
        max_position_embeddings=512,
        type_vocab_size=16,
        type_sequence_label_size=2,
        initializer_range=0.02,
        num_labels=3,
        num_choices=4,
        pad_token_id=0,
        scope=None,
    ):
        self.parent = parent
        self.batch_size = batch_size
        self.seq_length = seq_length
        self.is_training = is_training
        self.use_input_mask = use_input_mask
        self.use_token_type_ids = use_token_type_ids
        self.use_labels = use_labels
        self.vocab_size = vocab_size
        self.hidden_size = hidden_size
        self.num_hidden_layers = num_hidden_layers
        self.num_attention_heads = num_attention_heads
        self.num_key_value_heads = num_key_value_heads
        self.intermediate_size = intermediate_size
        self.hidden_act = hidden_act
        self.hidden_dropout_prob = hidden_dropout_prob
        self.attention_probs_dropout_prob = attention_probs_dropout_prob
        self.max_position_embeddings = max_position_embeddings
        self.type_vocab_size = type_vocab_size
        self.type_sequence_label_size = type_sequence_label_size
        self.initializer_range = initializer_range
        self.num_labels = num_labels
        self.num_choices = num_choices
        self.pad_token_id = pad_token_id
        self.scope = scope

    def prepare_config_and_inputs(self):
        input_ids = ids_tensor([self.batch_size, self.seq_length], self.vocab_size)

        input_mask = None
        if self.use_input_mask:
            input_mask = ops.tril(ops.ones(self.batch_size, self.seq_length))

        token_type_ids = None
        if self.use_token_type_ids:
            token_type_ids = ids_tensor([self.batch_size, self.seq_length], self.type_vocab_size)

        sequence_labels = None
        token_labels = None
        choice_labels = None
        if self.use_labels:
            sequence_labels = ids_tensor([self.batch_size], self.type_sequence_label_size)
            token_labels = ids_tensor([self.batch_size, self.seq_length], self.num_labels)
            choice_labels = ids_tensor([self.batch_size], self.num_choices)

        config = self.get_config()

        return config, input_ids, token_type_ids, input_mask, sequence_labels, token_labels, choice_labels

    def get_config(self):
        return StableLmConfig(
            vocab_size=self.vocab_size,
            hidden_size=self.hidden_size,
            num_hidden_layers=self.num_hidden_layers,
            num_attention_heads=self.num_attention_heads,
            num_key_value_heads=self.num_key_value_heads,
            intermediate_size=self.intermediate_size,
            hidden_act=self.hidden_act,
            hidden_dropout_prob=self.hidden_dropout_prob,
            attention_probs_dropout_prob=self.attention_probs_dropout_prob,
            max_position_embeddings=self.max_position_embeddings,
            type_vocab_size=self.type_vocab_size,
            is_decoder=False,
            initializer_range=self.initializer_range,
            pad_token_id=self.pad_token_id,
        )

    def create_and_check_model(
        self, config, input_ids, token_type_ids, input_mask, sequence_labels, token_labels, choice_labels
    ):
        model = StableLmModel(config=config)
        model.set_train(False)
        result = model(input_ids, attention_mask=input_mask)
        result = model(input_ids)
        self.parent.assertEqual(result.last_hidden_state.shape, (self.batch_size, self.seq_length, self.hidden_size))

    def create_and_check_model_as_decoder(
        self,
        config,
        input_ids,
        token_type_ids,
        input_mask,
        sequence_labels,
        token_labels,
        choice_labels,
        encoder_hidden_states,
        encoder_attention_mask,
    ):
        config.add_cross_attention = True
        model = StableLmModel(config)
        model.set_train(False)
        result = model(
            input_ids,
            attention_mask=input_mask,
            encoder_hidden_states=encoder_hidden_states,
            encoder_attention_mask=encoder_attention_mask,
        )
        result = model(
            input_ids,
            attention_mask=input_mask,
            encoder_hidden_states=encoder_hidden_states,
        )
        result = model(input_ids, attention_mask=input_mask)
        self.parent.assertEqual(result.last_hidden_state.shape, (self.batch_size, self.seq_length, self.hidden_size))

    def create_and_check_for_causal_lm(
        self,
        config,
        input_ids,
        token_type_ids,
        input_mask,
        sequence_labels,
        token_labels,
        choice_labels,
        encoder_hidden_states,
        encoder_attention_mask,
    ):
        model = StableLmForCausalLM(config=config)
        model.set_train(False)
        result = model(input_ids, attention_mask=input_mask, labels=token_labels)
        self.parent.assertEqual(result.logits.shape, (self.batch_size, self.seq_length, self.vocab_size))

    def create_and_check_decoder_model_past_large_inputs(
        self,
        config,
        input_ids,
        token_type_ids,
        input_mask,
        sequence_labels,
        token_labels,
        choice_labels,
        encoder_hidden_states,
        encoder_attention_mask,
    ):
        config.is_decoder = True
        config.add_cross_attention = True
        model = StableLmForCausalLM(config=config)
        model.set_train(False)

        # first forward pass
        outputs = model(
            input_ids,
            attention_mask=input_mask,
            encoder_hidden_states=encoder_hidden_states,
            encoder_attention_mask=encoder_attention_mask,
            use_cache=True,
        )
        past_key_values = outputs.past_key_values

        # create hypothetical multiple next token and extent to next_input_ids
        next_tokens = ids_tensor((self.batch_size, 3), config.vocab_size)
        next_mask = ids_tensor((self.batch_size, 3), vocab_size=2)

        # append to next input_ids and
        next_input_ids = ops.cat([input_ids, next_tokens], axis=-1)
        next_attention_mask = ops.cat([input_mask, next_mask], axis=-1)

        output_from_no_past = model(
            next_input_ids,
            attention_mask=next_attention_mask,
            encoder_hidden_states=encoder_hidden_states,
            encoder_attention_mask=encoder_attention_mask,
            output_hidden_states=True,
        )["hidden_states"][0]
        output_from_past = model(
            next_tokens,
            attention_mask=next_attention_mask,
            encoder_hidden_states=encoder_hidden_states,
            encoder_attention_mask=encoder_attention_mask,
            past_key_values=past_key_values,
            output_hidden_states=True,
        )["hidden_states"][0]

        # select random slice
        random_slice_idx = ids_tensor((1,), output_from_past.shape[-1]).item()
        output_from_no_past_slice = output_from_no_past[:, -3:, random_slice_idx]
        output_from_past_slice = output_from_past[:, :, random_slice_idx]

        self.parent.assertTrue(output_from_past_slice.shape[1] == next_tokens.shape[1])

        # test that outputs are equal for slice
        self.parent.assertTrue(np.allclose(output_from_past_slice.asnumpy(), output_from_no_past_slice.asnumpy(), atol=1e-3))

    def prepare_config_and_inputs_for_common(self):
        config_and_inputs = self.prepare_config_and_inputs()
        (
            config,
            input_ids,
            token_type_ids,
            input_mask,
            sequence_labels,
            token_labels,
            choice_labels,
        ) = config_and_inputs
        inputs_dict = {"input_ids": input_ids, "attention_mask": input_mask}
        return config, inputs_dict


@require_mindspore
# Copied from transformers.tests.persimmon.test_modeling_persimmon.PersimmonModelTest with Persimmon -> StableLm
class StableLmModelTest(ModelTesterMixin, GenerationTesterMixin, unittest.TestCase):
    all_model_classes = (
        (StableLmModel, StableLmForCausalLM, StableLmForSequenceClassification, StableLmForTokenClassification)
        if is_mindspore_available()
        else ()
    )
    pipeline_model_mapping = (
        {
            "feature-extraction": StableLmModel,
            "text-classification": StableLmForSequenceClassification,
            "token-classification": StableLmForTokenClassification,
            # TODO (ydshieh): check why these two fail. Fix them or skip them in a better way.
            # "text-generation": StableLmForCausalLM,
            # "zero-shot": StableLmForSequenceClassification,
        }
        if is_mindspore_available()
        else {}
    )

    all_generative_model_classes = (StableLmForCausalLM,) if is_mindspore_available() else ()
    test_headmasking = False
    test_pruning = False

    def setUp(self):
        self.model_tester = StableLmModelTester(self)
        self.config_tester = ConfigTester(self, config_class=StableLmConfig, hidden_size=37)

    def test_config(self):
        self.config_tester.run_common_tests()

    def test_model(self):
        config_and_inputs = self.model_tester.prepare_config_and_inputs()
        self.model_tester.create_and_check_model(*config_and_inputs)

    def test_stablelm_sequence_classification_model(self):
        config, input_dict = self.model_tester.prepare_config_and_inputs_for_common()
        config.num_labels = 3
        input_ids = input_dict["input_ids"]
        attention_mask = input_ids.ne(1)
        sequence_labels = ids_tensor([self.model_tester.batch_size], self.model_tester.type_sequence_label_size)
        model = StableLmForSequenceClassification(config)
        model.set_train(False)
        result = model(input_ids, attention_mask=attention_mask, labels=sequence_labels)
        self.assertEqual(result.logits.shape, (self.model_tester.batch_size, self.model_tester.num_labels))

    def test_stablelm_sequence_classification_model_for_single_label(self):
        config, input_dict = self.model_tester.prepare_config_and_inputs_for_common()
        config.num_labels = 3
        config.problem_type = "single_label_classification"
        input_ids = input_dict["input_ids"]
        attention_mask = input_ids.ne(1)
        sequence_labels = ids_tensor([self.model_tester.batch_size], self.model_tester.type_sequence_label_size)
        model = StableLmForSequenceClassification(config)
        model.set_train(False)
        result = model(input_ids, attention_mask=attention_mask, labels=sequence_labels)
        self.assertEqual(result.logits.shape, (self.model_tester.batch_size, self.model_tester.num_labels))

    def test_stablelm_sequence_classification_model_for_multi_label(self):
        config, input_dict = self.model_tester.prepare_config_and_inputs_for_common()
        config.num_labels = 3
        config.problem_type = "multi_label_classification"
        input_ids = input_dict["input_ids"]
        attention_mask = input_ids.ne(1)
        sequence_labels = ids_tensor(
            [self.model_tester.batch_size, config.num_labels], self.model_tester.type_sequence_label_size
        ).to(mindspore.float32)
        model = StableLmForSequenceClassification(config)
        model.set_train(False)
        result = model(input_ids, attention_mask=attention_mask, labels=sequence_labels)
        self.assertEqual(result.logits.shape, (self.model_tester.batch_size, self.model_tester.num_labels))

    # Copied from tests.models.llama.test_modeling_llama.LlamaModelTest.test_llama_token_classification_model with Llama->StableLm,llama->stablelm
    def test_stablelm_token_classification_model(self):
        config, input_dict = self.model_tester.prepare_config_and_inputs_for_common()
        config.num_labels = 3
        input_ids = input_dict["input_ids"]
        attention_mask = input_ids.ne(1)
        token_labels = ids_tensor([self.model_tester.batch_size, self.model_tester.seq_length], config.num_labels)
        model = StableLmForTokenClassification(config=config)
        model
        model.set_train(False)
        result = model(input_ids, attention_mask=attention_mask, labels=token_labels)
        self.assertEqual(
            result.logits.shape,
            (self.model_tester.batch_size, self.model_tester.seq_length, self.model_tester.num_labels),
        )

    @parameterized.expand([("linear",), ("dynamic",)])
    # Copied from tests.models.llama.test_modeling_llama.LlamaModelTest.test_model_rope_scaling_from_config with Llama->StableLm
    def test_model_rope_scaling_from_config(self, scaling_type):
        config, _ = self.model_tester.prepare_config_and_inputs_for_common()
        short_input = ids_tensor([1, 10], config.vocab_size)
        long_input = ids_tensor([1, int(config.max_position_embeddings * 1.5)], config.vocab_size)

        set_seed(42)  # Fixed seed at init time so the two models get the same random weights
        original_model = StableLmModel(config)
        original_model.set_train(False)
        original_short_output = original_model(short_input).last_hidden_state
        original_long_output = original_model(long_input).last_hidden_state

        set_seed(42)  # Fixed seed at init time so the two models get the same random weights
        config.rope_scaling = {"type": scaling_type, "factor": 10.0}
        scaled_model = StableLmModel(config)
        scaled_model.set_train(False)
        scaled_short_output = scaled_model(short_input).last_hidden_state
        scaled_long_output = scaled_model(long_input).last_hidden_state

        # Dynamic scaling does not change the RoPE embeddings until it receives an input longer than the original
        # maximum sequence length, so the outputs for the short input should match.
        if scaling_type == "dynamic":
            self.assertTrue(np.allclose(original_short_output.asnumpy(), scaled_short_output.asnumpy(), atol=1e-5))
        else:
            self.assertFalse(np.allclose(original_short_output.asnumpy(), scaled_short_output.asnumpy(), atol=1e-5))

        # The output should be different for long inputs
        self.assertFalse(np.allclose(original_long_output.asnumpy(), scaled_long_output.asnumpy(), atol=1e-5))

    # Copied from tests.models.falcon.test_modeling_falcon.FalconModelTest.test_model_rope_scaling with Falcon->StableLm
    def test_model_rope_scaling(self):
        config, _ = self.model_tester.prepare_config_and_inputs_for_common()
        hidden_size = config.hidden_size
        num_heads = config.num_attention_heads
        head_dim = hidden_size // num_heads
        scaling_factor = 10
        short_input_length = 10
        long_input_length = int(config.max_position_embeddings * 1.5)

        # Inputs
        x = ops.randn(1, dtype=mindspore.float32)  # used exlusively to get the dtype and the device

        # Sanity check original RoPE
        original_rope = StableLmRotaryEmbedding(
            head_dim,
            max_position_embeddings=config.max_position_embeddings,
            base=config.rope_theta,
        )
        original_cos_short, original_sin_short = original_rope(x, short_input_length)
        original_cos_long, original_sin_long = original_rope(x, long_input_length)
        self.assertTrue(np.allclose(original_cos_short.asnumpy(), original_cos_long[:short_input_length, :].asnumpy()))
        self.assertTrue(np.allclose(original_sin_short.asnumpy(), original_sin_long[:short_input_length, :].asnumpy()))

        # Sanity check linear RoPE scaling
        # New position "x" should match original position with index "x/scaling_factor"
        linear_scaling_rope = StableLmLinearScalingRotaryEmbedding(
            head_dim,
            max_position_embeddings=config.max_position_embeddings,
            base=config.rope_theta,
            scaling_factor=scaling_factor,
        )
        linear_cos_short, linear_sin_short = linear_scaling_rope(x, short_input_length)
        linear_cos_long, linear_sin_long = linear_scaling_rope(x, long_input_length)
        self.assertTrue(np.allclose(linear_cos_short.asnumpy(), linear_cos_long[:short_input_length, :].asnumpy()))
        self.assertTrue(np.allclose(linear_sin_short.asnumpy(), linear_sin_long[:short_input_length, :].asnumpy()))

        for new_position in range(0, long_input_length, scaling_factor):
            original_position = int(new_position // scaling_factor)
            self.assertTrue(np.allclose(linear_cos_long[new_position, :].asnumpy(), original_cos_long[original_position, :].asnumpy()))
            self.assertTrue(np.allclose(linear_sin_long[new_position, :].asnumpy(), original_sin_long[original_position, :].asnumpy()))

        # Sanity check Dynamic NTK RoPE scaling
        # Scaling should only be observed after a long input is fed. We can observe that the frequencies increase
        # with scaling_factor (or that `inv_freq` decreases)
        ntk_scaling_rope = StableLmDynamicNTKScalingRotaryEmbedding(
            head_dim,
            max_position_embeddings=config.max_position_embeddings,
            base=config.rope_theta,
            scaling_factor=scaling_factor,
        )
        ntk_cos_short, ntk_sin_short = ntk_scaling_rope(x, short_input_length)
        ntk_cos_long, ntk_sin_long = ntk_scaling_rope(x, long_input_length)
        self.assertTrue(np.allclose(ntk_cos_short.asnumpy(), original_cos_short.asnumpy()))
        self.assertTrue(np.allclose(ntk_sin_short.asnumpy(), original_sin_short.asnumpy()))
        with self.assertRaises(AssertionError):
            self.assertTrue(np.allclose(ntk_cos_long.asnumpy(), original_cos_long.asnumpy()))
        with self.assertRaises(AssertionError):
            self.assertTrue(np.allclose(ntk_sin_long.asnumpy(), original_sin_long.asnumpy()))
        self.assertTrue((ntk_scaling_rope.inv_freq <= original_rope.inv_freq).all())


@require_mindspore
class StableLmModelIntegrationTest(unittest.TestCase):
    @pytest.mark.skip
    @slow
    def test_model_stablelm_3b_4e1t_logits(self):
        input_ids = {"input_ids": mindspore.tensor([[510, 8588, 310, 1900, 9386]], dtype=mindspore.int64)}

        model = StableLmForCausalLM.from_pretrained("stabilityai/stablelm-3b-4e1t")
        model.set_train(False)

        output = model(**input_ids).logits

        # Expected mean on dim = -1
        EXPECTED_MEAN = mindspore.tensor([[2.7146, 2.4245, 1.5616, 1.4424, 2.6790]])
        self.assertTrue(np.allclose(output.mean(axis=-1).asnumpy(), EXPECTED_MEAN.asnumpy(), atol=1e-4, rtol=1e-4))

        # Expected logits sliced from [0, 0, 0:30]
        EXPECTED_SLICE = mindspore.tensor([7.1030, -1.4195,  9.9206,  7.7008,  4.9891,  4.2169,  5.5426,  3.7878, 6.7593,  5.7360,  8.4691,  5.5448,  5.0544, 10.4129,  8.5573, 13.0405, 7.3265,  3.5868,  6.1106,  5.9406,  5.6376,  5.7490,  5.4850,  4.8124, 5.1991,  4.6419,  4.5719,  9.9588,  6.7222,  4.5070])  # fmt: skip
        self.assertTrue(np.allclose(output[0, 0, :30].asnumpy(), EXPECTED_SLICE.asnumpy(), atol=1e-4, rtol=1e-4))

    @slow
    def test_model_stablelm_3b_4e1t_generation(self):
        tokenizer = AutoTokenizer.from_pretrained("stabilityai/stablelm-3b-4e1t")
        model = StableLmForCausalLM.from_pretrained("stabilityai/stablelm-3b-4e1t")
        input_ids = tokenizer.encode(
            "My favorite food has always been pizza, but lately",
            return_tensors="ms",
        )

        outputs = model.generate(input_ids, max_new_tokens=20, temperature=0)
        text = tokenizer.decode(outputs[0], skip_special_tokens=True)

        EXPECTED_TEXT_COMPLETION = """My favorite food has always been pizza, but lately I’ve been craving something different. I’ve been trying to eat healthier and I’ve"""
        self.assertEqual(text, EXPECTED_TEXT_COMPLETION)

    @pytest.mark.skip
    @slow
    def test_model_tiny_random_stablelm_2_logits(self):
        # Check parallel residual and qk layernorm forward pass
        input_ids = {"input_ids": mindspore.tensor([[510, 8588, 310, 1900, 9386]], dtype=mindspore.int64)}

        model = StableLmForCausalLM.from_pretrained("stabilityai/tiny-random-stablelm-2")
        model.set_train(False)

        output = model(**input_ids).logits

        # Expected mean on dim = -1
        EXPECTED_MEAN = mindspore.tensor([[-2.7196, -3.6099, -2.6877, -3.1973, -3.9344]])
        self.assertTrue(np.allclose(output.mean(axis=-1).asnumpy(), EXPECTED_MEAN.asnumpy(), atol=1e-4, rtol=1e-4))

        # Expected logits sliced from [0, 0, 0:30]
        EXPECTED_SLICE = mindspore.tensor([2.8364, 5.3811, 5.1659, 7.5485, 4.3219, 6.3315, 1.3967, 6.9147, 3.9679, 6.4786, 5.9176, 3.3067, 5.2917, 0.1485, 3.9630, 7.9947,10.6727, 9.6757, 8.8772, 8.3527, 7.8445, 6.6025, 5.5786, 7.0985,6.1369, 3.4259, 1.9397, 4.6157, 4.8105, 3.1768])  # fmt: skip
        self.assertTrue(np.allclose(output[0, 0, :30].asnumpy(), EXPECTED_SLICE.asnumpy(), atol=1e-4, rtol=1e-4))

    @slow
    def test_model_tiny_random_stablelm_2_generation(self):
        # Check parallel residual and qk layernorm generation
        tokenizer = AutoTokenizer.from_pretrained("stabilityai/tiny-random-stablelm-2")
        model = StableLmForCausalLM.from_pretrained("stabilityai/tiny-random-stablelm-2")
        input_ids = tokenizer.encode(
            "My favorite ride at the amusement park",
            return_tensors="ms",
        )

        outputs = model.generate(input_ids, max_new_tokens=20, temperature=0)
        text = tokenizer.decode(outputs[0], skip_special_tokens=True)

        EXPECTED_TEXT_COMPLETION = """My favorite ride at the amusement park is the 2000-mile roller coaster. It's a thrilling ride filled with roller coast"""
        self.assertEqual(text, EXPECTED_TEXT_COMPLETION)

    # @require_bitsandbytes
    # @slow
    # @require_flash_attn
    # def test_model_3b_long_prompt(self):
    #     EXPECTED_OUTPUT_TOKEN_IDS = [3, 3, 3]
    #     input_ids = [306, 338] * 2047
    #     model = StableLmForCausalLM.from_pretrained(
    #         "stabilityai/stablelm-3b-4e1t",
    #         device_map="auto",
    #         torch_dtype="auto",
    #         load_in_4bit=True,
    #         attn_implementation="flash_attention_2",
    #     )
    #     input_ids = mindspore.tensor([input_ids]).to(model.model.embed_tokens.weight.device)
    #     generated_ids = model.generate(input_ids, max_new_tokens=4, temperature=0)
    #     self.assertEqual(EXPECTED_OUTPUT_TOKEN_IDS, generated_ids[0][-3:].tolist())

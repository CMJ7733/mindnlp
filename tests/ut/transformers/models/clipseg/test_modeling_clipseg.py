# coding=utf-8
# Copyright 2022 The HuggingFace Inc. team. All rights reserved.
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
"""Testing suite for the mindspore CLIPSeg model."""

import inspect
import os
import tempfile
import unittest

import numpy as np
import requests
from mindnlp.utils.testing_utils import (
    require_mindspore,
    require_vision,
    slow,
)
from mindnlp.utils import is_mindspore_available, is_vision_available

from ...test_configuration_common import ConfigTester
from ...test_modeling_common import (
    ModelTesterMixin,
    _config_zero_init,
    floats_tensor,
    ids_tensor,
    random_attention_mask,
)


if is_mindspore_available():
    import mindspore
    from mindnlp.core import nn, ops

    from mindnlp.transformers import (
        CLIPSegForImageSegmentation, 
        CLIPSegModel, 
        CLIPSegTextModel, 
        CLIPSegVisionModel,
        CLIPSegTextConfig,
        CLIPSegVisionConfig,
        CLIPSegConfig,
        CLIPSegProcessor
    )
    from mindnlp.transformers.models.auto.modeling_auto import MODEL_MAPPING_NAMES


if is_vision_available():
    from PIL import Image

class CLIPSegVisionModelTester:
    def __init__(
        self,
        parent,
        batch_size=12,
        image_size=30,
        patch_size=2,
        num_channels=3,
        is_training=True,
        hidden_size=32,
        num_hidden_layers=2,
        num_attention_heads=4,
        intermediate_size=37,
        dropout=0.1,
        attention_dropout=0.1,
        initializer_range=0.02,
        scope=None,
    ):
        self.parent = parent
        self.batch_size = batch_size
        self.image_size = image_size
        self.patch_size = patch_size
        self.num_channels = num_channels
        self.is_training = is_training
        self.hidden_size = hidden_size
        self.num_hidden_layers = num_hidden_layers
        self.num_attention_heads = num_attention_heads
        self.intermediate_size = intermediate_size
        self.dropout = dropout
        self.attention_dropout = attention_dropout
        self.initializer_range = initializer_range
        self.scope = scope

        # in ViT, the seq length equals the number of patches + 1 (we add 1 for the [CLS] token)
        num_patches = (image_size // patch_size) ** 2
        self.seq_length = num_patches + 1

    def prepare_config_and_inputs(self):
        pixel_values = floats_tensor([self.batch_size, self.num_channels, self.image_size, self.image_size])
        config = self.get_config()

        return config, pixel_values

    def get_config(self):
        return CLIPSegVisionConfig(
            image_size=self.image_size,
            patch_size=self.patch_size,
            num_channels=self.num_channels,
            hidden_size=self.hidden_size,
            num_hidden_layers=self.num_hidden_layers,
            num_attention_heads=self.num_attention_heads,
            intermediate_size=self.intermediate_size,
            dropout=self.dropout,
            attention_dropout=self.attention_dropout,
            initializer_range=self.initializer_range,
        )

    def create_and_check_model(self, config, pixel_values):
        model = CLIPSegVisionModel(config=config)
        model.set_train(False)
        result = model(pixel_values)
        # expected sequence length = num_patches + 1 (we add 1 for the [CLS] token)
        image_size = (self.image_size, self.image_size)
        patch_size = (self.patch_size, self.patch_size)
        num_patches = (image_size[1] // patch_size[1]) * (image_size[0] // patch_size[0])
        self.parent.assertEqual(result.last_hidden_state.shape, (self.batch_size, num_patches + 1, self.hidden_size))
        self.parent.assertEqual(result.pooler_output.shape, (self.batch_size, self.hidden_size))

    def prepare_config_and_inputs_for_common(self):
        config_and_inputs = self.prepare_config_and_inputs()
        config, pixel_values = config_and_inputs
        inputs_dict = {"pixel_values": pixel_values}
        return config, inputs_dict


@require_mindspore
class CLIPSegVisionModelTest(ModelTesterMixin, unittest.TestCase):
    """
    Here we also overwrite some of the tests of test_modeling_common.py, as CLIPSeg does not use input_ids, inputs_embeds,
    attention_mask and seq_length.
    """

    all_model_classes = (CLIPSegVisionModel,) if is_mindspore_available() else ()
    fx_compatible = False
    test_pruning = False
    test_resize_embeddings = False
    test_head_masking = False

    def setUp(self):
        self.model_tester = CLIPSegVisionModelTester(self)
        self.config_tester = ConfigTester(
            self, config_class=CLIPSegVisionConfig, has_text_modality=False, hidden_size=37
        )

    def test_config(self):
        self.config_tester.run_common_tests()

    @unittest.skip(reason="CLIPSeg does not use inputs_embeds")
    def test_inputs_embeds(self):
        pass

    @unittest.skip(reason="SegFormer does not have get_input_embeddings method and get_output_embeddings methods")
    def test_model_get_set_embeddings(self):
        pass

    def test_model_get_set_embeddings(self):
        config, _ = self.model_tester.prepare_config_and_inputs_for_common()

        for model_class in self.all_model_classes:
            model = model_class(config)
            self.assertIsInstance(model.get_input_embeddings(), (nn.Module))
            x = model.get_output_embeddings()
            self.assertTrue(x is None or isinstance(x, nn.Linear))

    def test_forward_signature(self):
        config, _ = self.model_tester.prepare_config_and_inputs_for_common()

        for model_class in self.all_model_classes:
            model = model_class(config)
            signature = inspect.signature(model.forward)
            # signature.parameters is an OrderedDict => so arg_names order is deterministic
            arg_names = [*signature.parameters.keys()]

            expected_arg_names = ["pixel_values"]
            self.assertListEqual(arg_names[:1], expected_arg_names)

    def test_model(self):
        config_and_inputs = self.model_tester.prepare_config_and_inputs()
        self.model_tester.create_and_check_model(*config_and_inputs)

    @unittest.skip
    def test_training(self):
        pass

    @unittest.skip
    def test_training_gradient_checkpointing(self):
        pass

    @unittest.skip(
        reason="This architecure seem to not compute gradients properly when using GC, check: https://github.com/huggingface/transformers/pull/27124"
    )
    def test_training_gradient_checkpointing_use_reentrant(self):
        pass

    @unittest.skip(
        reason="This architecure seem to not compute gradients properly when using GC, check: https://github.com/huggingface/transformers/pull/27124"
    )
    def test_training_gradient_checkpointing_use_reentrant_false(self):
        pass
    
    def test_model_outputs_equivalence(self):
        pass
    @unittest.skip(reason="CLIPSegVisionModel has no base class and is not available in MODEL_MAPPING")
    def test_save_load_fast_init_from_base(self):
        pass

    @unittest.skip(reason="CLIPSegVisionModel has no base class and is not available in MODEL_MAPPING")
    def test_save_load_fast_init_to_base(self):
        pass

    @slow
    def test_model_from_pretrained(self):
        model_name = "CIDAS/clipseg-rd64-refined"
        model = CLIPSegVisionModel.from_pretrained(model_name)
        self.assertIsNotNone(model)


class CLIPSegTextModelTester:
    def __init__(
        self,
        parent,
        batch_size=12,
        seq_length=7,
        is_training=True,
        use_input_mask=True,
        use_labels=True,
        vocab_size=99,
        hidden_size=32,
        num_hidden_layers=2,
        num_attention_heads=4,
        intermediate_size=37,
        dropout=0.1,
        attention_dropout=0.1,
        max_position_embeddings=512,
        initializer_range=0.02,
        scope=None,
    ):
        self.parent = parent
        self.batch_size = batch_size
        self.seq_length = seq_length
        self.is_training = is_training
        self.use_input_mask = use_input_mask
        self.use_labels = use_labels
        self.vocab_size = vocab_size
        self.hidden_size = hidden_size
        self.num_hidden_layers = num_hidden_layers
        self.num_attention_heads = num_attention_heads
        self.intermediate_size = intermediate_size
        self.dropout = dropout
        self.attention_dropout = attention_dropout
        self.max_position_embeddings = max_position_embeddings
        self.initializer_range = initializer_range
        self.scope = scope

    def prepare_config_and_inputs(self):
        input_ids = ids_tensor([self.batch_size, self.seq_length], self.vocab_size)

        input_mask = None
        if self.use_input_mask:
            input_mask = random_attention_mask([self.batch_size, self.seq_length])

        if input_mask is not None:
            batch_size, seq_length = input_mask.shape
            rnd_start_indices = np.random.randint(1, seq_length - 1, size=(batch_size,))
            for batch_idx, start_index in enumerate(rnd_start_indices):
                input_mask[int(batch_idx), :int(start_index)] = 1
                input_mask[int(batch_idx), int(start_index):] = 0

        config = self.get_config()

        return config, input_ids, input_mask

    def get_config(self):
        return CLIPSegTextConfig(
            vocab_size=self.vocab_size,
            hidden_size=self.hidden_size,
            num_hidden_layers=self.num_hidden_layers,
            num_attention_heads=self.num_attention_heads,
            intermediate_size=self.intermediate_size,
            dropout=self.dropout,
            attention_dropout=self.attention_dropout,
            max_position_embeddings=self.max_position_embeddings,
            initializer_range=self.initializer_range,
        )

    def create_and_check_model(self, config, input_ids, input_mask):
        model = CLIPSegTextModel(config=config)
        model.set_train(False)
        result = model(input_ids, attention_mask=input_mask)
        result = model(input_ids)
        self.parent.assertEqual(result.last_hidden_state.shape, (self.batch_size, self.seq_length, self.hidden_size))
        self.parent.assertEqual(result.pooler_output.shape, (self.batch_size, self.hidden_size))

    def prepare_config_and_inputs_for_common(self):
        config_and_inputs = self.prepare_config_and_inputs()
        config, input_ids, input_mask = config_and_inputs
        inputs_dict = {"input_ids": input_ids, "attention_mask": input_mask}
        return config, inputs_dict


@require_mindspore
class CLIPSegTextModelTest(ModelTesterMixin, unittest.TestCase):
    all_model_classes = (CLIPSegTextModel,) if is_mindspore_available() else ()
    fx_compatible = False
    test_pruning = False
    test_head_masking = False
    model_split_percents = [0.5, 0.8, 0.9]

    def setUp(self):
        self.model_tester = CLIPSegTextModelTester(self)
        self.config_tester = ConfigTester(self, config_class=CLIPSegTextConfig, hidden_size=37)

    def test_config(self):
        self.config_tester.run_common_tests()

    def test_model(self):
        config_and_inputs = self.model_tester.prepare_config_and_inputs()
        self.model_tester.create_and_check_model(*config_and_inputs)

    @unittest.skip
    def test_training(self):
        pass

    @unittest.skip
    def test_training_gradient_checkpointing(self):
        pass

    @unittest.skip(
        reason="This architecure seem to not compute gradients properly when using GC, check: https://github.com/huggingface/transformers/pull/27124"
    )
    def test_training_gradient_checkpointing_use_reentrant(self):
        pass

    @unittest.skip(
        reason="This architecure seem to not compute gradients properly when using GC, check: https://github.com/huggingface/transformers/pull/27124"
    )
    def test_training_gradient_checkpointing_use_reentrant_false(self):
        pass

    @unittest.skip(reason="CLIPSeg does not use inputs_embeds")
    def test_inputs_embeds(self):
        pass

    @unittest.skip(reason="CLIPSegTextModel has no base class and is not available in MODEL_MAPPING")
    def test_save_load_fast_init_from_base(self):
        pass

    @unittest.skip(reason="CLIPSegTextModel has no base class and is not available in MODEL_MAPPING")
    def test_save_load_fast_init_to_base(self):
        pass

    @slow
    def test_model_from_pretrained(self):
        model_name = "CIDAS/clipseg-rd64-refined"
        model = CLIPSegTextModel.from_pretrained(model_name)
        self.assertIsNotNone(model)


class CLIPSegModelTester:
    def __init__(
        self,
        parent,
        text_kwargs=None,
        vision_kwargs=None,
        is_training=True,
        # This should respect the `num_hidden_layers` in `CLIPSegVisionModelTester`
        extract_layers=(1,),
    ):
        if text_kwargs is None:
            text_kwargs = {}
        if vision_kwargs is None:
            vision_kwargs = {}

        self.parent = parent
        self.text_model_tester = CLIPSegTextModelTester(parent, **text_kwargs)
        self.vision_model_tester = CLIPSegVisionModelTester(parent, **vision_kwargs)
        self.batch_size = self.text_model_tester.batch_size  # need bs for batching_equivalence test
        self.is_training = is_training
        self.extract_layers = extract_layers

    def prepare_config_and_inputs(self):
        text_config, input_ids, attention_mask = self.text_model_tester.prepare_config_and_inputs()
        vision_config, pixel_values = self.vision_model_tester.prepare_config_and_inputs()

        config = self.get_config()

        return config, input_ids, attention_mask, pixel_values

    def get_config(self):
        return CLIPSegConfig.from_text_vision_configs(
            self.text_model_tester.get_config(),
            self.vision_model_tester.get_config(),
            projection_dim=64,
            reduce_dim=32,
            extract_layers=self.extract_layers,
        )

    def create_and_check_model(self, config, input_ids, attention_mask, pixel_values):
        model = CLIPSegModel(config).set_train(False)
        result = model(input_ids, pixel_values, attention_mask)
        self.parent.assertEqual(
            result.logits_per_image.shape, (self.vision_model_tester.batch_size, self.text_model_tester.batch_size)
        )
        self.parent.assertEqual(
            result.logits_per_text.shape, (self.text_model_tester.batch_size, self.vision_model_tester.batch_size)
        )

    def create_and_check_model_for_image_segmentation(self, config, input_ids, attention_maks, pixel_values):
        model = CLIPSegForImageSegmentation(config).set_train(False)
        result = model(input_ids, pixel_values)
        self.parent.assertEqual(
            result.logits.shape,
            (
                self.vision_model_tester.batch_size,
                self.vision_model_tester.image_size,
                self.vision_model_tester.image_size,
            ),
        )
        self.parent.assertEqual(
            result.conditional_embeddings.shape, (self.text_model_tester.batch_size, config.projection_dim)
        )

    def prepare_config_and_inputs_for_common(self):
        config_and_inputs = self.prepare_config_and_inputs()
        config, input_ids, attention_mask, pixel_values = config_and_inputs
        inputs_dict = {
            "input_ids": input_ids,
            "attention_mask": attention_mask,
            "pixel_values": pixel_values,
        }
        return config, inputs_dict


@require_mindspore
class CLIPSegModelTest(ModelTesterMixin, unittest.TestCase):
    all_model_classes = (CLIPSegModel, CLIPSegForImageSegmentation) if is_mindspore_available() else ()
    pipeline_model_mapping = {"feature-extraction": CLIPSegModel} if is_mindspore_available() else {}
    fx_compatible = False
    test_head_masking = False
    test_pruning = False
    test_resize_embeddings = False
    test_attention_outputs = False

    def _prepare_for_class(self, inputs_dict, model_class, return_labels=False):
        # CLIPSegForImageSegmentation requires special treatment
        if return_labels:
            if model_class.__name__ == "CLIPSegForImageSegmentation":
                batch_size, _, height, width = inputs_dict["pixel_values"].shape
                inputs_dict["labels"] = ops.zeros(
                    batch_size, height, width, dtype=mindspore.float32
                )

        return inputs_dict

    def setUp(self):
        self.model_tester = CLIPSegModelTester(self)

    def test_model(self):
        config_and_inputs = self.model_tester.prepare_config_and_inputs()
        self.model_tester.create_and_check_model(*config_and_inputs)

    def test_model_for_image_segmentation(self):
        config_and_inputs = self.model_tester.prepare_config_and_inputs()
        self.model_tester.create_and_check_model_for_image_segmentation(*config_and_inputs)

    @unittest.skip(reason="Hidden_states is tested in individual model tests")
    def test_hidden_states_output(self):
        pass

    @unittest.skip(reason="Inputs_embeds is tested in individual model tests")
    def test_inputs_embeds(self):
        pass

    @unittest.skip(reason="Retain_grad is tested in individual model tests")
    def test_retain_grad_hidden_states_attentions(self):
        pass

    @unittest.skip(reason="CLIPSegModel does not have input/output embeddings")
    def test_model_get_set_embeddings(self):
        pass

    @unittest.skip(
        reason="This architecure seem to not compute gradients properly when using GC, check: https://github.com/huggingface/transformers/pull/27124"
    )
    def test_training_gradient_checkpointing(self):
        pass

    @unittest.skip(
        reason="This architecure seem to not compute gradients properly when using GC, check: https://github.com/huggingface/transformers/pull/27124"
    )
    def test_training_gradient_checkpointing_use_reentrant(self):
        pass

    def test_model_outputs_equivalence(self):
        pass

    @unittest.skip("SegFormer does not have get_input_embeddings method and get_output_embeddings methods")
    def test_model_get_set_embeddings(self):
        pass

    @unittest.skip(
        reason="This architecure seem to not compute gradients properly when using GC, check: https://github.com/huggingface/transformers/pull/27124"
    )
    def test_training_gradient_checkpointing_use_reentrant_false(self):
        pass

    # override as the some parameters require custom initialization
    def test_initialization(self):
        config, inputs_dict = self.model_tester.prepare_config_and_inputs_for_common()

        configs_no_init = _config_zero_init(config)
        for model_class in self.all_model_classes:
            model = model_class(config=configs_no_init)
            for name, param in model.parameters_and_names():
                if param.requires_grad:
                    # check if `logit_scale` is initilized as per the original implementation
                    if "logit_scale" in name:
                        self.assertAlmostEqual(
                            param.data.item(),
                            np.log(1 / 0.07),
                            delta=1e-3,
                            msg=f"Parameter {name} of model {model_class} seems not properly initialized",
                        )
                    elif "film" in name or "transposed_conv" in name or "reduce" in name:
                        # those parameters use Mindspore' default nn.Linear initialization scheme
                        pass
                    else:
                        self.assertIn(
                            ((param.data.mean() * 1e9).round() / 1e9).item(),
                            [0.0, 1.0],
                            msg=f"Parameter {name} of model {model_class} seems not properly initialized",
                        )


    def test_load_vision_text_config(self):
        config, inputs_dict = self.model_tester.prepare_config_and_inputs_for_common()

        # Save CLIPSegConfig and check if we can load CLIPSegVisionConfig from it
        with tempfile.TemporaryDirectory() as tmp_dir_name:
            config.save_pretrained(tmp_dir_name)
            vision_config = CLIPSegVisionConfig.from_pretrained(tmp_dir_name)
            self.assertDictEqual(config.vision_config.to_dict(), vision_config.to_dict())

        # Save CLIPSegConfig and check if we can load CLIPSegTextConfig from it
        with tempfile.TemporaryDirectory() as tmp_dir_name:
            config.save_pretrained(tmp_dir_name)
            text_config = CLIPSegTextConfig.from_pretrained(tmp_dir_name)
            self.assertDictEqual(config.text_config.to_dict(), text_config.to_dict())

    # overwrite from common since FlaxCLIPSegModel returns nested output
    # which is not supported in the common test

    def test_training(self):
        if not self.model_tester.is_training:
            self.skipTest(reason="Training test is skipped as the model was not trained")

        for model_class in self.all_model_classes:
            config, inputs_dict = self.model_tester.prepare_config_and_inputs_for_common()
            config.return_dict = True

            if model_class.__name__ in MODEL_MAPPING_NAMES.values():
                continue

            print("Model class:", model_class)

            model = model_class(config)
            model.set_train(False)
            inputs = self._prepare_for_class(inputs_dict, model_class, return_labels=True)
            for k, v in inputs.items():
                print(k, v.shape)
            loss = model(**inputs).loss

    @slow
    def test_model_from_pretrained(self):
        model_name = "CIDAS/clipseg-rd64-refined"
        model = CLIPSegModel.from_pretrained(model_name, ignore_mismatched_sizes=True)
        self.assertIsNotNone(model)


# We will verify our results on an image of cute cats
def prepare_img():
    url = "http://images.cocodataset.org/val2017/000000039769.jpg"
    image = Image.open(requests.get(url, stream=True).raw)
    return image


@require_vision
@require_mindspore
class CLIPSegModelIntegrationTest(unittest.TestCase):
    @slow
    def test_inference_image_segmentation(self):
        model_name = "CIDAS/clipseg-rd64-refined"
        processor = CLIPSegProcessor.from_pretrained(model_name, ignore_mismatched_sizes=True)
        model = CLIPSegForImageSegmentation.from_pretrained(model_name,ignore_mismatched_sizes=True)

        image = prepare_img()
        texts = ["a cat", "a remote", "a blanket"]
        inputs = processor(text=texts, images=[image] * len(texts), padding=True, return_tensors="ms")

        # forward pass
        outputs = model(**inputs)

        # verify the predicted masks
        self.assertEqual(
            outputs.logits.shape,
            (3, 352, 352),
        )
        expected_masks_slice = mindspore.Tensor(
            [[-7.4613, -7.4785, -7.3628], [-7.3268, -7.0899, -7.1333], [-6.9838, -6.7900, -6.8913]]
        )
        self.assertTrue(np.allclose(outputs.logits[0, :3, :3], expected_masks_slice, atol=1e-3))

        # verify conditional and pooled output
        expected_conditional = mindspore.Tensor([0.5601, -0.0314, 0.1980])
        expected_pooled_output = mindspore.Tensor([0.5036, -0.2681, -0.2644])
        self.assertTrue(np.allclose(outputs.conditional_embeddings[0, :3], expected_conditional, atol=1e-3))
        self.assertTrue(np.allclose(outputs.pooled_output[0, :3], expected_pooled_output, atol=1e-3))

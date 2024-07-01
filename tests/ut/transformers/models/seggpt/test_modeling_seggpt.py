# Copyright 2024 Huawei Technologies Co., Ltd
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
# ============================================
"""Testing suite for the MindSpore SegGpt model."""

import inspect
import math
import unittest

import numpy as np
from datasets import load_dataset

from mindnlp.transformers import SegGptConfig
from mindnlp.utils.testing_utils import (
    require_mindspore,
    require_vision,
    slow,
)
from mindnlp.utils import cached_property, is_mindspore_available, is_vision_available

from ...test_configuration_common import ConfigTester
from ...test_modeling_common import ModelTesterMixin, floats_tensor
# from ...test_pipeline_mixin import PipelineTesterMixin


if is_mindspore_available():
    import mindspore as ms
    from mindspore import nn, ops

    from mindnlp.transformers import SegGptForImageSegmentation, SegGptModel
    from mindnlp.transformers.models.seggpt.modeling_seggpt import SegGptLoss


if is_vision_available():
    from mindnlp.transformers import SegGptImageProcessor


class SegGptModelTester:
    def __init__(
        self,
        parent,
        batch_size=2,
        image_size=30,
        patch_size=2,
        num_channels=3,
        is_training=False,
        use_labels=True,
        hidden_size=32,
        num_hidden_layers=2,
        num_attention_heads=4,
        hidden_act="gelu",
        hidden_dropout_prob=0.1,
        attention_probs_dropout_prob=0.1,
        initializer_range=0.02,
        mlp_ratio=2.0,
        merge_index=0,
        intermediate_hidden_state_indices=[1],
        pretrain_image_size=10,
        decoder_hidden_size=10,
    ):
        self.parent = parent
        self.batch_size = batch_size
        self.image_size = image_size
        self.patch_size = patch_size
        self.num_channels = num_channels
        self.is_training = is_training
        self.use_labels = use_labels
        self.hidden_size = hidden_size
        self.num_hidden_layers = num_hidden_layers
        self.num_attention_heads = num_attention_heads
        self.hidden_act = hidden_act
        self.hidden_dropout_prob = hidden_dropout_prob
        self.attention_probs_dropout_prob = attention_probs_dropout_prob
        self.initializer_range = initializer_range
        self.mlp_ratio = mlp_ratio
        self.merge_index = merge_index
        self.intermediate_hidden_state_indices = intermediate_hidden_state_indices
        self.pretrain_image_size = pretrain_image_size
        self.decoder_hidden_size = decoder_hidden_size

        # in SegGpt, the seq length equals the number of patches (we don't use the [CLS] token)
        num_patches = (image_size // patch_size) ** 2
        self.seq_length = num_patches

    def prepare_config_and_inputs(self):
        pixel_values = floats_tensor(
            [self.batch_size, self.num_channels, self.image_size // 2, self.image_size])
        prompt_pixel_values = floats_tensor(
            [self.batch_size, self.num_channels,
                self.image_size // 2, self.image_size]
        )
        prompt_masks = floats_tensor(
            [self.batch_size, self.num_channels, self.image_size // 2, self.image_size])

        labels = None
        if self.use_labels:
            labels = floats_tensor(
                [self.batch_size, self.num_channels, self.image_size // 2, self.image_size])

        config = self.get_config()

        return config, pixel_values, prompt_pixel_values, prompt_masks, labels

    def get_config(self):
        return SegGptConfig(
            image_size=self.image_size,
            patch_size=self.patch_size,
            num_channels=self.num_channels,
            hidden_size=self.hidden_size,
            num_hidden_layers=self.num_hidden_layers,
            num_attention_heads=self.num_attention_heads,
            hidden_act=self.hidden_act,
            hidden_dropout_prob=self.hidden_dropout_prob,
            initializer_range=self.initializer_range,
            mlp_ratio=self.mlp_ratio,
            merge_index=self.merge_index,
            intermediate_hidden_state_indices=self.intermediate_hidden_state_indices,
            pretrain_image_size=self.pretrain_image_size,
            decoder_hidden_size=self.decoder_hidden_size,
        )

    def create_and_check_model(self, config, pixel_values, prompt_pixel_values, prompt_masks, labels):
        model = SegGptModel(config=config)
        model.set_train(False)
        result = model(pixel_values, prompt_pixel_values, prompt_masks)
        self.parent.assertEqual(
            result.last_hidden_state.shape,
            (
                self.batch_size,
                self.image_size // self.patch_size,
                self.image_size // self.patch_size,
                self.hidden_size,
            ),
        )

    def prepare_config_and_inputs_for_common(self):
        config_and_inputs = self.prepare_config_and_inputs()
        (
            config,
            pixel_values,
            prompt_pixel_values,
            prompt_masks,
            labels,
        ) = config_and_inputs
        inputs_dict = {
            "pixel_values": pixel_values,
            "prompt_pixel_values": prompt_pixel_values,
            "prompt_masks": prompt_masks,
        }
        return config, inputs_dict


@require_mindspore
class SegGptModelTest(ModelTesterMixin, unittest.TestCase):
    """
    Here we also overwrite some of the tests of test_modeling_common.py, as SegGpt does not use input_ids, inputs_embeds,
    attention_mask and seq_length.
    """

    all_model_classes = (
        SegGptModel, SegGptForImageSegmentation) if is_mindspore_available() else ()
    fx_compatible = False

    test_pruning = False
    test_resize_embeddings = False
    test_head_masking = False
    test_torchscript = False
    pipeline_model_mapping = (
        {"feature-extraction": SegGptModel,
            "mask-generation": SegGptModel} if is_mindspore_available() else {}
    )

    def setUp(self):
        self.model_tester = SegGptModelTester(self)
        self.config_tester = ConfigTester(
            self, config_class=SegGptConfig, has_text_modality=False)

    def test_config(self):
        self.config_tester.run_common_tests()

    @unittest.skip(reason="SegGpt does not use inputs_embeds")
    def test_inputs_embeds(self):
        pass

    def test_model_common_attributes(self):
        config, _ = self.model_tester.prepare_config_and_inputs_for_common()

        for model_class in self.all_model_classes:
            model = model_class(config)
            self.assertIsInstance(model.get_input_embeddings(), (nn.Cell))

    def test_forward_signature(self):
        config, _ = self.model_tester.prepare_config_and_inputs_for_common()

        for model_class in self.all_model_classes:
            model = model_class(config)
            signature = inspect.signature(model.construct)
            # signature.parameters is an OrderedDict => so arg_names order is deterministic
            arg_names = [*signature.parameters.keys()]

            expected_arg_names = ["pixel_values",
                                  "prompt_pixel_values", "prompt_masks"]
            self.assertListEqual(arg_names[:3], expected_arg_names)

    def test_model(self):
        config_and_inputs = self.model_tester.prepare_config_and_inputs()
        self.model_tester.create_and_check_model(*config_and_inputs)

    def test_hidden_states_output(self):
        def check_hidden_states_output(inputs_dict, config, model_class):
            model = model_class(config)
            model.set_train(False)

            outputs = model(
                **self._prepare_for_class(inputs_dict, model_class))

            hidden_states = outputs.encoder_hidden_states if config.is_encoder_decoder else outputs.hidden_states

            expected_num_layers = getattr(
                self.model_tester, "expected_num_hidden_layers", self.model_tester.num_hidden_layers + 1
            )
            self.assertEqual(len(hidden_states), expected_num_layers)

            patch_height = patch_width = config.image_size // config.patch_size

            self.assertListEqual(
                list(hidden_states[0].shape[-3:]),
                [patch_height, patch_width, self.model_tester.hidden_size],
            )

        config, inputs_dict = self.model_tester.prepare_config_and_inputs_for_common()

        for model_class in self.all_model_classes:
            inputs_dict["output_hidden_states"] = True
            check_hidden_states_output(inputs_dict, config, model_class)

            # check that output_hidden_states also work using config
            del inputs_dict["output_hidden_states"]
            config.output_hidden_states = True

            check_hidden_states_output(inputs_dict, config, model_class)

    def test_batching_equivalence(self):
        def recursive_check(batched_object, single_row_object, model_name, key):
            if isinstance(batched_object, (list, tuple)):
                for batched_object_value, single_row_object_value in zip(batched_object, single_row_object):
                    recursive_check(batched_object_value,
                                    single_row_object_value, model_name, key)
            else:
                batched_row = batched_object[:1]
                self.assertFalse(
                    ops.isnan(batched_row).any(
                    ), f"Batched output has `nan` in {model_name} for key={key}"
                )
                self.assertFalse(
                    ops.isinf(batched_row).any(
                    ), f"Batched output has `inf` in {model_name} for key={key}"
                )
                self.assertFalse(
                    ops.isnan(single_row_object).any(
                    ), f"Single row output has `nan` in {model_name} for key={key}"
                )
                self.assertFalse(
                    ops.isinf(single_row_object).any(
                    ), f"Single row output has `inf` in {model_name} for key={key}"
                )

                self.assertTrue(
                    ops.max(ops.abs(batched_row - single_row_object)
                            )[0] <= 1e-03,
                    msg=(
                        f"Batched and Single row outputs are not equal in {model_name} for key={key}. "
                        f"Difference={ops.max(ops.abs(batched_row - single_row_object))}."
                    ),
                )

        config, batched_input = self.model_tester.prepare_config_and_inputs_for_common()

        for model_class in self.all_model_classes:
            config.output_hidden_states = True

            model_name = model_class.__name__
            batched_input_prepared = self._prepare_for_class(
                batched_input, model_class)
            model = model_class(config)
            model.set_train(False)

            batch_size = self.model_tester.batch_size
            single_row_input = {}
            for key, value in batched_input_prepared.items():
                if isinstance(value, ms.Tensor) and value.shape[0] % batch_size == 0:
                    single_batch_shape = value.shape[0] // batch_size
                    single_row_input[key] = value[:single_batch_shape]

            model_batched_output = model(**batched_input_prepared)
            model_row_output = model(**single_row_input)

            for key in model_batched_output:
                # the first hidden state in SegGPT has weird hack of adding first half of batch with second half
                if key == "hidden_states":
                    model_batched_output[key] = model_batched_output[key][1:]
                    model_row_output[key] = model_row_output[key][1:]
                recursive_check(
                    model_batched_output[key], model_row_output[key], model_name, key)

    @unittest.skip(reason="Due to the inability to generate random numbers consistent with torch.rand,\
                   we can only pass the test locally by loading data files generated with torch.rand.")
    def test_seggpt_loss(self):
        config = self.model_tester.get_config()

        # ms.set_seed(100)
        # prompt_masks = ops.rand(1, config.num_channels,
        #                         config.image_size, config.image_size)
        # label = ops.rand(1, config.num_channels,
        #                  config.image_size, config.image_size)
        # pred_masks = ops.rand(1, config.num_channels,
        #                       config.image_size * 2, config.image_size)
        # # seq_len x 2 because the loss concatenates prompt_masks and labels as pred_masks is concatenated
        # bool_masked_pos = ops.rand(1, self.model_tester.seq_length * 2) > 0.5

        prompt_masks = ms.Tensor(np.load('prompt_masks.npy'))
        label = ms.Tensor(np.load('label.npy'))
        pred_masks = ms.Tensor(np.load('pred_masks.npy'))
        bool_masked_pos = ms.Tensor(np.load('bool_masked_pos.npy'))

        loss = SegGptLoss(config)
        loss_value = loss(prompt_masks, pred_masks, label, bool_masked_pos)
        expected_loss_value = ms.Tensor(0.3340)

        loss_value = loss_value.asnumpy()
        self.assertTrue(np.allclose(loss_value,
                        expected_loss_value.asnumpy(), atol=1e-4))

    @slow
    def test_model_from_pretrained(self):
        model_name = "BAAI/seggpt-vit-large"
        model = SegGptModel.from_pretrained(model_name)
        self.assertIsNotNone(model)


def prepare_img():
    ds = load_dataset("EduardoPacheco/seggpt-example-data")["train"]
    images = [image.convert("RGB") for image in ds["image"]]
    masks = [image.convert("RGB") for image in ds["mask"]]
    return images, masks


def prepare_bool_masked_pos(config: SegGptConfig):
    num_patches = math.prod(
        [i // config.patch_size for i in config.image_size])
    mask_ratio = 0.75
    num_masked_patches = int(num_patches * mask_ratio)

    # seed = 2
    # offset = 0
    # shuffle_idx = ops.RandpermV2()(Tensor(num_patches), seed, offset)

    shuffle_idx = ms.Tensor(np.load('shuffle_idx.npy'))

    bool_masked_pos = ms.Tensor([0] * (num_patches - num_masked_patches) + [1] * num_masked_patches)[
        shuffle_idx
    ]
    bool_masked_pos = bool_masked_pos.unsqueeze(0).bool()

    return bool_masked_pos


@require_mindspore
@require_vision
class SegGptModelIntegrationTest(unittest.TestCase):
    @cached_property
    def default_image_processor(self):
        return SegGptImageProcessor.from_pretrained("BAAI/seggpt-vit-large")

    @unittest.skip(reason="The inference error between MindSpore and Torch here is within 2e-4.")
    def test_one_shot_inference(self):
        model = SegGptForImageSegmentation.from_pretrained(
            "BAAI/seggpt-vit-large", ms_dtype=ms.float32)

        image_processor = self.default_image_processor

        images, masks = prepare_img()
        input_image = images[1]
        prompt_image = images[0]
        prompt_mask = masks[0]

        inputs = image_processor(
            images=input_image,
            prompt_images=prompt_image,
            prompt_masks=prompt_mask,
            return_tensors="ms",
            do_convert_rgb=False,
        )

        # forward pass
        outputs = model(**inputs)

        # verify the logits
        expected_shape = (1, 3, 896, 448)
        self.assertEqual(outputs.pred_masks.shape, expected_shape)

        expected_slice = ms.Tensor(
            [
                [[-2.1208, -2.1190, -2.1198], [-2.1237, -2.1228, -2.1227],
                    [-2.1232, -2.1226, -2.1228]],
                [[-2.0405, -2.0396, -2.0403], [-2.0434, -2.0434, -2.0433],
                    [-2.0428, -2.0432, -2.0434]],
                [[-1.8102, -1.8088, -1.8099], [-1.8131, -1.8126, -1.8129],
                    [-1.8130, -1.8128, -1.8131]],
            ]
        )

        self.assertTrue(np.allclose(
            outputs.pred_masks[0, :, :3, :3].asnumpy(), expected_slice.asnumpy(), atol=1e-4))

        result = image_processor.post_process_semantic_segmentation(
            outputs, [input_image.size[::-1]])[0]

        result_expected_shape = (170, 297)
        expected_area = 1082
        area = (result > 0).sum().item()
        self.assertEqual(result.shape, result_expected_shape)
        self.assertEqual(area, expected_area)

    @slow
    def test_few_shot_inference(self):
        model = SegGptForImageSegmentation.from_pretrained(
            "BAAI/seggpt-vit-large")
        image_processor = self.default_image_processor

        images, masks = prepare_img()
        input_images = [images[1]] * 2
        prompt_images = [images[0], images[2]]
        prompt_masks = [masks[0], masks[2]]

        inputs = image_processor(
            images=input_images,
            prompt_images=prompt_images,
            prompt_masks=prompt_masks,
            return_tensors="ms",
            do_convert_rgb=False,
        )

        inputs = dict(inputs.items())
        outputs = model(**inputs, feature_ensemble=True)

        expected_shape = (2, 3, 896, 448)
        expected_slice = ms.Tensor(
            [
                [[-2.1201, -2.1192, -2.1189], [-2.1217, -2.1210, -2.1204],
                    [-2.1216, -2.1202, -2.1194]],
                [[-2.0393, -2.0390, -2.0387], [-2.0402, -2.0402, -2.0397],
                    [-2.0400, -2.0394, -2.0388]],
                [[-1.8083, -1.8076, -1.8077], [-1.8105, -1.8102, -1.8099],
                    [-1.8105, -1.8095, -1.8090]],
            ]
        )

        self.assertEqual(outputs.pred_masks.shape, expected_shape)
        self.assertTrue(np.allclose(outputs.pred_masks[0, :, 448:451, :3].asnumpy(
        ), expected_slice.asnumpy(), atol=4e-4))

    @unittest.skip(reason="Due to the inability to generate random numbers consistent with torch.randperm,\
                   we can only pass the test locally by loading data files generated with torch.randperm.")
    def test_one_shot_with_label(self):
        model = SegGptForImageSegmentation.from_pretrained(
            "BAAI/seggpt-vit-large")

        image_processor = self.default_image_processor

        images, masks = prepare_img()

        input_image = images[1]
        label = masks[1]
        prompt_image = images[0]
        prompt_mask = masks[0]

        inputs = image_processor(
            images=input_image,
            prompt_masks=prompt_mask,
            prompt_images=prompt_image,
            return_tensors="ms",
            do_convert_rgb=False,
        )

        labels = image_processor(images=None, prompt_masks=label, return_tensors="ms", do_convert_rgb=False)[
            "prompt_masks"
        ]

        bool_masked_pos = prepare_bool_masked_pos(model.config)

        outputs = model(**inputs, labels=labels,
                        bool_masked_pos=bool_masked_pos)

        expected_loss = ms.Tensor(0.0074)
        self.assertTrue(np.allclose(outputs.loss.asnumpy(),
                        expected_loss.asnumpy(), atol=1e-4))

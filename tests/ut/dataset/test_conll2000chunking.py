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
Test CoNLL2000Chunking
"""
import os
import unittest
import pytest
from mindnlp.dataset import CoNLL2000Chunking
from mindnlp.dataset import load


class TestCoNLL2000Chunking(unittest.TestCase):
    r"""
    Test CoNLL2000Chunking
    """

    def setUp(self):
        self.input = None

    @pytest.mark.skip(reason="this ut has already tested")
    def test_conll2000chunking(self):
        """Test CoNLL2000Chunking"""
        num_lines = {
            "train": 8936,
            "test": 2012,
        }
        root = os.path.join(os.path.expanduser("~"), ".mindnlp")
        dataset_train, dataset_test = CoNLL2000Chunking(
            root=root, split=("train", "test")
        )
        assert dataset_train.get_dataset_size() == num_lines["train"]
        assert dataset_test.get_dataset_size() == num_lines["test"]

        dataset_train = CoNLL2000Chunking(root=root, split="train")
        dataset_test = CoNLL2000Chunking(root=root, split="test")
        assert dataset_train.get_dataset_size() == num_lines["train"]
        assert dataset_test.get_dataset_size() == num_lines["test"]

    @pytest.mark.skip(reason="this ut has already tested")
    def test_conll2000chunking_by_register(self):
        """test conll2000chunking by register"""
        root = os.path.join(os.path.expanduser("~"), ".mindnlp")
        _ = load(
            "CoNLL2000Chunking",
            root=root,
            split=("train", "test"),
        )
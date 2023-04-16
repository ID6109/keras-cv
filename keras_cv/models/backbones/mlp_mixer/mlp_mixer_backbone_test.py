# Copyright 2023 The KerasCV Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os

import tensorflow as tf
from absl.testing import parameterized
from tensorflow import keras

from keras_cv.models.backbones.mlp_mixer.mlp_mixer_backbone import (
    MLPMixerB16Backbone,
)
from keras_cv.models.backbones.mlp_mixer.mlp_mixer_backbone import (
    MLPMixerB32Backbone,
)
from keras_cv.models.backbones.mlp_mixer.mlp_mixer_backbone import (
    MLPMixerBackbone,
)
from keras_cv.models.backbones.mlp_mixer.mlp_mixer_backbone import (
    MLPMixerL16Backbone,
)
from keras_cv.utils.train import get_feature_extractor


class MobileNetV3BackboneTest(tf.test.TestCase, parameterized.TestCase):
    def setUp(self):
        self.input_batch = tf.ones(shape=(2, 224, 224, 3))

    def test_valid_call(self):
        model = MLPMixerBackbone(
            patch_size=16,
            num_blocks=12,
            hidden_dim=768,
            tokens_mlp_dim=384,
            channels_mlp_dim=3072,
            include_rescaling=False,
        )
        model(self.input_batch)

    def test_valid_call_with_rescaling(self):
        model = MLPMixerBackbone(
            patch_size=16,
            num_blocks=12,
            hidden_dim=768,
            tokens_mlp_dim=384,
            channels_mlp_dim=3072,
            include_rescaling=True,
        )
        model(self.input_batch)

    @parameterized.named_parameters(
        ("tf_format", "tf", "model"),
        ("keras_format", "keras_v3", "model.keras"),
    )
    def test_saved_model(self, save_format, filename):
        model = MLPMixerBackbone(
            patch_size=16,
            num_blocks=12,
            hidden_dim=768,
            tokens_mlp_dim=384,
            channels_mlp_dim=3072,
            include_rescaling=True,
        )
        model_output = model(self.input_batch)
        save_path = os.path.join(self.get_temp_dir(), filename)
        model.save(save_path, save_format=save_format)
        restored_model = keras.models.load_model(save_path)

        # Check we got the real object back.
        self.assertIsInstance(restored_model, MLPMixerBackbone)

        # Check that output matches.
        restored_output = restored_model(self.input_batch)
        self.assertAllClose(model_output, restored_output)

    @parameterized.named_parameters(
        ("tf_format", "tf", "model"),
        ("keras_format", "keras_v3", "model.keras"),
    )
    def test_model_backbone_layer_names_stability(self):
        model = MLPMixerBackbone(
            patch_size=16,
            num_blocks=12,
            hidden_dim=768,
            tokens_mlp_dim=384,
            channels_mlp_dim=3072,
            include_rescaling=False,
        )
        model_2 = MLPMixerBackbone(
            patch_size=16,
            num_blocks=12,
            hidden_dim=768,
            tokens_mlp_dim=384,
            channels_mlp_dim=3072,
            include_rescaling=False,
        )
        layers_1 = model.layers
        layers_2 = model_2.layers
        for i in range(len(layers_1)):
            if "input" in layers_1[i].name:
                continue
            self.assertEquals(layers_1[i].name, layers_2[i].name)

    def test_create_backbone_model_with_level_config(self):
        model = MLPMixerBackbone(
            patch_size=16,
            num_blocks=12,
            hidden_dim=768,
            tokens_mlp_dim=384,
            channels_mlp_dim=3072,
            include_rescaling=False,
            input_shape=[256, 256, 3],
        )
        levels = [3, 4]
        layer_names = [model.pyramid_level_inputs[level] for level in [3, 4]]
        backbone_model = get_feature_extractor(model, layer_names, levels)
        inputs = tf.keras.Input(shape=[256, 256, 3])
        outputs = backbone_model(inputs)
        self.assertLen(outputs, 2)
        self.assertEquals(list(outputs.keys()), [3, 4])
        self.assertEquals(outputs[3].shape, [None, 32, 32, 512])
        self.assertEquals(outputs[4].shape, [None, 16, 16, 1024])

    @parameterized.named_parameters(
        ("one_channel", 1),
        ("four_channels", 4),
    )
    def test_application_variable_input_channels(self, num_channels):
        model = MLPMixerBackbone(
            patch_size=16,
            num_blocks=12,
            hidden_dim=768,
            tokens_mlp_dim=384,
            channels_mlp_dim=3072,
            input_shape=(None, None, num_channels),
            include_rescaling=False,
        )
        self.assertEqual(model.output_shape, (None, None, None, 2048))

    @parameterized.named_parameters(
        ("B16", MLPMixerB16Backbone),
        ("B32", MLPMixerB32Backbone),
        ("L16", MLPMixerL16Backbone),
    )
    def test_specific_arch_forward_pass(self, arch_class):
        backbone = arch_class()
        backbone(tf.random.uniform(shape=[2, 256, 256, 3]))


if __name__ == "__main__":
    tf.test.main()
#!/usr/bin/env python3

import unittest

import torch
from captum.attr._core.layer.grad_cam import LayerGradCam

from ..helpers.basic_models import BasicModel_MultiLayer, BasicModel_ConvNet_One_Conv
from ..helpers.utils import assertTensorAlmostEqual, BaseTest


class Test(BaseTest):
    def test_simple_input_non_conv(self):
        net = BasicModel_MultiLayer()
        inp = torch.tensor([[0.0, 100.0, 0.0]], requires_grad=True)
        self._grad_cam_test_assert(net, net.linear0, inp, [400.0])

    def test_simple_input_conv(self):
        net = BasicModel_ConvNet_One_Conv()
        inp = torch.arange(16).view(1, 1, 4, 4).float()
        self._grad_cam_test_assert(net, net.conv1, inp, [[11.25, 13.5], [20.25, 22.5]])

    def test_simple_input_conv_relu(self):
        net = BasicModel_ConvNet_One_Conv()
        inp = torch.arange(16).view(1, 1, 4, 4).float()
        self._grad_cam_test_assert(net, net.relu1, inp, [[0.0, 4.0], [28.0, 32.5]])

    def test_simple_input_conv_without_final_relu(self):
        net = BasicModel_ConvNet_One_Conv()
        inp = torch.arange(16).view(1, 1, 4, 4).float()
        inp.requires_grad_()
        # Adding negative value to test final relu is not applied by default
        inp[0, 0, 1, 1] = -4.0
        self._grad_cam_test_assert(
            net, net.conv1, inp, 0.5625 * inp, attribute_to_layer_input=True
        )

    def test_simple_input_conv_fc_with_final_relu(self):
        net = BasicModel_ConvNet_One_Conv()
        inp = torch.arange(16).view(1, 1, 4, 4).float()
        inp.requires_grad_()
        # Adding negative value to test final relu is applied
        inp[0, 0, 1, 1] = -4.0
        exp = 0.5625 * inp
        exp[0, 0, 1, 1] = 0.0
        self._grad_cam_test_assert(
            net,
            net.conv1,
            inp,
            exp,
            attribute_to_layer_input=True,
            relu_attributions=True,
        )

    def test_simple_multi_input_conv(self):
        net = BasicModel_ConvNet_One_Conv()
        inp = torch.arange(16).view(1, 1, 4, 4).float()
        inp2 = torch.ones((1, 1, 4, 4))
        self._grad_cam_test_assert(
            net, net.conv1, (inp, inp2), [[14.5, 19.0], [32.5, 37.0]]
        )

    def _grad_cam_test_assert(
        self,
        model,
        target_layer,
        test_input,
        expected_activation,
        additional_input=None,
        attribute_to_layer_input=False,
        relu_attributions=False,
    ):
        layer_gc = LayerGradCam(model, target_layer)
        attributions = layer_gc.attribute(
            test_input,
            target=0,
            additional_forward_args=additional_input,
            attribute_to_layer_input=attribute_to_layer_input,
            relu_attributions=relu_attributions,
        )
        assertTensorAlmostEqual(self, attributions, expected_activation, delta=0.01)


if __name__ == "__main__":
    unittest.main()

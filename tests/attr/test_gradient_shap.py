#!/usr/bin/env python3

import torch
import numpy as np

from .helpers.utils import assertArraysAlmostEqual, assertTensorAlmostEqual, BaseTest
from .helpers.classification_models import SoftmaxModel
from .helpers.basic_models import BasicModel2, BasicLinearModel
from captum.attr._core.gradient_shap import GradientShap
from captum.attr._core.integrated_gradients import IntegratedGradients


class Test(BaseTest):

    # This test reproduces some of the test cases from the original implementation
    # https://github.com/slundberg/shap/
    # explainers/test_gradient.py
    def test_basic_multi_input(self):
        batch_size = 10

        x1 = torch.ones(batch_size, 3)
        x2 = torch.ones(batch_size, 4)
        inputs = (x1, x2)

        batch_size_baselines = 20
        baselines = (
            torch.zeros(batch_size_baselines, 3),
            torch.zeros(batch_size_baselines, 4),
        )

        model = BasicLinearModel()
        model.eval()
        model.zero_grad()

        np.random.seed(0)
        torch.manual_seed(0)
        gradient_shap = GradientShap(model)
        n_samples = 50
        attributions, delta = gradient_shap.attribute(
            inputs, baselines, n_samples=n_samples, return_convergence_delta=True
        )
        attributions_without_delta = gradient_shap.attribute((x1, x2), baselines)

        self._assert_attribution_delta(inputs, attributions, n_samples, delta)
        # Compare with integrated gradients
        ig = IntegratedGradients(model)
        baselines = (torch.zeros(batch_size, 3), torch.zeros(batch_size, 4))
        attributions_ig = ig.attribute(inputs, baselines=baselines)
        self._assert_shap_ig_comparision(attributions, attributions_ig)

        # compare attributions retrieved with and without
        # `return_convergence_delta` flag
        for attribution, attribution_without_delta in zip(
            attributions, attributions_without_delta
        ):
            assertTensorAlmostEqual(self, attribution, attribution_without_delta)

    def test_basic_scalar_baselines_multi_input(self):
        inputs = (torch.ones(10, 3), torch.rand(10, 4))
        baselines_scalars = (0.0, 0.0)
        baselines_tensors = (
            torch.zeros(1, 3),
            torch.zeros(10, 4),
        )

        model = BasicLinearModel()
        model.eval()

        gradient_shap = GradientShap(model)
        attributions_base_scalars, _ = gradient_shap.attribute(
            inputs, baselines_scalars, n_samples=50, return_convergence_delta=True
        )
        attributions_base_tnsrs, _ = gradient_shap.attribute(
            inputs, baselines_tensors, n_samples=50, return_convergence_delta=True
        )
        assertTensorAlmostEqual(
            self, attributions_base_scalars[0], attributions_base_tnsrs[0]
        )
        assertTensorAlmostEqual(
            self, attributions_base_scalars[1], attributions_base_tnsrs[1]
        )

    def test_classification_baselines_as_function(self):
        num_in = 40
        inputs = torch.arange(0.0, num_in * 2.0).reshape(2, num_in)

        def generate_baselines():
            return torch.arange(0.0, num_in * 4.0).reshape(4, num_in)

        def generate_baselines_with_inputs(inputs):
            return torch.arange(0.0, inputs.shape[1] * 2.0).reshape(2, inputs.shape[1])

        def generate_baselines_returns_array():
            return np.arange(0.0, num_in * 4.0).reshape(4, num_in)

        # 10-class classification model
        model = SoftmaxModel(num_in, 20, 10)
        model.eval()
        model.zero_grad()

        gradient_shap = GradientShap(model)
        n_samples = 10
        attributions, delta = gradient_shap.attribute(
            inputs,
            baselines=generate_baselines,
            target=torch.tensor(1),
            n_samples=n_samples,
            stdevs=0.009,
            return_convergence_delta=True,
        )
        self._assert_attribution_delta((inputs,), (attributions,), n_samples, delta)

        attributions, delta = gradient_shap.attribute(
            inputs,
            baselines=generate_baselines_with_inputs,
            target=torch.tensor(1),
            n_samples=n_samples,
            stdevs=0.00001,
            return_convergence_delta=True,
        )
        self._assert_attribution_delta((inputs,), (attributions,), n_samples, delta)

        with self.assertRaises(AssertionError):
            attributions, delta = gradient_shap.attribute(
                inputs,
                baselines=generate_baselines_returns_array,
                target=torch.tensor(1),
                n_samples=n_samples,
                stdevs=0.00001,
                return_convergence_delta=True,
            )

    def test_classification(self):
        num_in = 40
        inputs = torch.arange(0.0, num_in * 2.0).reshape(2, num_in)
        baselines = torch.arange(0.0, num_in * 4.0).reshape(4, num_in)
        target = torch.tensor(1)
        # 10-class classification model
        model = SoftmaxModel(num_in, 20, 10)
        model.eval()
        model.zero_grad()

        gradient_shap = GradientShap(model)
        n_samples = 10
        attributions, delta = gradient_shap.attribute(
            inputs,
            baselines=baselines,
            target=target,
            n_samples=n_samples,
            stdevs=0.009,
            return_convergence_delta=True,
        )
        self._assert_attribution_delta((inputs,), (attributions,), n_samples, delta)

        # try to call `compute_convergence_delta` externally
        with self.assertRaises(AssertionError):
            gradient_shap.compute_convergence_delta(
                attributions, inputs, baselines, target=target
            )
        # now, let's expand target and choose random baselines from `baselines` tensor
        rand_indices = np.random.choice(baselines.shape[0], inputs.shape[0]).tolist()
        chosen_baselines = baselines[rand_indices]

        target_extendes = torch.tensor([1, 1])
        external_delta = gradient_shap.compute_convergence_delta(
            attributions, chosen_baselines, inputs, target=target_extendes
        )
        self._assert_delta(external_delta)

        # Compare with integrated gradients
        ig = IntegratedGradients(model)
        baselines = torch.arange(0.0, num_in * 2.0).reshape(2, num_in)
        attributions_ig = ig.attribute(inputs, baselines=baselines, target=target)
        self._assert_shap_ig_comparision((attributions,), (attributions_ig,))

    def test_basic_relu_multi_input(self):
        model = BasicModel2()

        input1 = torch.tensor([[3.0]])
        input2 = torch.tensor([[1.0]], requires_grad=True)

        baseline1 = torch.tensor([[0.0]])
        baseline2 = torch.tensor([[0.0]])
        inputs = (input1, input2)
        baselines = (baseline1, baseline2)

        gs = GradientShap(model)
        n_samples = 30000
        attributions, delta = gs.attribute(
            inputs,
            baselines=baselines,
            n_samples=n_samples,
            return_convergence_delta=True,
        )
        self._assert_attribution_delta(inputs, attributions, n_samples, delta)

        ig = IntegratedGradients(model)
        attributions_ig = ig.attribute(inputs, baselines=baselines)
        self._assert_shap_ig_comparision(attributions, attributions_ig)

    def _assert_delta(self, delta):
        delta_condition = all(abs(delta.numpy().flatten()) < 0.0006)
        self.assertTrue(
            delta_condition,
            "Sum of SHAP values {} does"
            " not match the difference of endpoints.".format(delta),
        )

    def _assert_attribution_delta(self, inputs, attributions, n_samples, delta):
        for input, attribution in zip(inputs, attributions):
            self.assertEqual(attribution.shape, input.shape)
        bsz = inputs[0].shape[0]
        self.assertEqual([bsz * n_samples], list(delta.shape))

        delta = torch.mean(delta.reshape(bsz, -1), dim=1)
        self._assert_delta(delta)

    def _assert_shap_ig_comparision(self, attributions1, attributions2):
        for attribution1, attribution2 in zip(attributions1, attributions2):
            for attr_row1, attr_row2 in zip(
                attribution1.detach().numpy(), attribution2.detach().numpy()
            ):
                assertArraysAlmostEqual(attr_row1, attr_row2, delta=0.005)

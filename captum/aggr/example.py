import matplotlib.pyplot as plt
import numpy as np

import torch
import torch.nn as nn
import torch.nn.functional as F

import torchvision
import torchvision.transforms as transforms
import torchvision.transforms.functional as TF

from torchvision import models

from captum.attr import IntegratedGradients

transform = transforms.Compose([transforms.ToTensor(), transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))])

trainset = torchvision.datasets.CIFAR10(root='./data', train=True,
        download=True, transform=transform)
trainloader = torch.utils.data.DataLoader(trainset, batch_size=4,
        shuffle=True, num_workers=2)

testset = torchvision.datasets.CIFAR10(root='./data', train=False,
        download=True, transform=transform)
testloader = torch.utils.data.DataLoader(testset, batch_size=4,
        shuffle=False, num_workers=2)

classes = ('plane', 'car', 'bird', 'cat',
        'deer', 'dog', 'frog', 'horse', 'ship', 'truck')

class Net(nn.Module):
    def __init__(self):
        super(Net, self).__init__()
        self.conv1 = nn.Conv2d(3, 6, 5)
        self.pool1 = nn.MaxPool2d(2, 2)
        self.pool2 = nn.MaxPool2d(2, 2)
        self.conv2 = nn.Conv2d(6, 16, 5)
        self.fc1 = nn.Linear(16 * 5 * 5, 120)
        self.fc2 = nn.Linear(120, 84)
        self.fc3 = nn.Linear(84, 10)
        self.relu1 = nn.ReLU()
        self.relu2 = nn.ReLU()
        self.relu3 = nn.ReLU()
        self.relu4 = nn.ReLU()

    def forward(self, x):
        x = self.pool1(self.relu1(self.conv1(x)))
        x = self.pool2(self.relu2(self.conv2(x)))
        x = x.view(-1, 16 * 5 * 5)
        x = self.relu3(self.fc1(x))
        x = self.relu4(self.fc2(x))
        x = self.fc3(x)
        return x


net = Net()
net.load_state_dict(torch.load('./tutorials/models/cifar_torchvision.pt'))
net.eval()

def attribute_image_features(algorithm, input, out, **kwargs):
    net.zero_grad()
    tensor_attributions = algorithm.attribute(input, target=out, **kwargs)
    return tensor_attributions

def attrib_iter(n=10):
    ig = IntegratedGradients(net)
    for i, (x, y) in enumerate(testloader):
        if i == 9:
            break

        out = net(x)
        out = F.softmax(out, dim=1)
        _, pred_idx = torch.topk(out, 1)
        pred_idx.squeeze_()

        z = None
        for j in range(x.size(0)):
            input = x[j].unsqueeze(0)
            input.requires_grad = True

            attr_ig = ig.attribute(input, target=pred_idx[j], baselines=input * 0)
            attr_ig = np.transpose(attr_ig.squeeze().cpu().detach().numpy(), (1, 2, 0))

            if z is None:
                z = np.zeros_like(attr_ig)

            z += attr_ig

        z /= x.size(0)

        yield z


from captum.aggr.aggregator import Aggregator
from captum.aggr.stat import Mean, Var, StdDev, Min, Max

# TODO: discuss constructing here vs. inside class
aggr = Aggregator([Mean(), Var(), StdDev(), Min(), Max()])
for attrib in attrib_iter():
    aggr.update(attrib)

print(aggr.summary)

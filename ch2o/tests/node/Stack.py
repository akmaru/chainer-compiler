# coding: utf-8

import chainer
import chainer.functions as F


class Stack(chainer.Chain):
    def forward(self, x, y):
        y1 = F.stack((x, y))
        return y1


class StackAxis0(chainer.Chain):
    def forward(self, x, y):
        y1 = F.stack((x, y), axis=0)
        return y1


class StackAxis1(chainer.Chain):
    def forward(self, x, y):
        y1 = F.stack((x, y), axis=1)
        return y1


class StackAxis2(chainer.Chain):
    def forward(self, x, y):
        y1 = F.stack((x, y), axis=2)
        return y1


# ======================================

import ch2o
import numpy as np

if __name__ == '__main__':
    v = np.random.rand(5, 4, 2).astype(np.float32)
    w = np.random.rand(5, 4, 2).astype(np.float32)

    ch2o.generate_testcase(Stack, [v, w])
    ch2o.generate_testcase(StackAxis0, [v, w], subname='axis0')
    ch2o.generate_testcase(StackAxis1, [v, w], subname='axis1')
    ch2o.generate_testcase(StackAxis2, [v, w], subname='axis2')

#!/usr/bin/python3

import os

import chainer
import numpy as np
from onnx import onnx_pb
import onnx_chainer


def replace_id(builtins=__builtins__):
    orig_id = id

    def my_id(x):
        if isinstance(x, chainer.Parameter):
            return x.name
        return orig_id(x)
    builtins.id = my_id


def makedirs(d):
    if not os.path.exists(d):
        os.makedirs(d)


class AnyModel(chainer.Chain):
    def __init__(self, fn, params):
        super(AnyModel, self).__init__()
        with self.init_scope():
            for name, value in params.items():
                setattr(self, name, chainer.Parameter(value, name=name))
        self.fn = fn

    def __call__(self, *args):
        result = self.fn(self, *args)
        return result


def create_backprop_test(test_name, fn, **kwargs):
    test_dir = 'out/backprop_test_%s' % test_name
    test_model_path = os.path.join(test_dir, 'model.onnx')
    test_data_dir = os.path.join(test_dir, 'test_data_set_0')
    makedirs(test_data_dir)

    params = {}
    for name, value in kwargs.items():
        params[name] = np.array(value, np.float32)
    model = AnyModel(fn, params)

    onnx_chainer.export(model, (),
                        filename=test_model_path,
                        graph_name='backprop_test_' + test_name)

    model.cleargrads()
    result = model()
    result.grad = np.ones(result.shape, result.dtype)
    result.backward()

    param_names = []
    output_names = []
    xmodel = onnx_pb.ModelProto()
    with open(test_model_path, 'rb') as f:
        xmodel.ParseFromString(f.read())
        for param in xmodel.graph.initializer:
            assert param.name
            param_names.append(param.name)
        for output in xmodel.graph.output:
            assert output.name
            output_names.append(output.name)

    assert len(output_names) == 1
    assert sorted(param_names) == sorted(params)

    outputs = [(output_names[0], result)]
    for name in sorted(params):
        value = getattr(model, name).grad
        outputs.append(('grad_out@' + name, value))

    for i, (xname, value) in enumerate(outputs):
        tensor = onnx_pb.TensorProto(name=xname,
                                     dims=value.shape,
                                     data_type=onnx_pb.TensorProto.FLOAT)
        tensor.float_data.extend(np.array(value.data).flat)
        with open(os.path.join(test_data_dir, 'output_%d.pb' % i), 'wb') as f:
            f.write(tensor.SerializeToString())


class BackpropTest(object):
    def __init__(self, name, fn, **kwargs):
        self.name = name
        self.fn = fn
        self.kwargs = kwargs

    def generate(self):
        create_backprop_test(self.name, self.fn, **self.kwargs)


def get_backprop_tests():
    F = chainer.functions
    tests = []

    def test(name, fn, **kwargs):
        tests.append(BackpropTest(name, fn, **kwargs))

    test('add1', lambda m: m.a + m.b, a=[3], b=[7])
    test('mul1', lambda m: m.a * m.b, a=[3], b=[7])
    test('add', lambda m: m.a + m.b, a=[3, 5], b=[7, 2])
    test('sub', lambda m: m.a - m.b, a=[3, 5], b=[7, 2])
    test('mul', lambda m: m.a * m.b, a=[3, 5], b=[7, 2])
    test('div', lambda m: m.a / m.b, a=[3, 5], b=[7, 2])
    test('neg', lambda m: -m.a, a=[3, 5])
    test('reduce_sum', lambda m: F.sum(m.a, axis=0), a=[3, 5, 7])

    return tests


def main():
    replace_id()
    for test in get_backprop_tests():
        test.generate()


if __name__ == '__main__':
    main()
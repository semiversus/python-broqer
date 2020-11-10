from collections import OrderedDict

import pytest

from broqer.op.bitwise import BitwiseCombineLatest, map_bit
from broqer import Publisher, NONE
from tests import helper_multi, helper_single

test_vector = [
    # init, bit_value_map, input_vector, output_vector
    (0, [(0, True), (1, False), (4, True)],
        [(NONE, True, NONE)],
        [17, 19]),
    (~0, [(0, True)],
        [(True,), (False,), (True,)],
        [~0, ~0, ~1, ~0]),
    (0xAA, [(0, False), (1, False), (7, True)],
        [(NONE, True, NONE), (True, True, True), (False, NONE, NONE), (False, False, False)],
        (0xA8, 0xAA, 0xAB, 0xAA, 0x28))
]
@pytest.mark.parametrize('method', [helper_multi.check_get_method, helper_multi.check_subscription, helper_multi.check_dependencies])
@pytest.mark.parametrize('init,bit_value_map,input_vector,output_vector', test_vector)
def test_bitwise_combine_latest(method, init, bit_value_map, input_vector, output_vector):
    publisher_bit_mapping = OrderedDict([(Publisher(v), b) for b, v in bit_value_map])
    i_vector = [tuple(v for k, v in bit_value_map)] + input_vector

    operator = BitwiseCombineLatest(publisher_bit_mapping, init)

    method(operator, i_vector, output_vector)


test_vector = [
    # bit_index, input_vector, output_vector
    (0, [0, 1, 2, 3, ~0], [False, True, False, True, True]),
    (128, [~0, 0, 1<<128, (1<<128)-1], [True, False, True, False])
]
@pytest.mark.parametrize('method', [helper_single.check_get_method, helper_single.check_subscription, helper_single.check_dependencies])
@pytest.mark.parametrize('bit_index, input_vector,output_vector', test_vector)
def test_map_bit(method, bit_index, input_vector, output_vector):
    operator = map_bit(bit_index)

    method(operator, input_vector, output_vector)

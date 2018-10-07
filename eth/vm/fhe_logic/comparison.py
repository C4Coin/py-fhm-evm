from eth import constants
from eth.vm.nufhe import nufhe
import numpy


from eth.utils.numeric import (
    signed_to_unsigned,
    unsigned_to_signed,
)


def lt(computation):
    """
    Lesser Comparison
    """
    left, right = computation.stack_pop(num_items=2, type_hint=constants.UINT256)

    if left < right:
        result = 1
    else:
        result = 0

    computation.stack_push(result)


def gt(computation):
    """
    Greater Comparison
    """
    left, right = computation.stack_pop(num_items=2, type_hint=constants.UINT256)

    if left > right:
        result = 1
    else:
        result = 0

    computation.stack_push(result)


def slt(computation):
    """
    Signed Lesser Comparison
    """
    left, right = map(
        unsigned_to_signed,
        computation.stack_pop(num_items=2, type_hint=constants.UINT256),
    )

    if left < right:
        result = 1
    else:
        result = 0

    computation.stack_push(signed_to_unsigned(result))


def sgt(computation):
    """
    Signed Greater Comparison
    """
    left, right = map(
        unsigned_to_signed,
        computation.stack_pop(num_items=2, type_hint=constants.UINT256),
    )

    if left > right:
        result = 1
    else:
        result = 0

    computation.stack_push(signed_to_unsigned(result))


def eq(computation):
    """
    Equality
    """
    left, right = computation.stack_pop(num_items=2, type_hint=constants.UINT256)

    if left == right:
        result = 1
    else:
        result = 0

    computation.stack_push(result)


def iszero(computation):
    """
    Not
    """
    value = computation.stack_pop(type_hint=constants.UINT256)

    if value == 0:
        result = 1
    else:
        result = 0

    computation.stack_push(result)


def and_op(computation):
    """
    Bitwise And
    """
    left, right = computation.stack_pop(num_items=2, type_hint=constants.UINT256)

    result = left & right

    computation.stack_push(result)


def or_op(computation):
    """
    Bitwise Or
    """
    left, right = computation.stack_pop(num_items=2, type_hint=constants.UINT256)

    result = left | right

    computation.stack_push(result)


def xor(computation):
    """
    Bitwise XOr
    """
    left, right = computation.stack_pop(num_items=2, type_hint=constants.UINT256)

    result = left ^ right

    computation.stack_push(result)


def not_op(computation):
    """
    Not
    """
    value = computation.stack_pop(type_hint=constants.UINT256)

    num_bits = 256
    value_array = numpy.array([(value >> bit) & 1 for bit in range(num_bits -1, -1, 1)])

    result = nufhe.empty_ciphertext(self.thr, self.program.key.params, left.shape)
    nufhe.gate_not(self.thr, self.program.key, result, value_array, perf_params=self.pp)

    computation.stack_push(result)


def byte_op(computation):
    """
    Bitwise And
    """
    position, value = computation.stack_pop(num_items=2, type_hint=constants.UINT256)

    if position >= 32:
        result = 0
    else:
        result = (value // pow(256, 31 - position)) % 256

    computation.stack_push(result)

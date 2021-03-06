from eth_hash.auto import keccak

from eth.constants import (
    GAS_CODEDEPOSIT,
    STACK_DEPTH_LIMIT,
)
from eth import precompiles
from eth.vm.computation import (
    BaseComputation
)
from eth.exceptions import (
    OutOfGas,
    InsufficientFunds,
    StackDepthLimit,
)
from eth.utils.address import (
    force_bytes_to_address,
)
from eth.utils.hexadecimal import (
    encode_hex,
)

from .opcodes import FHE_OPCODES

FHE_PRECOMPILES = {
    force_bytes_to_address(b'\x01'): precompiles.ecrecover,
    force_bytes_to_address(b'\x02'): precompiles.sha256,
    force_bytes_to_address(b'\x03'): precompiles.ripemd160,
    force_bytes_to_address(b'\x04'): precompiles.identity,
}

from reikna.cluda import any_api
import numpy
import nufhe


class FheComputation(BaseComputation):
    """
    A class for all execution computations in the ``Fhe`` fork.
    Inherits from :class:`~eth.vm.computation.BaseComputation`
    """
    # Override
    opcodes = FHE_OPCODES
    _precompiles = FHE_PRECOMPILES


    def __init__(self,
                 state,
                 message,
                 transaction_context) -> None:

        super(BaseComputation, self).__init__(state, message, transaction_context)
        self.thr = any_api().Thread.create(interactive=True)
        self.rng = numpy.random.RandomState() # hack a rng for now
        self.pp = nufhe.performance_parameters(single_kernel_bootstrap=False, transforms_per_block=1)

        secret_key, bootstrap_key = nufhe.make_key_pair(self.thr, self.rng, transform_type='NTT') # prob. goes somewhere else
        self.secret_key = secret_key
        self.bootstrap_key = bootstrap_key

        self.key = None

        self.size = 32

    def apply_message(self):
        snapshot = self.state.snapshot()

        if self.msg.depth > STACK_DEPTH_LIMIT:
            raise StackDepthLimit("Stack depth limit reached")

        if self.msg.should_transfer_value and self.msg.value:
            sender_balance = self.state.account_db.get_balance(self.msg.sender)

            if sender_balance < self.msg.value:
                raise InsufficientFunds(
                    "Insufficient funds: {0} < {1}".format(sender_balance, self.msg.value)
                )

            self.state.account_db.delta_balance(self.msg.sender, -1 * self.msg.value)
            self.state.account_db.delta_balance(self.msg.storage_address, self.msg.value)

            self.logger.trace(
                "TRANSFERRED: %s from %s -> %s",
                self.msg.value,
                encode_hex(self.msg.sender),
                encode_hex(self.msg.storage_address),
            )

        self.state.account_db.touch_account(self.msg.storage_address)

        computation = self.apply_computation(
            self.state,
            self.msg,
            self.transaction_context,
        )

        if computation.is_error:
            self.state.revert(snapshot)
        else:
            self.state.commit(snapshot)

        return computation

    def apply_create_message(self):
        computation = self.apply_message()

        if computation.is_error:
            return computation
        else:
            contract_code = computation.output

            if contract_code:
                contract_code_gas_fee = len(contract_code) * GAS_CODEDEPOSIT
                try:
                    computation.consume_gas(
                        contract_code_gas_fee,
                        reason="Write contract code for CREATE",
                    )
                except OutOfGas:
                    computation.output = b''
                else:
                    self.logger.trace(
                        "SETTING CODE: %s -> length: %s | hash: %s",
                        encode_hex(self.msg.storage_address),
                        len(contract_code),
                        encode_hex(keccak(contract_code))
                    )
                    self.state.account_db.set_code(self.msg.storage_address, contract_code)
            return computation

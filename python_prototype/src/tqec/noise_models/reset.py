import cirq

from tqec.noise_models import BaseNoiseModel


class XNoiseAfterReset(BaseNoiseModel):
    def __init__(self, p: float):
        cirq.value.validate_probability(p, "bitflip noise after reset probability")
        self._p = p
        self._noisy_gate: cirq.BitFlipChannel = cirq.bit_flip(self._p)
        super().__init__()

    def noisy_operation(self, operation: cirq.Operation) -> cirq.OP_TREE:
        if isinstance(operation.gate, cirq.ResetChannel):
            return [
                operation,
                [
                    self._noisy_gate.on(qubit).with_tags(cirq.VirtualTag())
                    for qubit in operation.qubits
                ],
            ]
        else:
            return self.recurse_in_operation_if_CircuitOperation(operation)

import cirq


class BaseNoiseModel(cirq.NoiseModel):
    def __init__(self, probability: float) -> None:
        self._p = cirq.value.validate_probability(
            probability, "noise model probability"
        )
        super().__init__()

    def recurse_in_operation_if_CircuitOperation(
        self, operation: cirq.Operation
    ) -> cirq.OP_TREE:
        # If we have an instance of CircuitOperation, special handling should be performed to avoid
        # inserting a depolarizing channel as large as the circuit. In this specific case, we recurse
        # into the CircuitOperation, and modify a copy of its underlying circuit.
        if isinstance(operation, cirq.CircuitOperation):
            noisy_circuit = (
                operation.circuit.unfreeze(copy=True).with_noise(self).freeze()
            )
            return operation.replace(circuit=noisy_circuit)
        return operation

    def is_in_effect(self) -> bool:
        return self._p > 1e-12

    @property
    def prob(self) -> float:
        return self._p

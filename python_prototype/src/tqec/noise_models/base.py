import cirq


class BaseNoiseModel(cirq.NoiseModel):
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

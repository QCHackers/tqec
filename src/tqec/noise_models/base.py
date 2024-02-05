import cirq


class BaseNoiseModel(cirq.NoiseModel):
    def __init__(self, probability: float) -> None:
        """Base class for all `tqec` noise models

        :param probability: strength of the noise described by the instance.
        """
        self._p = cirq.value.validate_probability(
            probability, "noise model probability"
        )
        super().__init__()

    def recurse_in_operation_if_circuit_operation(
        self, operation: cirq.Operation
    ) -> cirq.OP_TREE:
        """Helper method to handle cirq.CircuitOperation nearly transparently

        This method is here to help sub-classes handle cirq.CircuitOperation instances
        nearly transparently: they simply have to think about using this method if they stumble
        upon such an operation, and that is all!

        This method does nothing if the provided operation is not a cirq.CircuitOperation instance
        and returns the same, unmodified, instance.

        :param operation: a cirq.Operation instance that will be recursed in if and only if it is
            a cirq.CircuitOperation instance.
        :returns: a unmodified cirq.Operation instance if the provided operation is not an instance
            of cirq.CircuitOperation. Else, the result of applying the noise model (subclass of this
            class) calling this method on the cirq.Circuit instance wrapped in the operation.
        """
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

import cirq


class QubitTypeException(Exception):
    def __init__(self, expected_qubit_type: type, found_qubit_type: type) -> None:
        super().__init__(
            f"Excepted only instances of {expected_qubit_type.__name__} but found an instance of {found_qubit_type.__name__}."
        )


class MeasurementAppliedOnMultipleQubitsException(Exception):
    def __init__(self, qubits: tuple[cirq.Qid, ...]) -> None:
        super().__init__(
            f"Found a measurement applied on multiple qubits ({qubits}) which should not happen."
        )

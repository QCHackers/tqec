class TQECException(Exception):
    pass


class QubitTypeException(TQECException):
    def __init__(self, expected_qubit_type: type, found_qubit_type: type) -> None:
        super().__init__(
            f"Excepted only instances of {expected_qubit_type.__name__} but found an instance of {found_qubit_type.__name__}."
        )

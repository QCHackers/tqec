import cirq

from tqec.circuit.schedule import ScheduledCircuit
from tqec.exceptions import TQECException
from tqec.plaquette.library.utils.detectors import make_memory_experiment_detector
from tqec.plaquette.library.utils.pauli import make_pauli_syndrome_measurement_circuit
from tqec.plaquette.plaquette import Plaquette
from tqec.plaquette.qubit import PlaquetteQubits


def pauli_memory_plaquette(
    qubits: PlaquetteQubits,
    pauli_string: str,
    schedule: list[int],
    include_detector: bool = True,
    is_first_round: bool = False,
) -> Plaquette:
    (syndrome_qubit,) = qubits.get_syndrome_qubits()
    data_qubits = qubits.get_data_qubits()

    if len(pauli_string) != len(data_qubits):
        raise TQECException(
            f"{PauliMemoryPlaquette.__name__} requires the exact same "
            f"number of data qubits and Pauli terms. Got {len(pauli_string)} "
            f"pauli terms and {len(data_qubits)} data qubits."
        )

    circuit = make_pauli_syndrome_measurement_circuit(
        syndrome_qubit, data_qubits, pauli_string
    )
    if include_detector:
        circuit.append(
            cirq.Moment(make_memory_experiment_detector(syndrome_qubit, is_first_round))
        )

    return Plaquette(qubits, ScheduledCircuit(circuit, schedule))


class PauliMemoryPlaquette(Plaquette):
    def __init__(
        self,
        qubits: PlaquetteQubits,
        pauli_string: str,
        schedule: list[int],
        include_detector: bool = True,
        is_first_round: bool = False,
    ):
        (syndrome_qubit,) = qubits.get_syndrome_qubits()
        data_qubits = qubits.get_data_qubits()

        if len(pauli_string) != len(data_qubits):
            raise TQECException(
                f"{PauliMemoryPlaquette.__name__} requires the exact same "
                f"number of data qubits and Pauli terms. Got {len(pauli_string)} "
                f"pauli terms and {len(data_qubits)} data qubits."
            )

        circuit = make_pauli_syndrome_measurement_circuit(
            syndrome_qubit, data_qubits, pauli_string
        )
        if include_detector:
            circuit.append(
                cirq.Moment(
                    make_memory_experiment_detector(syndrome_qubit, is_first_round)
                )
            )

        super().__init__(qubits, ScheduledCircuit(circuit, schedule))

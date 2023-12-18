import numpy

from tqec.plaquette.qubit import PlaquetteQubit
from tqec.plaquette.schedule import ScheduledCircuit
from tqec.position import Shape2D


class Plaquette:
    def __init__(
        self,
        qubits: list[PlaquetteQubit],
        layer_circuits: list[ScheduledCircuit],
    ) -> None:
        """Represents a QEC plaquette"""
        self._qubits = qubits
        self._layer_circuits = layer_circuits

    def to_qubit_array(self) -> numpy.ndarray:
        """Should be specialised for specific plaquette types"""
        shape = self.shape
        array = numpy.zeros(shape.to_numpy_shape(), dtype=bool)
        for qubit in self.qubits:
            array[qubit.position.y, qubit.position.x] = True
        return array

    def get_layer(self, index: int) -> ScheduledCircuit:
        return self._layer_circuits[index]

    @property
    def number_of_layers(self) -> int:
        return len(self._layer_circuits)

    def append_layer(self, scheduled_circuit: ScheduledCircuit) -> None:
        self._layer_circuits.append(scheduled_circuit)

    def set_existing_layer(
        self, scheduled_circuit: ScheduledCircuit, index: int
    ) -> None:
        assert index < len(self._layer_circuits)
        self._layer_circuits[index] = scheduled_circuit

    @property
    def shape(self) -> Shape2D:
        maxx = max(qubit.position.x for qubit in self.qubits)
        maxy = max(qubit.position.y for qubit in self.qubits)
        return Shape2D(maxx + 1, maxy + 1)

    @property
    def qubits(self) -> list[PlaquetteQubit]:
        return self._qubits

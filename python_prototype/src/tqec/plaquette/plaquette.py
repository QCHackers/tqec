from dataclasses import dataclass

from cirq.circuits.circuit import Circuit
import numpy

from tqec.plaquette.qubit import PlaquetteQubit
from tqec.position import Shape2D


@dataclass
class Plaquette:
    qubits: list[PlaquetteQubit]
    layer_circuits: list[Circuit]

    def to_qubit_array(self) -> numpy.ndarray:
        """Should be specialised for specific plaquette types"""
        shape = self.shape
        array = numpy.zeros(shape.to_numpy_shape(), dtype=bool)
        for qubit in self.qubits:
            array[qubit.position.y, qubit.position.x] = True
        return array

    def get_layer(self, index: int) -> Circuit:
        return self.layer_circuits[index]

    @property
    def shape(self) -> Shape2D:
        maxx = max(qubit.position.x for qubit in self.qubits)
        maxy = max(qubit.position.y for qubit in self.qubits)
        return Shape2D(maxx + 1, maxy + 1)

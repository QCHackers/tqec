"""Internal reprenstation of plaquettes."""
from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, Iterable


class Stabilizer(Enum):
    """Default Pauli stabilizers."""

    I = auto()
    X = auto()
    Y = auto()
    Z = auto()


@dataclass
class Plaquette:
    """Plaquette class which will be defined by user input.

    Attributes:
        index (int): Index as used in the template.
        stabilizer (Stabilizer): Stabilizer type, for verification.
        circuit (int): Measurement Circuit. TODO define propper type.
        name (str): Display name for the plaquette.
    """

    index: int
    stabilizer: Stabilizer
    circuit: int
    name: str

    def __str__(self):
        return self.name

    def __repr__(self):
        return f"Plaquette(Index:{self.index}, Stabilizer={self.stabilizer.name}, Name={self.name})"

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Plaquette):
            return False
        return (
            self.index == other.index
            and self.stabilizer == other.stabilizer
            and self.circuit == other.circuit
            and self.name == other.name
        )

    def commutes(self, other: "Plaquette") -> bool:
        """Check if self commutes with another plaquette.

        Args:
            other (Plaquette): The other plaquette.

        Returns:
            bool: True if the two plaquettes commute.
        """
        if other.stabilizer == Stabilizer.I:
            return True
        match self.stabilizer:
            case Stabilizer.I:
                return True
            case Stabilizer.X:
                return other.stabilizer in [Stabilizer.X, Stabilizer.Z]
            case Stabilizer.Y:
                return other.stabilizer in [Stabilizer.Y]
            case Stabilizer.Z:
                return other.stabilizer in [Stabilizer.X, Stabilizer.Z]

    def circuits_match(
        self, other: "Plaquette", self_qubits: list[int], other_qubits: list[int]
    ) -> bool:
        """Check if self and another plaquette have matching circuits on the indicated qubits.

        Given the list of qubits, the two plaquettes have matching circuits iff
        all the qubits of self are measured before their respective counterparts in other.

        Args:
            other (Plaquette): The other plaquette.
            self_qubits (list[int]): The qubits of self to compare.
            other_qubits (list[int]): The qubits of other to compare to.

        Returns:
            bool: True if the two plaquettes are on the same circuit.
        """
        raise NotImplementedError


class PlaquetteFactory:
    """Factory class for Plaquette objects.

    Attributes:
        _id (int): Internal id.
    """

    plaquettes: dict[int, Plaquette]

    def __init__(self):
        self._id = 0

    def add(
        self,
        index: int,
        stabilizer: Stabilizer,
        circuit: int,
        name: str,
        *_: Any,
        overwrite: bool = False,
        **__: Any,
    ) -> Plaquette:
        """Add a new Plaquette object if it doesn't already exist.

        Args:
            index (int): Index as used in the template.
            stabilizer (Stabilizer): Stabilizer type, for verification.
            circuit (int): Measurement Circuit.
            name (str): Display name for the plaquette.
            overwrite (bool, optional): Overwrite existing plaquette. Defaults to False.

        Returns:
            Plaquette: A new Plaquette object.
        """
        tmp_plaquette = Plaquette(index, stabilizer, circuit, name)
        if index in self.plaquettes:
            if tmp_plaquette == self.plaquettes[index]:
                return self.plaquettes[index]
            if not overwrite:
                raise ValueError(
                    f"A different plaquette with index {index} already exists."
                )

        self.plaquettes[index] = tmp_plaquette
        return tmp_plaquette

    def get(self, index: int) -> Plaquette | None:
        """Get a Plaquette object by index.

        Args:
            index (int): The plaquette.

        Returns:
            Plaquette | None: The Plaquette object or None if not found.
        """
        return self.plaquettes.get(index, None)

    def delete(self, index: int) -> None:
        """Delete a Plaquette object by index.

        Args:
            index (int): The plaquette.
        """
        if index in self.plaquettes:
            del self.plaquettes[index]

    def clear(self) -> None:
        """Clear all Plaquette objects."""
        self.plaquettes = {}

    def __iter__(self) -> Iterable[Plaquette]:
        """Iterate over all Plaquette objects.

        Returns:
            Iterable[Plaquette]: An iterable of all Plaquette objects.
        """
        return iter(self.plaquettes.values())

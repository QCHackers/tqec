"""User-facing interface for plaquette operations."""
from .plaquettes import Plaquette, PlaquetteFactory, Stabilizer


class PlaquetteAPI:
    """Exposes the PlaquetteFactory to the user/userinterface."""

    _factory: PlaquetteFactory
    _id: int

    def __init__(self):
        self._factory = PlaquetteFactory()
        self._id = 0

    def add(self, stabilizer: Stabilizer, circuit: int, name: str) -> Plaquette:
        """Add a plaquette to the factory.

        Args:
            stabilizer (Stabilizer): Stabilizer type, for verification.
            circuit (int): Measurement Circuit.
            name (str): Display name for the plaquette.

        Returns:
            Plaquette: The newly created plaquette.
        """
        plaquette = self._factory.add(self._id, stabilizer, circuit, name)
        self._id += 1
        return plaquette

    def get(self, index: int) -> Plaquette | None:
        """Get a Plaquette object by index.

        Args:
            index (int): The plaquette.

        Returns:
            Plaquette | None: The Plaquette object or None if not found.
        """
        return self._factory.get(index)

    def delete(self, index: int) -> None:
        """Delete a Plaquette object by index.

        Args:
            index (int): The plaquette.
        """
        self._factory.delete(index)

    def clear(self) -> None:
        """Clear all Plaquette objects."""
        self._factory.clear()

    def all(self) -> list[Plaquette]:
        """Get all Plaquette objects.

        Returns:
            list[Plaquette]: A list of all Plaquette objects.
        """
        return list(self._factory.plaquettes.values())

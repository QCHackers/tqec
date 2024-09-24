from __future__ import annotations

import typing
from typing import Any, Sequence

import cirq
import stim

from tqec.circuit.operations.measurement import Measurement
from tqec.exceptions import TQECException

STIM_TAG = "STIM_OPERATION"


class ShiftCoords(cirq.Operation):
    def __init__(self, *shifts: int) -> None:
        """Annotates that the qubit/detector coordinate origin is being moved.

        This is a replication of the
        [stimcirq.ShiftCoordsAnnotation](https://github.com/quantumlib/Stim/blob/main/glue/cirq/stimcirq/_shift_coords_annotation.py)
        class. We can directly use `stimcirq.ShiftCoordsAnnotation` here, however,
        replication brings the class into the `tqec` namespace and is useful for the
        potential future iteration.

        Since the operation is not a real quantum operation, it does not have qubits
        and is not applied to any qubits. This might cause surprising behavior if you
        try to append or insert it into a circuit. It is always recommended to containerize
        this operation in a `cirq.Moment` before appending it to a circuit.

        In `tqec`, this kind of annotation operation should be tagged with the `cirq.VirtualTag`
        and the `STIM_TAG` to work correctly with the circuit transformation and the noise model.
        You can use the `make_shift_coords` helper function to create an instance of this class
        with the correct tags. Otherwise, you might need to manually tag the operation with the
        `cirq.VirtualTag` and the `STIM_TAG`.

        Warning:
            you should use `make_shift_coords` to create instances of this class.
            To understand how to use this class directly, please refer to the
            documentation above.

        Args:
            *shifts: How much to shift each coordinate.
        """
        # The number of shift coordinates should be between 1 and 16.
        # See [SHIFT_COORDS](https://github.com/quantumlib/Stim/blob/main/doc/gates.md#SHIFT_COORDS)
        if not 1 <= len(shifts) <= 16:
            raise TQECException(
                "The number of shift coordinates should be between 1 and 16, "
                f"but got {len(shifts)}."
            )

        self._shifts = shifts

    @property
    def shifts(self) -> tuple[int, ...]:
        """The shifts the operation represents."""
        return self._shifts

    @property
    def qubits(self) -> tuple[cirq.Qid, ...]:
        return ()

    def with_qubits(self, *new_qubits: cirq.Qid) -> ShiftCoords:
        return self

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}{self._shifts}"


class MeasurementsRecord(cirq.Operation):
    def __init__(self, measurement_data: Sequence[Measurement]) -> None:
        """A group of measurements.

        This class simply stores a list of :class:`~.Measurement` instances.
        Its purpose is to be used as a base to build operations that require
        a list of measurements.

        Args:
            measurement_data: a sequence of :class:`~.Measurement` that form
                a group. The exact meaning of this group (e.g., a detector or
                an observable) is not explicit and have to be provided by
                subclasses.
                There should be no duplicate in the provided sequence.

        Raises:
            TQECException: if there is any duplicate entry in the provided
                `measurement_data`.
        """
        # check there is no duplicate relative_measurement_data
        if len(set(measurement_data)) != len(measurement_data):
            raise TQECException(
                "The relative_measurement_data should not contain duplicate elements."
            )

        self._data = list(measurement_data)

    @property
    def qubits(self) -> tuple[cirq.Qid, ...]:
        return ()

    def with_qubits(self, *new_qubits: cirq.Qid) -> MeasurementsRecord:
        return self

    @property
    def measurement_data(self) -> list[Measurement]:
        """The recorded relative measurement data."""
        return self._data


class Detector(MeasurementsRecord):
    def __init__(
        self, measurement_data: Sequence[Measurement], coordinates: tuple[float, ...]
    ) -> None:
        """Operation representing a detector.

        Since the operation is not a real quantum operation, it does not have qubits
        and is not applied to any qubits. This might cause surprising behavior if you
        try to append or insert it into a circuit. It is always recommended to containerize
        this operation in a `cirq.Moment` before appending it to a circuit.

        In `tqec`, this kind of annotation operation should be tagged with the `cirq.VirtualTag`
        and the `STIM_TAG` to work correctly with the circuit transformation and the noise model.
        You can use the `make_detector` helper function to create an instance of this class
        with the correct tags. Otherwise, you might need to manually tag the operation with the
        `cirq.VirtualTag` and the `STIM_TAG`.

        Warning:
            you should use `make_detector` to create instances of this class.
            To understand how to use this class directly, please refer to the
            documentation above.

        Args:
            measurement_data: a sequence of :class:`~.Measurement` that form
                a group. There should be no duplicate in the provided sequence.
            coordinates: an annotation that will be forwarded to the DETECTOR Stim
                instruction.
        """

        super().__init__(measurement_data)
        self._coordinates = coordinates

    def _circuit_diagram_info_(self, _: Any) -> str:
        row, col, t = self.coordinates
        return f"Detector({row},{col},{t})"

    def __repr__(self) -> str:
        return (
            f"Detector(measurement_data={self._data}, coordinates={self._coordinates})"
        )

    @property
    def coordinates(self) -> tuple[float, ...]:
        return self._coordinates


class Observable(MeasurementsRecord):
    def __init__(
        self, measurement_data: Sequence[Measurement], observable_index: int = 0
    ) -> None:
        """Operation representing an observable.

        Since the operation is not a real quantum operation, it does not have qubits
        and is not applied to any qubits. This might cause surprising behavior if you
        try to append or insert it into a circuit. It is always recommended to containerize
        this operation in a `cirq.Moment` before appending it to a circuit.

        In `tqec`, this kind of annotation operation should be tagged with the `cirq.VirtualTag`
        and the `STIM_TAG` to work correctly with the circuit transformation and the noise model.
        You can use the `make_observable` helper function to create an instance of this class
        with the correct tags. Otherwise, you might need to manually tag the operation with the
        `cirq.VirtualTag` and the `STIM_TAG`.

        Warning:
            you should use `make_observable` to create instances of this class.
            To understand how to use this class directly, please refer to the
            documentation above.

        Args:
            measurement_data: a sequence of :class:`~.Measurement` that form
                a group. There should be no duplicate in the provided sequence.
            observable_index: index of the observable.
        """
        if observable_index < 0:
            raise TQECException(
                "The observable_index should be a non-negative integer, "
                f"but got {observable_index}."
            )

        super().__init__(measurement_data)
        self._observable_index = observable_index

    def _circuit_diagram_info_(self, _: cirq.CircuitDiagramInfoArgs) -> str:
        return f"Observable({self._observable_index})"

    @property
    def index(self) -> int:
        """Return the index of the observable."""
        return self._observable_index

    def __repr__(self) -> str:
        return f"Observable(measurement_data={self._data}, observable_index={self._observable_index})"


def make_shift_coords(*shifts: int) -> cirq.Operation:
    """This is a helper function to make a :class:~ShiftCoords operation with
    the `cirq.VirtualTag` tag.

    Args:
        *shifts: How much to shift each coordinate.

    Returns:
        A :class:`ShiftCoords` operation with the `cirq.VirtualTag` tag.
    """
    return ShiftCoords(*shifts).with_tags(cirq.VirtualTag(), STIM_TAG)


def make_detector(
    measurements: Sequence[Measurement], coordinates: tuple[float, ...]
) -> cirq.Operation:
    """This is a helper function to make a :class:`Detector` operation with the
    `cirq.VirtualTag` tag.

    Args:
        measurements: a list of measurements that compose the parity check of
            the detector.
        coordinates: an annotation that will be forwarded to the DETECTOR Stim
            instruction.

    Returns:
        A :class:`Detector` operation with the `cirq.VirtualTag` tag.
    """
    if coordinates[-1] < 0:
        raise TQECException(
            "The last coordinate should represent the time coordinate "
            f"and cannot be negative. Got {coordinates[-1]}."
        )
    return Detector(measurements, coordinates).with_tags(cirq.VirtualTag(), STIM_TAG)


def make_observable(
    measurements: Sequence[Measurement], observable_index: int = 0
) -> cirq.Operation:
    """This is a helper function to make a :class:`Observable` operation with
    the `cirq.VirtualTag` tag.

    Args:
        relative_measurements: a list of measurements that compose the
            parity check of the observable.
        observable_index: index of the observable.

    Returns:
        A :class:`Observable` operation with the `cirq.VirtualTag` tag.
    """

    return Observable(measurements, observable_index).with_tags(
        cirq.VirtualTag(), STIM_TAG
    )


@cirq.value_equality
class RX(cirq.Operation):
    """Reset in the X-basis."""

    def __init__(self, *qubits: cirq.Qid) -> None:
        """Create the X-reset operation.

        Args:
            qubits: the qubits that should be reset by the operation.
        """
        self._qubits = tuple(qubits)

    @property
    def qubits(self) -> tuple[cirq.Qid, ...]:
        return self._qubits

    def with_qubits(self, *new_qubits: cirq.Qid) -> RX:
        return RX(*new_qubits)

    def _value_equality_values_(self) -> tuple[cirq.Qid, ...]:
        return self._qubits

    def _circuit_diagram_info_(self, args: Any) -> str:
        k = ",".join(repr(e) for e in self.qubits)
        return f"RX {k}"

    @staticmethod
    def _json_namespace_() -> str:
        return ""

    def _json_dict_(self) -> dict[str, Any]:
        return {"qubits": self.qubits}

    def __repr__(self) -> str:
        return f"tqec.circuit.operations.operation.RX({self.qubits!r})"

    def _decompose_(self) -> list[Any]:
        return []

    def _is_comment_(self) -> bool:
        return False

    def _stim_conversion_(
        self,
        edit_circuit: stim.Circuit,
        edit_measurement_key_lengths: list[tuple[str, int]],
        targets: list[int],
        **kwargs: dict[str, typing.Any],
    ) -> None:
        edit_circuit.append("RX", targets, [])


@cirq.value_equality
class MX(cirq.Operation):
    """Measurement in the X-basis."""

    def __init__(self, *qubits: cirq.Qid) -> None:
        """Create the X-measurement operation.

        Args:
            qubits: the qubits that should be measured by the operation.
        """
        self._qubits = tuple(qubits)

    @property
    def qubits(self) -> tuple[cirq.Qid, ...]:
        return self._qubits

    def with_qubits(self, *new_qubits: cirq.Qid) -> MX:
        return MX(*new_qubits)

    def _value_equality_values_(self) -> Any:
        return self._qubits

    def _circuit_diagram_info_(self, args: Any) -> str:
        k = ",".join(repr(e) for e in self.qubits)
        return f"MX {k}"

    @staticmethod
    def _json_namespace_() -> str:
        return ""

    def _json_dict_(self) -> dict[str, Any]:
        return {"qubits": self.qubits}

    def __repr__(self) -> str:
        return f"tqec.circuit.operations.operation.MX({self.qubits!r})"

    def _decompose_(self) -> list[Any]:
        return []

    def _is_comment_(self) -> bool:
        return False

    def _stim_conversion_(
        self,
        edit_circuit: stim.Circuit,
        edit_measurement_key_lengths: list[tuple[str, int]],
        targets: list[int],
        **kwargs: dict[str, typing.Any],
    ) -> None:
        edit_measurement_key_lengths.append((",".join(map(str, targets)), len(targets)))
        edit_circuit.append_operation("MX", targets, [])

    def _is_measurement_(self) -> bool:
        return True

from typing import Any
from dataclasses import dataclass

import cirq

STIM_TAG = "STIM_OPERATION"


class ShiftCoords(cirq.Operation):
    def __init__(self, *shifts: int) -> None:
        """
        Annotates that the qubit/detector coordinate origin is being moved.

        This is a replication of the 
        [stimcirq.ShiftCoordsAnnotation](https://github.com/quantumlib/Stim/blob/main/glue/cirq/stimcirq/_shift_coords_annotation.py)
        class. We can directly use `stimcirq.ShiftCoordsAnnotation` here, however,
        replication brings the class into the `tqec` namespace and is useful for the
        potential future iteration.

        :param shifts: How much to shift each coordinate.
        """
        self._shifts = shifts

    @property
    def shifts(self) -> tuple[int, ...]:
        """The shifts the operation represents."""
        return self._shifts

    @property
    def qubits(self) -> tuple['cirq.Qid', ...]:
        return ()

    def with_qubits(self, *new_qubits: 'cirq.Qid') -> "ShiftCoords":
        return self


@dataclass(frozen=True)
class RelativeMeasurementData:
    """The data of a spatially and temporally relative measurement

    This class stores two attributes (relative_qubit_positioning and
    relative_measurement_offset) that respectively represent a spatial
    offset (a **relative** positioning with respect to some origin) and
    a temporal offset (with respect to a given Moment index).

    This relative information will be analysed by the fill_in_global_record_indices
    transformer and replaced by real qubit and global measurement records.

    Attributes:
        relative_qubit_positioning: The qubit coordinate offset. This will be added to a
            qubit coordinate system origin to obtain the actual qubit the measurement
            has been performed on.
        relative_measurement_offset: The relative measurement offset. The measurements
            performed on the qubit specified bt the relative_qubit_positioning will be
            accessed using this offset. For example, a value of -1 means the last
            measurement performed on the qubit till the time of the current operation.
    """

    relative_qubit_positioning: cirq.GridQubit
    relative_measurement_offset: int


class RelativeMeasurementsRecord(cirq.Operation):
    def __init__(
        self,
        local_coordinate_system_origin: cirq.GridQubit,
        data: list[RelativeMeasurementData],
    ) -> None:
        """A group of relative measurement data representing measurements relative
        to the origin of local coordinate system and current measurement timestamp.

        :param local_coordinate_system_origin: origin of the local coordinate system. 
            The origin along with the local coordinate system will be pinned to the 
            global coordinate system to resolve the actual qubit coordinates the 
            measurements applied to.
        :param data: a list of :class:`RelativeMeasurementData` that composed the
            relative measurements' operation.
        """
        self._local_coordinate_system_origin = local_coordinate_system_origin
        self._data = data

    @property
    def qubits(self) -> tuple['cirq.Qid', ...]:
        return ()

    def with_qubits(self, *new_qubits: 'cirq.Qid') -> "RelativeMeasurementsRecord":
        return self

    @property
    def data(self) -> list[RelativeMeasurementData]:
        """The recorded relative measurement data."""
        return self._data

    @property
    def origin(self) -> cirq.GridQubit:
        """The origin of the local coordinate system."""
        return self._local_coordinate_system_origin

    @origin.setter
    def origin(self, new_origin: cirq.GridQubit):
        """The origin of the local coordinate system."""
        self._local_coordinate_system_origin = new_origin


class Detector(RelativeMeasurementsRecord):
    def __init__(
        self,
        local_coordinate_system_origin: cirq.GridQubit,
        data: list[RelativeMeasurementData],
        time_coordinate: int = 0,
    ) -> None:
        """Operation representing a detector.

        :param local_coordinate_system_origin: origin of the local coordinate system.
            The origin along with the local coordinate system will be pinned to the
            global coordinate system to resolve the actual qubit coordinates the
            measurements applied to.
        :param data: a list of :class:`RelativeMeasurementData` that composed the
            relative measurements' operation.
        :param time_coordinate: an annotation that will be forwarded to the DETECTOR
            Stim structure as the last coordinate.
        """
        super().__init__(local_coordinate_system_origin, data)
        self._time_coordinate = time_coordinate

    def _circuit_diagram_info_(self, _: Any) -> str:
        row, col, t = self.coordinates
        return f"Detector({row},{col},{t})"

    @property
    def coordinates(self) -> tuple[int, ...]:
        return (
            self.origin.row,
            self.origin.col,
            self._time_coordinate,
        )


class Observable(RelativeMeasurementsRecord):
    def __init__(
        self,
        local_coordinate_system_origin: cirq.GridQubit,
        data: list[RelativeMeasurementData],
        observable_index: int = 0,
    ) -> None:
        """Operation representing an observable.

        :param local_coordinate_system_origin: origin of the local coordinate system.
            The origin along with the local coordinate system will be pinned to the
            global coordinate system to resolve the actual qubit coordinates the
            measurements applied to.
        :param data: a list of :class:`RelativeMeasurementData` that composed the
            relative measurements' operation.
        :param observable_index: the index of the observable.
        """
        super().__init__(local_coordinate_system_origin, data)
        self._observable_index = observable_index

    def _circuit_diagram_info_(self, _: cirq.CircuitDiagramInfoArgs):
        return f"Observable({self._observable_index})"

    @property
    def index(self) -> int:
        """Return the index of the observable."""
        return self._observable_index


def make_shift_coords(*shifts: int) -> cirq.Operation:
    """This is a helper function to make a :class:~ShiftCoords operation with the
    `cirq.VirtualTag` tag.

    :param shifts: How much to shift each coordinate.

    :return: A :class:`ShiftCoords` operation with the `cirq.VirtualTag` tag.
    """
    return ShiftCoords(*shifts).with_tags(cirq.VirtualTag(), STIM_TAG)


def make_detector(
        local_coordinate_system_origin: cirq.GridQubit,
        relative_measurements: list[tuple[cirq.GridQubit, int] | RelativeMeasurementData],
        time_coordinate: int = 0,
) -> cirq.Operation:
    """This is a helper function to make a :class:`Detector` operation with the
    `cirq.VirtualTag` tag.

    :param local_coordinate_system_origin: origin of the local coordinate system.
        The origin along with the local coordinate system will be pinned to the
        global coordinate system to resolve the actual qubit coordinates the
        measurements applied to.
    :param relative_measurements: a list of relative measurements that compose the
        parity check of the detector. Each element of the list is a tuple of
        (relative_qubit_position, relative_measurement_offset) or a :class:`RelativeMeasurementData`
        instance. When a tuple is provided, the first element is the position of
        the qubit relative to the local coordinate system origin and the second element
        is the relative measurement offset with respect to the most recent measurement
        performed on the qubit.
    :param time_coordinate: an annotation that will be forwarded to the DETECTOR
        Stim structure as the last coordinate.

    :return: A :class:`Detector` operation with the `cirq.VirtualTag` tag.
    """
    relative_measurements_data = [
        RelativeMeasurementData(*rm) if not isinstance(rm, RelativeMeasurementData) else rm
        for rm in relative_measurements
    ]
    return Detector(
        local_coordinate_system_origin,
        relative_measurements_data,
        time_coordinate
    ).with_tags(cirq.VirtualTag(), STIM_TAG)


def make_observable(
        local_coordinate_system_origin: cirq.GridQubit,
        relative_measurements: list[tuple[cirq.GridQubit, int] | RelativeMeasurementData],
        observable_index: int = 0,
) -> cirq.Operation:
    """This is a helper function to make a :class:`Observable` operation with the
    `cirq.VirtualTag` tag.

    :param local_coordinate_system_origin: origin of the local coordinate system.
        The origin along with the local coordinate system will be pinned to the
        global coordinate system to resolve the actual qubit coordinates the
        measurements applied to.
    :param relative_measurements: a list of relative measurements that composed the
        parity check of the observable. Each element of the list is a tuple of
        (relative_qubit_position, relative_measurement_offset) or a :class:`RelativeMeasurementData`
        instance. When a tuple is provided, the first element is the position of
        the qubit relative to a local coordinate system origin and the second element
        is the relative measurement offset with respect to the most recent measurement
        performed on the qubit.
    :param observable_index: the index of the observable.

    :return: A :class:`Observable` operation with the `cirq.VirtualTag` tag.
    """
    relative_measurements_data = [
        RelativeMeasurementData(*rm) if not isinstance(rm, RelativeMeasurementData) else rm
        for rm in relative_measurements
    ]
    return Observable(
        local_coordinate_system_origin,
        relative_measurements_data,
        observable_index
    ).with_tags(cirq.VirtualTag(), STIM_TAG)

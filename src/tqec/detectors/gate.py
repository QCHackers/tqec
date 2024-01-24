from copy import deepcopy
from dataclasses import dataclass

import cirq
import stim

from tqec.detectors.measurement_map import CircuitMeasurementMap


class ShiftCoordsGate(cirq.Gate):
    def __init__(self, *args: int) -> None:
        """A virtual gate exporting to the SHIFT_COORDS stim instruction

        This gate does not have any effect on the quantum state of the qubit it is
        applied on. It is entirely transparent, and as such can be considered an annotation
        more than a gate.
        The stimcirq approach of directly representing these as cirq.Operation instances (see
        https://github.com/quantumlib/Stim/blob/main/glue/cirq/stimcirq/_shift_coords_annotation.py)
        might be better, this will be something to think about in the future.

        :param args: the coordinates to shift by.
        """
        self._args = args

    def _num_qubits_(self):
        # Set to 1 to avoid any issue with a 0-qubit "gate".
        return 1

    def on(self, *qubits: cirq.Qid) -> cirq.Operation:
        # Add the virtual tag to explicitely mark this gate as "not a real gate"
        return super().on(*qubits).with_tags(cirq.VirtualTag())

    def _circuit_diagram_info_(self, _: cirq.CircuitDiagramInfoArgs):
        targets = ",".join(map(str, self._args))
        return f"SC({targets})"

    def _stim_conversion_(
        self,
        # The stim circuit being built. Add onto it.
        edit_circuit: stim.Circuit,
        # Metadata about measurement groupings needed by stimcirq.StimSampler.
        # If your gate contains a measurement, it has to append how many qubits
        # that measurement measures (and its key) into this list.
        edit_measurement_key_lengths: list[tuple[str, int]],
        # The indices of qubits the gate is operating on.
        targets: list[int],
        # Forward compatibility with future arguments.
        **_,
    ):
        edit_circuit.append("SHIFT_COORDS", [], self._args)


@dataclass
class RelativeMeasurement:
    """A spatially and temporally relative measurement

    This class stores two attributes (relative_qubit_positioning and
    relative_measurement_offset) that repectively represent a spatial
    offset (a **relative** positioning with respect to some origin) and
    a temporal offset (with respect to a given Moment index).

    This class will be analysed and replaced by the fill_in_global_record_indices
    transformer.
    """

    relative_qubit_positioning: cirq.GridQubit
    relative_measurement_offset: int


class RelativeMeasurementGate(cirq.Gate):
    def __init__(
        self,
        qubit_coordinate_system_origin: cirq.GridQubit,
        relative_measurements_loopback_offsets: list[RelativeMeasurement],
    ) -> None:
        """Gate representing a Stim instruction with relative measurements as targets.

        Issue with this class: cirq expectations for a subclass of cirq.Gate is the following (from cirq
        documentation https://quantumai.google/cirq/build/gates):

        > A Gate is an effect that can be applied to a collection of qubits (objects with a Qid).
        > Gates can be applied to qubits by calling their on method, or, alternatively calling the gate
        > on the qubits. The object created by such calls is an Operation. Alternatively, a Gate can be
        > thought of as a factory that, given input qubits, generates an associated GateOperation object.

        I understand that as "cirq.Gate instances should not have any qubit-specific knowledge as this is the
        role of the cirq.Operation class".
        And this is fine in theory as a RelativeMeasurementGate should only store offsets from the origin qubit
        (origin qubit that should be provided with the "on" method to create an instance of cirq.Operation).

        Resolving measurement offsets could be done inside the _stim_conversion_ method thanks to:
        - the fact that qubit coordinates can be recovered with stim.Circuit.get_final_qubit_coordinates,
        - the fact that detectors only reference past measurements, already in the stim.Circuit instance.

        But the second point above is not always true: if a repetition is found (i.e., stim.CircuitRepeatBlock),
        the stim.Circuit instance given to the _stim_conversion_ method is bounded to the stim.Circuit instance
        in the stim.CircuitRepeatBlock and has no way of accessing the parent stim.Circuit instance.
        This makes impossible to reliably compute measurement offsets, **even by considering that the measurement
        schedule in the repeat-block is consistent with the one just before the repeat block** (as we would need
        to account for measurements that are not yet in the repeated stim.Circuit instance, that is currently
        being built).
        One solution to that would be to give access to parent(s) stim.Circuit instances, that should be doable
        but requires a change directly in Stim.

        :param qubit_coordinate_system_origin: origin of the qubit coordinate system. Used to move instances of
            this Gate along with plaquettes.
        :param measurements_loopback_offsets: a list of measurements that are part of the gate. The
            measurements are given as a tuple with the following entries:

            1. a qubit offset, that is considered relative to the qubit this gate will be applied on, and that
               represent the qubit the measurement we want to access has been performed on,
            2. a **local**, **negative** offset, representing the n-th measurement on the qubit given in the
               first entry of the tuple, going backward **from the predecessor of the Moment containing this
               gate** (this is where the **local** comes from).

            The tuple [cirq.GridQubit(1, 1), -1] means the last measurement that is:
            1. located before the Moment this gate is in, and
            2. applied on the qubit "origin + cirq.GridQubit(1, 1)", where "origin" is the qubit given to
               the "on" method to construct an operation.
        """
        self._qubit_coordinate_system_origin = qubit_coordinate_system_origin
        self._local_measurements_loopback_offsets_relative_to_origin = (
            relative_measurements_loopback_offsets
        )
        self._global_measurements_loopback_offsets: list[int] = []
        super().__init__()

    def __deepcopy__(self, memo: dict) -> "RelativeMeasurementGate":
        return RelativeMeasurementGate(
            deepcopy(self._qubit_coordinate_system_origin, memo=memo),
            deepcopy(
                self._local_measurements_loopback_offsets_relative_to_origin, memo=memo
            ),
        )

    def __copy__(self) -> "RelativeMeasurementGate":
        # Force the deepcopy to avoid any issue from shared reference. This is a safety measure to mitigate
        # potential issues caused by the fact that this class does not follow the spirit of cirq.Gate interface.
        return self.__deepcopy__({})

    def _num_qubits_(self):
        return 1

    def on(self, *qubits: cirq.Qid, add_virtual_tag: bool = True) -> cirq.Operation:
        assert len(qubits) == 1, (
            f"Cannot apply a {self.__class__.__name__} to more than "
            f"1 qubits ({len(qubits)} qubits given)."
        )
        assert isinstance(qubits[0], cirq.GridQubit), "Expecting a GridQubit instance."
        self._set_origin(qubits[0])
        # Add the virtual tag to explicitely mark this gate as "not a real gate"
        tag = [cirq.VirtualTag()] if add_virtual_tag else []
        return super().on(*qubits).with_tags(*tag)

    def _set_origin(self, new_origin: cirq.GridQubit) -> None:
        self._qubit_coordinate_system_origin = new_origin

    def compute_global_measurements_loopback_offsets(
        self,
        measurement_map: CircuitMeasurementMap,
        current_moment_index: int,
    ) -> None:
        """Computes, from the data in the given measurement_map, the global measurement offsets

        This method uses the global data computed in the CircuitMeasurementMap instance given as
        parameter to compute the measurement record indices for the current gate instance.

        :param measurement_map: global measurement data obtained from the complete quantum circuit.
        :param current_moment_index: index of the moment this gate instance is found in. Used to
            recover the correct data from the given measurement_map.
        """
        self._global_measurements_loopback_offsets.clear()
        for (
            relative_measurement
        ) in self._local_measurements_loopback_offsets_relative_to_origin:
            # Coordinate system: adding 2 GridQubit instances together, both are using the GridQubit
            #                    coordinate system, so no issue here.
            qubit = (
                self._qubit_coordinate_system_origin
                + relative_measurement.relative_qubit_positioning
            )
            self._global_measurements_loopback_offsets.append(
                measurement_map.get_measurement_relative_offset(
                    current_moment_index,
                    qubit,
                    relative_measurement.relative_measurement_offset,
                )
            )


class DetectorGate(RelativeMeasurementGate):
    def __init__(
        self,
        qubit_coordinate_system_origin: cirq.GridQubit,
        measurements_loopback_offsets: list[RelativeMeasurement],
        time_coordinate: int = 0,
    ) -> None:
        """Gate representing a detector.

        Issue with this class: see RelativeMeasurementGate docstring.

        :param qubit_coordinate_system_origin: origin of the qubit coordinate system. Used to move detectors
            along with measurement gates.
        :param measurements_loopback_offsets: a list of measurements that are part of the detector. The
            measurements are given as a tuple with the following entries:

            1. a qubit offset, that is considered relative to the qubit this gate will be applied on, and that
               represent the qubit the measurement we want to access has been performed on,
            2. a **local**, **negative** offset, representing the n-th measurement on the qubit given in the
               first entry of the tuple, going backward **from the predecessor of the Moment containing this
               gate** (this is where the **local** comes from).

            The tuple [cirq.GridQubit(1, 1), -1] means the last measurement that is:
            1. located before the Moment this gate is in, and
            2. applied on the qubit "origin + cirq.GridQubit(1, 1)", where "origin" is the qubit given to
               the "on" method to construct an operation.
        :param time_coordinate: an annotation that will be forwarded to the DETECTOR Stim structure as the
            last coordinate.
        """
        super().__init__(qubit_coordinate_system_origin, measurements_loopback_offsets)
        self._time_coordinate = time_coordinate

    def __deepcopy__(self, memo: dict) -> "DetectorGate":
        return DetectorGate(
            deepcopy(self._qubit_coordinate_system_origin, memo=memo),
            deepcopy(self._local_measurements_loopback_offsets_relative_to_origin),
            self._time_coordinate,
        )

    def __copy__(self) -> "DetectorGate":
        # Force the deepcopy to avoid any issue from shared reference. This is a safety measure to mitigate
        # potential issues caused by the fact that this class does not follow the spirit of cirq.Gate interface.
        return self.__deepcopy__({})

    def _circuit_diagram_info_(self, _: cirq.CircuitDiagramInfoArgs):
        return "D"

    @property
    def coordinates(self) -> tuple[int, ...]:
        return (
            self._qubit_coordinate_system_origin.row,
            self._qubit_coordinate_system_origin.col,
            self._time_coordinate,
        )

    def _stim_conversion_(
        self,
        # The stim circuit being built. Add onto it.
        edit_circuit: stim.Circuit,
        # Metadata about measurement groupings needed by stimcirq.StimSampler.
        # If your gate contains a measurement, it has to append how many qubits
        # that measurement measures (and its key) into this list.
        edit_measurement_key_lengths: list[tuple[str, int]],
        # The indices of qubits the gate is operating on.
        targets: list[int],
        # Forward compatibility with future arguments.
        **_,
    ):
        assert self._global_measurements_loopback_offsets, (
            "Global measurement loopback offsets have not been computed."
            " Please call compute_global_measurements_loopback_offsets."
        )
        edit_circuit.append(
            "DETECTOR",
            [stim.target_rec(i) for i in self._global_measurements_loopback_offsets],
            self.coordinates,
        )


class ObservableGate(RelativeMeasurementGate):
    def __init__(
        self,
        qubit_coordinate_system_origin: cirq.GridQubit,
        measurements_loopback_offsets: list[RelativeMeasurement],
        observable_index: int = 0,
    ) -> None:
        """Gate representing an observable.

        Issue with this class: see RelativeMeasurementGate docstring.

        Observables are, for the moment, represented as instances of RelativeMeasurementGate. This might
        be undesirable as observable are inherently global (to the whole QEC code) objects and not local
        to a given Plaquette and its neighbourhood.
        A future task will consist in replacing this local description of observables by a more appropriate,
        probably global, way of describing observables.

        :param qubit_coordinate_system_origin: origin of the qubit coordinate system. Used to move observables
            along with plaquettes.
        :param measurements_loopback_offsets: a list of measurements that are part of the observable. The
            measurements are given as a tuple with the following entries:

            1. a qubit offset, that is considered relative to the qubit this gate will be applied on, and that
               represent the qubit the measurement we want to access has been performed on,
            2. a **local**, **negative** offset, representing the n-th measurement on the qubit given in the
               first entry of the tuple, going backward **from the predecessor of the Moment containing this
               gate** (this is where the **local** comes from).

            The tuple [cirq.GridQubit(1, 1), -1] means the last measurement that is:
            1. located before the Moment this gate is in, and
            2. applied on the qubit "origin + cirq.GridQubit(1, 1)", where "origin" is the qubit given to
               the "on" method to construct an operation.
        """
        super().__init__(qubit_coordinate_system_origin, measurements_loopback_offsets)
        self._observable_index = observable_index

    def __deepcopy__(self, memo: dict) -> "ObservableGate":
        return ObservableGate(
            deepcopy(self._qubit_coordinate_system_origin, memo=memo),
            deepcopy(self._local_measurements_loopback_offsets_relative_to_origin),
            self._observable_index,
        )

    def __copy__(self) -> "ObservableGate":
        # Force the deepcopy to avoid any issue from shared reference. This is a safety measure to mitigate
        # potential issues caused by the fact that this class does not follow the spirit of cirq.Gate interface.
        return self.__deepcopy__({})

    def _circuit_diagram_info_(self, _: cirq.CircuitDiagramInfoArgs):
        return "O"

    @property
    def coordinates(self) -> tuple[int, ...]:
        return (self._observable_index,)

    def _stim_conversion_(
        self,
        # The stim circuit being built. Add onto it.
        edit_circuit: stim.Circuit,
        # Metadata about measurement groupings needed by stimcirq.StimSampler.
        # If your gate contains a measurement, it has to append how many qubits
        # that measurement measures (and its key) into this list.
        edit_measurement_key_lengths: list[tuple[str, int]],
        # The indices of qubits the gate is operating on.
        targets: list[int],
        # Forward compatibility with future arguments.
        **_,
    ):
        assert self._global_measurements_loopback_offsets, (
            "Global measurement loopback offsets have not been computed."
            " Please call compute_global_measurements_loopback_offsets."
        )
        edit_circuit.append(
            "OBSERVABLE_INCLUDE",
            [stim.target_rec(i) for i in self._global_measurements_loopback_offsets],
            self.coordinates,
        )

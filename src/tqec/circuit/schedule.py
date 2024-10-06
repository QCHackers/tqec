"""Defines the :class:`ScheduledCircuit` class.

This module is central to the `tqec` library because it implements one of the
most used class of the library: :class:`ScheduledCircuit`.

A :class:`ScheduledCircuit` is "simply" a `stim.Circuit` that have all its
moments (portions of computation between two `TICK` instructions) assigned to
a unique positive integer representing the time slice at which the moment should
be scheduled.

Alongside :class:`ScheduledCircuit`, this module defines:

- :class:`Schedule` that is a thin wrapper around `list[int]` to represent a
  schedule (a sorted list of non-duplicated positive integers).
- :func:`remove_duplicate_instructions` to remove some instructions appearing
  twice in a single moment (most of the time due to data qubit
  reset/measurements that are defined by each plaquette, even on qubits shared
  with other plaquettes, leading to duplicates).
- :func:`merge_scheduled_circuits` that merge several :class:`ScheduledCircuit`
  instances into one.
- :func:`relabel_circuits_qubit_indices` to prepare several
  :class:`ScheduledCircuit` before merging them. This function is called
  internally by :func:`merge_scheduled_circuits` but might be useful at other
  places and so is kept public.
"""

from __future__ import annotations

import bisect
import typing as ty
import warnings
from copy import deepcopy
from dataclasses import dataclass, field

import stim

from tqec.circuit.moment import Moment, iter_stim_circuit_without_repeat_by_moments
from tqec.circuit.qubit import GridQubit, get_final_qubits
from tqec.exceptions import TQECException, TQECWarning


class ScheduleException(TQECException):
    pass


@dataclass
class Schedule:
    """Thin wrapper around `list[int]` to represent a schedule.

    This class ensures that the list of integers provided is a valid
    schedule by checking that all entries are positive integers, that
    the list is sorted and that it does not contain any duplicate.
    """

    schedule: list[int] = field(default_factory=list)

    _INITIAL_SCHEDULE: ty.ClassVar[int] = 0

    def __post_init__(self) -> None:
        Schedule._check_schedule(self.schedule)

    @staticmethod
    def from_offsets(schedule_offsets: ty.Sequence[int]) -> Schedule:
        """Get a valid schedule from offsets.

        This method should be used to avoid any dependency on
        `Schedule._INITIAL_SCHEDULE` in user code.
        """
        return Schedule([Schedule._INITIAL_SCHEDULE + s for s in schedule_offsets])

    @staticmethod
    def _check_schedule(schedule: list[int]) -> None:
        # Check that the schedule is sorted and positive
        if schedule and (
            not all(schedule[i] < schedule[i + 1] for i in range(len(schedule) - 1))
            or schedule[0] < Schedule._INITIAL_SCHEDULE
        ):
            raise ScheduleException(
                f"The provided schedule {schedule} is not a sorted list of positive "
                "integers. You should only provide sorted schedules with positive "
                "entries."
            )

    def __len__(self) -> int:
        return len(self.schedule)

    def __getitem__(self, i: int) -> int:
        return self.schedule[i]

    def __iter__(self) -> ty.Iterator[int]:
        return iter(self.schedule)

    def insert(self, i: int, value: int) -> None:
        """Insert an integer to the schedule.

        If inserting the integer results in an invalid schedule, the schedule is
        brought back to its (valid) original state before calling this function
        and a `ScheduleException` is raised.

        Args:
            i: index at which the provided value should be inserted.
            value: value to insert.

        Raises:
            ScheduleException: if the inserted integer makes the schedule
                invalid.
        """
        self.schedule.insert(i, value)
        try:
            Schedule._check_schedule(self.schedule)
        except ScheduleException as e:
            self.schedule.pop(i)
            raise e

    def append(self, value: int) -> None:
        """Append an integer to the schedule.

        If appending the integer results in an invalid schedule, the schedule is
        brought back to its (valid) original state before calling this function
        and a `ScheduleException` is raised.

        Args:
            value: value to insert.

        Raises:
            ScheduleException: if the inserted integer makes the schedule
                invalid.
        """
        self.schedule.append(value)
        try:
            Schedule._check_schedule(self.schedule)
        except ScheduleException as e:
            self.schedule.pop(-1)
            raise e


class ScheduledCircuit:
    def __init__(
        self,
        moments: list[Moment],
        schedule: Schedule | list[int] | int,
        final_qubits: dict[int, GridQubit],
    ) -> None:
        """Represent a quantum circuit with scheduled moments.

        This class aims at representing a `stim.Circuit` instance that has all
        its moments scheduled, i.e., associated with a time slice.

        This class explicitly does not support `stim.CircuitRepeatBlock` (i.e.,
        `REPEAT` instruction). It will raise an exception if such an instruction is
        found.

        Args:
            moments: moments representing the computation that is scheduled.
            schedule: schedule of the provided `moments`. If an integer is
                provided, each moment of the provided `stim.Circuit` is
                scheduled sequentially, starting by the provided integer.
            final_qubits: a map from indices to qubits that is used to re-create
                `QUBIT_COORDS` instructions when generating a `stim.Circuit`.

        Raises:
            ScheduleError: if the provided schedule is invalid.
            TQECException: if the provided `circuit` contains at least one
                `stim.CircuitRepeatBlock` instance.
            TQECException: if the provided `circuit` contains at least one
                `QUBIT_COORDS` instruction after the first `TICK` instruction.
        """

        if isinstance(schedule, int):
            schedule = list(range(schedule, schedule + len(moments)))
        if isinstance(schedule, list):
            schedule = Schedule(schedule)

        if len(moments) != len(schedule):
            raise ScheduleException(
                "ScheduledCircuit expects all the provided moments to be scheduled. "
                f"Got {len(moments)} moments but {len(schedule)} schedules."
            )
        if any(m.contains_instruction("QUBIT_COORDS") for m in moments[1:]):
            raise ScheduleException(
                "ScheduledCircuit instance expects the input `stim.Circuit` to "
                "only contain QUBIT_COORDS instructions before the first TICK."
            )

        self._moments: list[Moment] = moments
        self._final_qubits: dict[int, GridQubit] = final_qubits
        self._schedule: Schedule = schedule

    @staticmethod
    def empty() -> ScheduledCircuit:
        return ScheduledCircuit([], Schedule(), {})

    @staticmethod
    def from_circuit(
        circuit: stim.Circuit, schedule: Schedule | list[int] | int = 0
    ) -> ScheduledCircuit:
        """Build a :class:`ScheduledCircuit` instance from a circuit and a
        schedule.

        Args:
            circuit: the instance of Circuit that is scheduled. Should not contain
                any instance of `stim.CircuitRepeatBlock`.
            schedule: a sorted list of positive integers or a positive integer. If a
                list is given, it should contain as many values as there are moments
                in the provided `stim.Circuit` instance. If an integer is provided,
                each moment of the provided `stim.Circuit` is scheduled sequentially,
                starting by the provided schedule.

        Raises:
            ScheduleError: if the provided schedule is invalid.
            TQECException: if the provided `circuit` contains at least one
                `stim.CircuitRepeatBlock` instance.
            TQECException: if the provided `circuit` contains at least one
                `QUBIT_COORDS` instruction after the first `TICK` instruction.
        """

        if isinstance(schedule, int):
            schedule = list(range(schedule, schedule + circuit.num_ticks + 1))
        if isinstance(schedule, list):
            schedule = Schedule(schedule)

        ScheduledCircuit._check_input_circuit(circuit)

        moments: list[Moment] = list(
            iter_stim_circuit_without_repeat_by_moments(
                circuit, collected_before_use=True
            )
        )
        if not moments:
            return ScheduledCircuit.empty()

        if any(m.contains_instruction("QUBIT_COORDS") for m in moments[1:]):
            raise ScheduleException(
                "ScheduledCircuit instance expects the input `stim.Circuit` to "
                "only contain QUBIT_COORDS instructions before the first TICK."
            )
        # Here, we know for sure that no qubit is (re)defined in another place
        # than the first moment, so we can directly get qubit coordinates from
        # that moment.
        final_qubits: dict[int, GridQubit] = get_final_qubits(moments[0].circuit)
        # And because we want the cleanest possible moments, we can remove the
        # `QUBIT_COORDS` instructions from the first moment.
        moments[0].remove_all_instructions_inplace(frozenset(["QUBIT_COORDS"]))
        return ScheduledCircuit(moments, schedule, final_qubits)

    @staticmethod
    def _check_input_circuit(circuit: stim.Circuit) -> None:
        # Ensure that the provided circuit does not contain any
        # `stim.CircuitRepeatBlock` instance.
        if any(isinstance(inst, stim.CircuitRepeatBlock) for inst in circuit):
            raise ScheduleException(
                "stim.CircuitRepeatBlock instances are not supported in "
                "a ScheduledCircuit instance."
            )

    @property
    def schedule(self) -> Schedule:
        return self._schedule

    def get_qubit_coords_definition_preamble(self) -> stim.Circuit:
        """Get a circuit with only `QUBIT_COORDS` instructions."""
        ret = stim.Circuit()
        for qi, qubit in sorted(self._final_qubits.items(), key=lambda t: t[0]):
            ret.append("QUBIT_COORDS", qi, (float(qubit.x), float(qubit.y)))
        return ret

    def get_circuit(self, include_qubit_coords: bool = True) -> stim.Circuit:
        """Build and return the `stim.Circuit` instance represented by self.

        Warning:
            The circuit is re-built at each call! Use that function wisely.

        Returns:
            `stim.Circuit` instance represented by self.
        """
        ret = stim.Circuit()
        if not self._moments:
            return ret

        # Appending the QUBIT_COORDS instructions first.
        if include_qubit_coords:
            ret += self.get_qubit_coords_definition_preamble()

        # Building the actual circuit.
        current_schedule: int = 0
        last_schedule: int = self._schedule[-1]
        for sched, moment in zip(self._schedule, self._moments):
            for _ in range(current_schedule, sched):
                ret.append("TICK", [], [])
                current_schedule += 1
            ret += moment.circuit
            if current_schedule != last_schedule:
                ret.append("TICK", [], [])
                current_schedule += 1
        return ret

    def get_repeated_circuit(
        self,
        repetitions: int,
        include_qubit_coords: bool = True,
        include_additional_tick_in_body: bool = True,
    ) -> stim.Circuit:
        """Build and return the `stim.Circuit` instance represented by self
        encapsulated in a `REPEAT` block.

        Warning:
            The circuit is re-built at each call! Use that function wisely.

        Warning:
            An extra `TICK` instruction is appended by default at the end of the
            body of the `REPEAT` block to mimic `stim` way of doing. You can
            control that behaviour with the `include_additional_tick_in_body`
            parameter.

        Args:
            repetitions: argument to the enclosing `REPEAT` block representing
                the number of repetitions that should be used in the returned
                circuit.
            include_qubit_coords: if `True`, `QUBIT_COORDS` instructions are
                inserted at the beginning of the returned circuit (before the
                `REPEAT` block).
            include_additional_tick_in_body: if `True`, an additional `TICK`
                instruction is appended to the **body** (i.e., the circuit
                inside the `REPEAT` block) of the returned circuit. This is the
                default behaviour as `stim` does that in its code and adding
                the `TICK` here makes more sense than after the `REPEAT` block.

        Returns:
            `stim.Circuit` instance represented by self encapsulated in a
            `REPEAT` block.
        """
        ret = stim.Circuit()
        # Appending the QUBIT_COORDS instructions first.
        if include_qubit_coords:
            ret += self.get_qubit_coords_definition_preamble()

        # Appending the repeated version of self
        body = self.get_circuit(include_qubit_coords=False)
        # A `TICK` instruction is appended before repeating the code block. This
        # is to mimic internal `stim` ways of doing.
        if include_additional_tick_in_body:
            body.append("TICK", [], [])
        repeated_instruction = stim.CircuitRepeatBlock(repetitions, body)
        ret.append(repeated_instruction)
        return ret

    def map_qubit_indices(
        self, qubit_index_map: dict[int, int], inplace: bool = False
    ) -> ScheduledCircuit:
        """Map the qubits **indices** the `ScheduledCircuit` instance is
        applied on.

        Note:
            This method differs from :meth:`ScheduledCircuit.map_to_qubits`
            because it changes the qubit indices, which requires to iterate the
            whole circuit and change every instruction target.

            This method should be used before combining several
            :class:`ScheduledCircuit` instances that are not aware of each
            other.

        Args:
            qubit_index_map: the map used to modify the qubit targets.
            inplace: if True, perform the modification in place and return self.
                Else, perform the modification in a copy and return the copy.
                Note that the runtime cost of this method should be the same
                independently of the value provided here.

        Returns:
            a modified instance of `ScheduledCircuit` (a copy if inplace is
            `True`, else `self`).
        """
        mapped_final_qubits = {
            qubit_index_map[qi]: q for qi, q in self._final_qubits.items()
        }
        mapped_moments: list[Moment] = []
        for moment in self._moments:
            mapped_moment_circuit = stim.Circuit()
            for instr in moment.instructions:
                mapped_targets: list[stim.GateTarget] = []
                for target in instr.targets_copy():
                    # Non qubit targets are left untouched.
                    if not target.is_qubit_target:
                        mapped_targets.append(target)
                        continue
                    # Qubit targets are mapped using `qubit_index_map`
                    target_qubit = ty.cast(int, target.qubit_value)
                    mapped_targets.append(
                        stim.GateTarget(qubit_index_map[target_qubit])
                        if not target.is_inverted_result_target
                        else stim.GateTarget(-qubit_index_map[target_qubit])
                    )
                mapped_moment_circuit.append(
                    instr.name, mapped_targets, instr.gate_args_copy()
                )
            mapped_moments.append(Moment(mapped_moment_circuit))
        if inplace:
            self._final_qubits = mapped_final_qubits
            self._moments = mapped_moments
            return self
        else:
            return ScheduledCircuit(mapped_moments, self._schedule, mapped_final_qubits)

    def map_to_qubits(
        self, qubit_map: dict[GridQubit, GridQubit], inplace: bool = False
    ) -> ScheduledCircuit:
        """Map the qubits the `ScheduledCircuit` instance is applied on.

        Note:
            This method only changes the `QUBIT_COORDS` instructions at the
            beginning of the circuit. As long as `inplace` is `True`, this
            method is very efficient. If `inplace` is `False`, the deep copy of
            `self` is the most costly part of this method.

        Args:
            qubit_map: the map used to modify the qubits.
            inplace: if True, perform the modification in place and return self.
                Else, perform the modification in a copy and return the copy.

        Returns:
            a modified instance of `ScheduledCircuit` (a copy if inplace is True,
            else self).
        """
        operand = self if inplace else deepcopy(self)
        operand._final_qubits = {
            qi: qubit_map[q] for qi, q in operand._final_qubits.items()
        }
        return operand

    def __copy__(self) -> ScheduledCircuit:
        return ScheduledCircuit(self._moments, self._schedule, self._final_qubits)

    def __deepcopy__(self, memo: dict[ty.Any, ty.Any]) -> ScheduledCircuit:
        return ScheduledCircuit(
            deepcopy(self._moments, memo=memo),
            deepcopy(self._schedule, memo=memo),
            deepcopy(self._final_qubits, memo=memo),
        )

    @property
    def scheduled_moments(self) -> ty.Iterator[tuple[int, Moment]]:
        """Yields `stim.Circuit` instances representing a moment with their
        computed schedule.

        This property yields all the scheduled moments.

        The yielded elements are sorted with respect to their schedule.
        """
        yield from zip(self._schedule, self._moments)

    @property
    def moments(self) -> ty.Iterator[Moment]:
        yield from self._moments

    @property
    def qubits(self) -> frozenset[GridQubit]:
        return frozenset(self._final_qubits.values())

    def _get_moment_index_by_schedule(self, schedule: int) -> int | None:
        """Get the index of the moment scheduled at the provided schedule.

        Args:
            schedule: the schedule at which the Moment instance should be returned.
                If the schedule is negative, it is considered as an index from
                the end. For example, -1 is the last schedule and -2 is the
                last schedule - 1 (which might not be the second to last schedule).

        Returns:
            the index of the Moment instance scheduled at the provided schedule.
            If no Moment instance is scheduled at the provided schedule, None is
            returned.

        Raises:
            TQECException: if the provided calculated schedule is negative.
        """
        if not self._schedule:
            return None

        schedule = self._schedule[-1] + 1 + schedule if schedule < 0 else schedule
        if schedule < 0:
            raise TQECException(
                "Trying to get the index of a Moment instance with a negative "
                f"schedule {schedule}."
            )
        moment_index = next(
            (i for i, sched in enumerate(self._schedule) if sched == schedule), None
        )
        return moment_index

    def moment_at_schedule(self, schedule: int) -> Moment:
        """Get the Moment instance scheduled at the provided schedule.

        Args:
            schedule: the schedule at which the Moment instance should be returned.
                If the schedule is negative, it is considered as an index from
                the end. For example, -1 is the last schedule and -2 is the
                last schedule - 1 (which might not be the second to last schedule).

        Raises:
            TQECException if no moment exist at the provided schedule.
        """
        moment_index = self._get_moment_index_by_schedule(schedule)
        if moment_index is None:
            raise TQECException(
                f"No Moment instance scheduled at the provided schedule {schedule}."
            )
        return self._moments[moment_index]

    def append_new_moment(self, moment: Moment) -> None:
        """Schedule the provided Moment instance at the end of the circuit. The
        new schedule will be the last schedule plus one.

        Args:
            moment: the moment to schedule.
        """
        # By default, we cannot assume that self._schedule contains an entry, so
        # we insert at the first moment.
        schedule = Schedule._INITIAL_SCHEDULE
        # If it turns out that we have at least one scheduled moment, then
        # insert just after.
        if self._schedule:
            schedule = self._schedule[-1] + 1
        self.add_to_schedule_index(schedule, moment)

    def add_to_schedule_index(self, schedule: int, moment: Moment) -> None:
        """Add the operations contained in the provided moment at the provided
        schedule.

        Args:
            schedule: schedule at which operations in `moment` should be added.
                If the schedule is negative, it is considered as an index from
                the end. For example, -1 is the last schedule and -2 is the
                last schedule - 1 (which might not be the second to last schedule).
            moment: operations that should be added.
        """
        moment_index = self._get_moment_index_by_schedule(schedule)
        if moment_index is None:
            # We have to insert a new schedule and a new Moment.
            insertion_index = bisect.bisect_left(self._schedule, schedule)
            self._schedule.insert(insertion_index, schedule)
            self._moments.insert(insertion_index, moment)
        else:
            # Else, the schedule already exists, in which case we just need to add the
            # operations to an existing moment. Note that this might fail if two
            # operations overlap.
            self._moments[moment_index] += moment

    @property
    def q2i(self) -> dict[GridQubit, int]:
        """Return the map from qubits used in `self` their index."""
        return {q: i for i, q in self._final_qubits.items()}

    def append_observable(
        self, index: int, targets: ty.Sequence[stim.GateTarget]
    ) -> None:
        """Append an `OBSERVABLE_INCLUDE` instruction to the last moment.

        Args:
            index: index of the observable to append measurement records to.
            targets: measurement records forming (part of) the observable.
        """
        if any(not t.is_measurement_record_target for t in targets):
            raise TQECException(
                "Cannot create an observable with targets that are not measurement "
                f"records. Got: {list(targets)}."
            )
        self._moments[-1].append("OBSERVABLE_INCLUDE", targets, [index])

    @property
    def num_measurements(self) -> int:
        return sum(m.num_measurements for m in self._moments)


class _ScheduledCircuits:
    def __init__(self, circuits: list[ScheduledCircuit]) -> None:
        """Represents a collection of :class`ScheduledCircuit` instances.

        This class aims at providing accessors for several instances of
        :class:`ScheduledCircuit`. It allows to iterate on gates globally, for
        all the managed instances of :class:`ScheduledCircuit`, and implement a
        few other accessor methods to help with the task of merging multiple
        :class`ScheduledCircuit` together.

        Args:
            circuits: the instances that should be managed. Note that the
                instances provided here do not have to be "compatible" with each
                other. In particular, the qubit indices of each circuit can
                overlap. Due to the computations that are needed internally to
                avoid overlapping indices (that will break the computation), the
                instances provided here are copied in the `__init__` method.
        """
        # We might need to remap qubits to avoid index collision on several
        # circuits.
        self._circuits, self._global_q2i = relabel_circuits_qubit_indices(circuits)
        self._iterators = [circuit.scheduled_moments for circuit in self._circuits]
        self._current_moments = [next(it, None) for it in self._iterators]

    def has_pending_moment(self) -> bool:
        """Checks if any of the managed instances has a pending moment.

        Any moment that has not been collected by using collect_moment
        is considered to be pending.
        """
        return any(self._has_pending_moment(i) for i in range(len(self._circuits)))

    def _has_pending_moment(self, index: int) -> bool:
        """Check if the managed instance at the given index has a pending
        operation."""
        return self._current_moments[index] is not None

    def _peek_scheduled_moment(self, index: int) -> tuple[int, Moment] | None:
        """Recover **without collecting** the pending operation for the
        instance at the given index."""
        return self._current_moments[index]

    def _pop_scheduled_moment(self, index: int) -> tuple[int, Moment]:
        """Recover and mark as collected the pending moment for the instance at
        the given index.

        Raises:
            AssertionError: if not self.has_pending_operation(index).
        """
        ret = self._current_moments[index]
        if ret is None:
            raise RuntimeError(
                "Trying to pop a Moment instance from a ScheduledCircuit with "
                "all its moments already collected."
            )
        self._current_moments[index] = next(self._iterators[index], None)
        return ret

    @property
    def number_of_circuits(self) -> int:
        return len(self._circuits)

    def collect_moments_at_minimum_schedule(self) -> tuple[int, list[Moment]]:
        """Collect all the moments that can be collected.

        This method collects and returns a list of all the moments that should
        be scheduled next.

        Returns:
            a list of :class:`Moment` instances that should be added next to
            the QEC circuit.
        """
        assert self.has_pending_moment()
        circuit_indices_organised_by_schedule: dict[int, list[int]] = dict()
        for circuit_index in range(self.number_of_circuits):
            if not self._has_pending_moment(circuit_index):
                continue
            schedule, _ = self._peek_scheduled_moment(circuit_index)  # type: ignore
            circuit_indices_organised_by_schedule.setdefault(schedule, list()).append(
                circuit_index
            )

        minimum_schedule = min(circuit_indices_organised_by_schedule.keys())
        moments_to_return: list[Moment] = list()
        for circuit_index in circuit_indices_organised_by_schedule[minimum_schedule]:
            _, moment = self._pop_scheduled_moment(circuit_index)
            moments_to_return.append(moment)
        return minimum_schedule, moments_to_return

    @property
    def q2i(self) -> dict[GridQubit, int]:
        return self._global_q2i


def _sort_target_groups(
    targets: ty.Iterable[list[stim.GateTarget]],
) -> list[list[stim.GateTarget]]:
    def _sort_key(target_group: ty.Iterable[stim.GateTarget]) -> tuple[int, ...]:
        return tuple(t.value for t in target_group)

    return sorted(targets, key=_sort_key)


def remove_duplicate_instructions(
    instructions: list[stim.CircuitInstruction],
    mergeable_instruction_names: frozenset[str],
) -> list[stim.CircuitInstruction]:
    """Removes all the duplicate instructions from the given list.

    Note:
        This function guarantees the following post-conditions on the returned
        results:

        - Instructions with a name that is not in `mergeable_instruction_names`
          are returned at the front of the returned list, in the same relative
          ordering as provided in `instructions` input.
        - Instructions with a name that is in `mergeable_instruction_names` will
          be returned after all the instructions with a name that does not
          appear in `mergeable_instruction_names`. The order in which these
          instructions are returned is not guaranteed and can change between
          executions.

    Warning:
        this function **does not keep instruction ordering**. It is intended to
        be used with input `instructions` that, once de-duplication has been
        applied, form a valid moment, which means that each instruction can be
        executed in parallel, and so their order in the returned list does not
        matter.

        If that is not your case, take extra care to the output of this
        function as it will likely introduce hard-to-debug issues. To prevent
        such potential misuse, this function checks for such cases and outputs
        a warning if it happens.

    Returns:
        a list containing a copy of the stim.CircuitInstruction instances from
        the given instructions but without any duplicate.
    """
    # Separate mergeable operations from non-mergeable ones.
    mergeable_operations: dict[
        tuple[str, tuple[float, ...]], set[tuple[stim.GateTarget, ...]]
    ] = {}
    final_operations: list[stim.CircuitInstruction] = list()
    for inst in instructions:
        if inst.name in mergeable_instruction_names:
            # Mergeable operations are automatically merged thanks to
            # the use of a set here.
            mergeable_operations.setdefault(
                (inst.name, tuple(inst.gate_args_copy())), set()
            ).update(tuple(group) for group in inst.target_groups())
        else:
            final_operations.append(inst)
    # Add the merged operations into the final ones
    final_operations.extend(
        stim.CircuitInstruction(
            name, sum(_sort_target_groups([list(t) for t in targets]), start=[]), args
        )
        for (name, args), targets in mergeable_operations.items()
    )
    # Warn if the output instructions do not form a valid moment, as this is
    # likely a misuse of this function.
    try:
        circuit = stim.Circuit()
        for instr in final_operations:
            circuit.append(instr)
        Moment.check_is_valid_moment(circuit)
    except TQECException:
        warnings.warn(
            "The instructions obtained at the end of the "
            "`remove_duplicate_instructions` function do not form a valid "
            "moment. You are likely misusing the function. Final instructions "
            "obtained and gathered into a single stim.Circuit: "
            f"\n{circuit}",
            TQECWarning,
        )
    return final_operations


_MERGEABLE_INSTRUCTION_NAMES = frozenset(
    ["M", "MR", "MRX", "MRY", "MRZ", "MX", "MY", "MZ", "R", "RX", "RY", "RZ"]
)


def merge_scheduled_circuits(circuits: list[ScheduledCircuit]) -> ScheduledCircuit:
    """Merge several ScheduledCircuit instances into one instance.

    This function takes several scheduled circuits as input and merge them,
    respecting their schedules, into a unique `ScheduledCircuit` instance that
    will then be returned to the caller.

    KeyError: if any of the provided circuit contains a qubit target that is
            not defined by a `QUBIT_COORDS` instruction.

    Returns:
        a circuit representing the merged scheduled circuits given as input.
    """
    scheduled_circuits = _ScheduledCircuits(circuits)

    all_moments: list[Moment] = []
    all_schedules = Schedule()
    global_i2q: dict[int, GridQubit] = {i: q for q, i in scheduled_circuits.q2i.items()}

    while scheduled_circuits.has_pending_moment():
        schedule, moments = scheduled_circuits.collect_moments_at_minimum_schedule()
        # Flatten the moments into a list of operations to perform some modifications
        instructions = sum((list(moment.instructions) for moment in moments), start=[])
        # Avoid duplicated operations. Any operation that have the Plaquette.get_mergeable_tag() tag
        # is considered mergeable, and can be removed if another operation in the list
        # is considered equal (and has the mergeable tag).
        deduplicated_instructions = remove_duplicate_instructions(
            instructions, mergeable_instruction_names=_MERGEABLE_INSTRUCTION_NAMES
        )
        circuit = stim.Circuit()
        for inst in deduplicated_instructions:
            circuit.append(
                inst.name,
                sum(_sort_target_groups(inst.target_groups()), start=[]),
                inst.gate_args_copy(),
            )
        all_moments.append(Moment(circuit))
        all_schedules.append(schedule)

    return ScheduledCircuit(all_moments, all_schedules, global_i2q)


def relabel_circuits_qubit_indices(
    circuits: ty.Sequence[ScheduledCircuit],
) -> tuple[list[ScheduledCircuit], dict[GridQubit, int]]:
    """Relabel the qubit indices of the provided circuits to avoid collision.

    When several :class:`ScheduledCircuit` are constructed without a global
    knowledge of all the qubits, qubit indices used by each instance likely
    overlap. This is an issue when we try to merge such circuits because one
    index might represent a different qubit depending on the circuit it is used
    in.

    This function takes a sequence of circuits and relabel their qubits to avoid
    such collisions.

    Warning:
        all the qubit targets used in each of the provided circuits should have
        a corresponding `QUBIT_COORDS([coordinates]) [qubit target]` for this
        function to work correctly. If that is not the case, a KeyError will be
        raised.

    Raises:
        KeyError: if any of the provided circuit contains a qubit target that is
            not defined by a `QUBIT_COORDS` instruction.

    Args:
        circuits: circuit instances to remap.

    Returns:
        the same circuits with update qubit indices as well as the global qubit
        indices map that has been used. Qubits in the returned global qubit map
        are assigned to an index such that:

        1. the sequence of indices is `range(0, len(qubit_map))`.
        2. the list `[qubit_map[q] for q in sorted(qubit_map)]` is exactly
           `list(range(len(qubit_map)))`.
    """
    # First, get a global qubit index map.
    needed_qubits = frozenset.union(*[c.qubits for c in circuits])
    global_q2i = {q: i for i, q in enumerate(sorted(needed_qubits))}
    # Then, get the remapped circuits. Note that map_qubit_indices should
    # have approximately the same runtime cost whatever the value of inplace
    # so we ask for a new instance to avoid keeping a reference to the given
    # circuits.
    relabeled_circuits: list[ScheduledCircuit] = []
    for circuit in circuits:
        local_indices_to_global_indices = {
            local_index: global_q2i[q] for q, local_index in circuit.q2i.items()
        }
        relabeled_circuits.append(
            circuit.map_qubit_indices(local_indices_to_global_indices, inplace=False)
        )
    return relabeled_circuits, global_q2i

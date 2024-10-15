"""Defines a class analogous to `cirq.Moment`

This module defines :class:`Moment` that is very close to the external
[`cirq.Moment`](https://quantumai.google/reference/python/cirq/Moment)
class.

Internally, :class:`Moment` stores the instructions using `stim.Circuit`
instead of using `cirq` data-structures.
"""

from __future__ import annotations

import typing as ty

import stim

from tqec.circuit.instructions import is_annotation_instruction
from tqec.circuit.qubit import count_qubit_accesses, get_used_qubit_indices
from tqec.exceptions import TQECException


class Moment:
    """A collection of instructions that can be executed in parallel.

    This class is a collection of `stim.CircuitInstruction` instances that
    can all be executed in parallel. That means that it maintains the following
    invariant:

    For each instruction contained in any instance of this class, exactly
    one of the following assertions is true:

    1. The instruction is an annotation (e.g., `QUBIT_COORDS`, `DETECTOR`, ...),
    2. It is the only instruction of the `Moment` instance to be applied
        on its targets. In other words, no other instructions in the `Moment`
        instance can be applied on the targets this instruction is applied to.

    In practice, that means that this class match closely the definition of
    [`cirq.Moment`](https://quantumai.google/reference/python/cirq/Moment).
    The only minor different is that `cirq` only uses the second assertion
    above (meaning that an annotation might push a quantum gate to the next
    moment, even though the annotation is never executed in hardware).
    """

    def __init__(self, circuit: stim.Circuit, copy_circuit: bool = False) -> None:
        Moment.check_is_valid_moment(circuit)
        self._circuit: stim.Circuit = circuit.copy() if copy_circuit else circuit
        self._used_qubits: set[int] = get_used_qubit_indices(self._circuit)

    @property
    def circuit(self) -> stim.Circuit:
        return self._circuit

    @staticmethod
    def check_is_valid_moment(circuit: stim.Circuit) -> None:
        if circuit.num_ticks > 0:
            raise TQECException(
                "Cannot initialize a Moment with a stim.Circuit instance "
                "containing at least one TICK instruction."
            )
        qubit_usage = count_qubit_accesses(circuit)
        if any(usage_count > 1 for usage_count in qubit_usage.values()):
            raise TQECException(
                "Moment instances cannot be initialized with a stim.Circuit "
                "instance containing gates applied on the same qubit."
            )
        if any(isinstance(inst, stim.CircuitRepeatBlock) for inst in circuit):
            raise TQECException(
                "Moment instances should no contain any instance "
                "of stim.CircuitRepeatBlock."
            )

    @property
    def qubits_indices(self) -> set[int]:
        """Return the qubit indices this moment operates on.

        Note:
            Some instructions are considered annotations (e.g., `QUBIT_COORDS`,
            see `tqec.circuit.qubit.NON_COMPUTATION_INSTRUCTIONS` for an
            exhaustive list). These instructions are ignored by this property,
            meaning that the qubits they operate on will only be returned by
            this property iff another non-annotation instruction is applied on
            said qubits.
        """
        return self._used_qubits

    def contains_instruction(self, instruction_name: str) -> bool:
        """Return `True` if `self` contains at least one operation with the
        provided name."""
        return any(instr.name == instruction_name for instr in self._circuit)

    def remove_all_instructions_inplace(
        self, instructions_to_remove: frozenset[str]
    ) -> None:
        """Remove in-place all the instructions that have their name in the
        provided `instructions_to_remove`."""
        new_circuit = stim.Circuit()
        for inst in self._circuit:
            if inst.name in instructions_to_remove:
                continue
            new_circuit.append(inst)
        self._circuit = new_circuit

    def __iadd__(self, other: Moment | stim.Circuit) -> Moment:
        """Add instructions in-place in `self`."""
        if isinstance(other, stim.Circuit):
            other = Moment(other, copy_circuit=False)
        both_sides_used_qubits = self._used_qubits.intersection(other._used_qubits)
        if both_sides_used_qubits:
            raise TQECException(
                "Trying to add an overlapping quantum circuit to a Moment instance."
            )
        self._circuit += other._circuit
        return self

    @staticmethod
    def _get_used_qubit_indices(
        targets: ty.Iterable[int | stim.GateTarget],
    ) -> list[int]:
        qubits: list[int] = []
        for target in targets:
            if isinstance(target, int):
                qubits.append(target)
                continue
            # isinstance(target, stim.GateTarget)
            if target.is_qubit_target:
                assert isinstance(target.qubit_value, int)  # type checker is happy
                qubits.append(target.qubit_value)
        return qubits

    def append(
        self,
        name_or_instr: str | stim.CircuitInstruction,
        targets: ty.Iterable[int | stim.GateTarget] | None = None,
        args: ty.Iterable[float] | None = None,
    ) -> None:
        """Append an instruction to the :class:`Moment`.

        Note:
            if you append an annotation (e.g., `DETECTOR` or `QUBIT_COORDS`) then
            you should use :meth:`append_annotation` that is more efficient.

        Args:
            name_or_instr: either the name of the instruction to append or the
                actual instruction. If the name is provided, `targets` and `args`
                are used to build the `stim.CircuitInstruction` instance that
                will be appended. Else, they are not accessed.
            targets: if `name_or_instr` is a string representing the instruction
                name, this argument represent the targets the instruction should
                be applied on. Else, it is not used.
            args: if `name_or_instr` is a string representing the instruction
                name, this argument represent the arguments the instruction
                should be applied with. Else, it is not used.
        """
        if targets is None:
            targets = tuple()
        if args is None:
            args = tuple()

        instruction: stim.CircuitInstruction
        if isinstance(name_or_instr, str):
            instruction = stim.CircuitInstruction(name_or_instr, targets, args)
        else:
            instruction = name_or_instr

        if is_annotation_instruction(instruction):
            self.append_annotation(instruction)
            return

        # Checking Moment invariant
        instruction_qubits = Moment._get_used_qubit_indices(
            targets if isinstance(name_or_instr, str) else name_or_instr.targets_copy()
        )
        overlapping_qubits = self._used_qubits.intersection(instruction_qubits)
        if overlapping_qubits:
            raise TQECException(
                f"Cannot add {instruction} to the Moment due to qubit(s) "
                f"{overlapping_qubits} being already in use."
            )
        self._used_qubits.update(instruction_qubits)
        self._circuit.append(instruction)

    def append_annotation(
        self, annotation_instruction: stim.CircuitInstruction
    ) -> None:
        """Append an annotation instruction to the Moment.

        This method is way more efficient than :meth:`append_instruction` to
        append an annotation. This is thanks to the fact that annotations are
        not using any qubit and so can be appended without checking that the
        instruction does not apply on already used qubits.

        Args:
            annotation_instruction: an annotation to append to the moment
                represented by `self`.

        Raises:
            TQECException: if `not is_annotation_instruction(annotation_instruction)`.
        """
        if not is_annotation_instruction(annotation_instruction):
            raise TQECException(
                "The method append_annotation only supports appending "
                f"annotations. Found instruction {annotation_instruction.name} "
                "That is not a valid annotation. Call append_instruction for "
                "generic instructions."
            )
        self._circuit.append(annotation_instruction)

    @property
    def instructions(self) -> ty.Iterator[stim.CircuitInstruction]:
        """Iterator over all the instructions contained in the moment."""
        # We can ignore the type error below because:
        # 1. if a Moment instance is created with a stim.CircuitRepeatBlock
        #    instance, it will raise an exception.
        # 2. `Moment.__iadd__` is the only method that may add an instance of
        #    stim.CircuitRepeatBlock, but it checks that the input circuit to be
        #    added does not contain such an instance (by creating a Moment from
        #    it).
        # So we know for sure that there are only `stim.CircuitInstruction`
        # instances.
        yield from self._circuit  # type: ignore

    def operates_on(self, qubits: ty.Sequence[int]) -> bool:
        """Returns `True` if `self` contains non-annotation operations that are
        applied on each of the provided qubit indices."""
        qindices = self.qubits_indices
        return all(q in qindices for q in qubits)

    @property
    def num_measurements(self) -> int:
        """Return the number of measurements in the :class:`Moment`
        instance."""
        # Mypy is showing an error here:
        # error: Returning Any from function declared to return "int"
        # I do not understand why, but it probably has to do with Stim typing
        # so let's ignore it for the moment.
        return self._circuit.num_measurements  # type: ignore

    def filter_by_qubits(self, qubits_to_keep: ty.Iterable[int]) -> Moment:
        """Return a new :class:`Moment` instance containing only the
        instructions that are applied on the provided qubits."""
        qubits = frozenset(qubits_to_keep)
        new_circuit = stim.Circuit()
        for instruction in self.instructions:
            targets: list[stim.GateTarget] = []
            for target_group in instruction.target_groups():
                qubit_targets = [
                    ty.cast(int, t.qubit_value)
                    for t in target_group
                    if t.is_qubit_target
                ]
                if any(q not in qubits for q in qubit_targets):
                    continue
                targets.extend(target_group)
            if targets:
                new_circuit.append(
                    instruction.name, targets, instruction.gate_args_copy()
                )
        return Moment(new_circuit)

    @property
    def is_empty(self) -> bool:
        """Return `True` if the :class:`Moment` instance is empty."""
        return len(self._circuit) == 0


def iter_stim_circuit_without_repeat_by_moments(
    circuit: stim.Circuit, collected_before_use: bool = True
) -> ty.Iterator[Moment]:
    """Iterate over the `stim.Circuit` by moments.

    A moment in a `stim.Circuit` is a sequence of instructions between two `TICK`
    instructions. Note that `stim.CircuitRepeatBlock` instances are explicitly not
    supported and no such instance should appear in the provided circuit.

    Args:
        circuit: circuit to iterate over. Should not contain any REPEAT block.
        collected_before_use: if `True`, the returned :class:`Moment` instances
            will contain a copy of the temporary `stim.Circuit` instance
            representing the moment. This is needed if the yielded
            :class:`Moment` instances are not used directly because the
            underlying `stim.Circuit` instance is cleared when resuming the
            generator.

    Yields:
        A `Moment` instance.

    Raises:
        TQECException: if the provided `circuit` contains at least one
            `stim.CircuitRepeatBlock` instance.
        TQECException: if the provided `circuit` `TICK` instructions are not
            inserted such that instructions between two `TICK` instructions
            are always applied on disjoint sets of qubits.
    """
    copy_func: ty.Callable[[stim.Circuit], stim.Circuit] = (
        (lambda c: c.copy()) if collected_before_use else (lambda c: c)
    )
    cur_moment = stim.Circuit()
    for inst in circuit:
        if isinstance(inst, stim.CircuitRepeatBlock):
            raise TQECException(
                "Found an instance of stim.CircuitRepeatBlock which is "
                "explicitly not supported by this method."
            )
        elif inst.name == "TICK":
            yield Moment(copy_func(cur_moment))
            cur_moment.clear()
        else:
            cur_moment.append(inst)
    if cur_moment:
        # No need to copy the last moment
        yield Moment(cur_moment)

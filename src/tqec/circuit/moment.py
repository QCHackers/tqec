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

from tqec.circuit.qubit import count_qubit_accesses, get_used_qubit_indices
from tqec.exceptions import TQECException


class Moment:
    """A collection of instructions that can be executed in parallel.

    This class is a collection of `stim.CircuitInstruction` instances that
    can all be executed in parallel. That means that it maintains the following
    invariant:

    For each instruction `I` contained in any instance of this class, exactly
    one of the following assertions is true:

    1. `I` is an annotation (e.g., `QUBIT_COORDS`, `DETECTOR`, ...),
    2. `I` is the only instruction of the `Moment` instance to be applied
        on its targets. In other words, no other gate in the `Moment`
        instance can be applied on the targets `I` is applied to.

    In practice, that means that this class match closely the definition of
    [`cirq.Moment`](https://quantumai.google/reference/python/cirq/Moment).
    The only minor different is that `cirq` only uses the second assertion
    above (meaning that an annotation might push a quantum gate to the next
    moment, even though the annotation is never executed in hardware).
    """

    def __init__(self, circuit: stim.Circuit, copy_circuit: bool = False) -> None:
        self._circuit: stim.Circuit = circuit.copy() if copy_circuit else circuit

    @property
    def circuit(self) -> stim.Circuit:
        return self._circuit

    def __post_init__(self) -> None:
        Moment.check_is_valid_moment(self._circuit)

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
    def qubits_indices(self) -> frozenset[int]:
        return get_used_qubit_indices(self._circuit)

    def contains_instruction(self, instruction_name: str) -> bool:
        return any(instr.name == instruction_name for instr in self._circuit)

    def remove_all_instructions_inplace(
        self, instructions_to_remove: frozenset[str]
    ) -> None:
        new_circuit = stim.Circuit()
        for inst in self._circuit:
            if inst.name in instructions_to_remove:
                continue
            new_circuit.append(inst)
        self._circuit = new_circuit

    def __iadd__(self, other: Moment | stim.Circuit) -> Moment:
        if isinstance(other, stim.Circuit):
            other = Moment(other)
        self_used_qubits = get_used_qubit_indices(self._circuit)
        other_used_qubits = get_used_qubit_indices(other._circuit)
        both_sides_used_qubits = self_used_qubits.intersection(other_used_qubits)
        if both_sides_used_qubits:
            raise TQECException(
                "Trying to add an overlapping quantum circuit to a Moment instance."
            )
        self._circuit += other._circuit
        return self

    def append(
        self,
        inst: str,
        targets: ty.Iterable[stim.GateTarget],
        arg: float | ty.Iterable[float],
    ) -> None:
        self_used_qubits = get_used_qubit_indices(self._circuit)
        instruction_used_qubits = frozenset(
            ty.cast(int, t.qubit_value) for t in targets if t.is_qubit_target
        )
        both_sides_used_qubits = self_used_qubits.intersection(instruction_used_qubits)
        if both_sides_used_qubits:
            raise TQECException(
                "Trying to add an overlapping instruction to a Moment instance."
            )
        self._circuit.append(inst, targets, arg)

    @property
    def instructions(self) -> ty.Iterator[stim.CircuitInstruction]:
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
        qindices = self.qubits_indices
        return all(q in qindices for q in qubits)

    @property
    def num_measurements(self) -> int:
        # Mypy is showing an error here:
        # error: Returning Any from function declared to return "int"
        # I do not understand why, but it probably has to do with Stim typing
        # so let's ignore it for the moment.
        return self._circuit.num_measurements  # type: ignore


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

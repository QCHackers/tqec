from __future__ import annotations

import dataclasses
from typing import Iterable

import numpy as np
import stim

from tqec.exceptions import TQECException

ANNOTATIONS = {
    "QUBIT_COORDS",
    "DETECTOR",
    "OBSERVABLE_INCLUDE",
    "SHIFT_COORDS",
    "TICK",
}


class PauliString:
    def __init__(self, qubits2pauli: dict[int, str]):
        """A mapping from qubits to Pauli operators that represent a Pauli string.

        Args:
            qubits2pauli: A dictionary mapping qubit indices to Pauli operators. The
                Pauli operators should be one of "I", "X", "Y", or "Z".
        """
        for qubit, pauli in qubits2pauli.items():
            if pauli not in "IXYZ":
                raise TQECException(
                    f"Invalid Pauli operator {pauli} for qubit {qubit}, expected I, X, Y, or Z."
                )
        self.qubits = {q: qubits2pauli[q] for q in sorted(qubits2pauli.keys())}
        self._hash = hash(tuple(self.qubits.items()))

    @property
    def weight(self) -> int:
        return len([p for p in self.qubits.values() if p != "I"])

    @staticmethod
    def from_stim_pauli_string(
        stim_pauli_string: stim.PauliString,
        ignore_identity: bool = True,
    ) -> "PauliString":
        """Convert a `stim.PauliString` to a `PauliString` instance, ignoring the sign."""
        if ignore_identity:
            return PauliString(
                {
                    q: "IXYZ"[stim_pauli_string[q]]
                    for q in range(len(stim_pauli_string))
                    if stim_pauli_string[q]
                }
            )
        return PauliString(
            {
                q: "IXYZ"[stim_pauli_string[q]]
                for q in range(len(stim_pauli_string))
            }
        )

    def to_stim_pauli_string(self, length: int | None) -> stim.PauliString:
        """Convert a `PauliString` to a `stim.PauliString` instance.

        Args:
            length: The length of the `stim.PauliString`. If `None`, the length is set to the
                maximum qubit index in the `PauliString` plus one.
        """
        max_qubit_index = max(self.qubits.keys())
        length = length or max_qubit_index + 1
        if length <= max_qubit_index:
            raise TQECException(
                f"The length specified {length} <= the maximum qubit index {max_qubit_index} in the pauli string."
            )
        stim_pauli_string = stim.PauliString(length)
        for q, p in self.qubits.items():
            stim_pauli_string[q] = p
        return stim_pauli_string

    def __bool__(self):
        return bool(self.qubits)

    def __mul__(self, other: "PauliString") -> "PauliString":
        result = {}
        for q in self.qubits.keys() | other.qubits.keys():
            a = self.qubits.get(q, "I")
            b = other.qubits.get(q, "I")
            ax = a in "XY"
            az = a in "YZ"
            bx = b in "XY"
            bz = b in "YZ"
            cx = ax ^ bx
            cz = az ^ bz
            c = "IXZY"[cx + cz * 2]
            result[q] = c
        return PauliString(result)

    def __repr__(self):
        return f"PauliString(qubits={self.qubits!r})"

    def __str__(self):
        return "*".join(f"{self.qubits[q]}{q}" for q in sorted(self.qubits.keys()))

    def __len__(self):
        return len(self.qubits)

    def commutes(self, other: "PauliString") -> bool:
        """Check if this Pauli string commutes with another Pauli string."""
        return not self.anticommutes(other)

    def anticommutes(self, other: "PauliString") -> bool:
        """Check if this Pauli string anticommutes with another Pauli string."""
        t = 0
        for q in self.qubits.keys() & other.qubits.keys():
            p1 = self.qubits[q]
            p2 = other.qubits[q]
            if p1 == "I" or p2 == "I":
                continue
            t += self.qubits[q] != other.qubits[q]
        return t % 2 == 1

    def collapse_by(self, collapse_operators: Iterable[PauliString]):
        """Collapse the pauli string by the given operators.

        By collapsing, we mean that we replace the qubits that are in the given operators
        by identities.
        """
        pauli_string_copy = PauliString(self.qubits.copy())
        for operator in collapse_operators:
            for q in operator.qubits.keys():
                if q in pauli_string_copy.qubits:
                    pauli_string_copy.qubits[q] = "I"
        return pauli_string_copy

    def after(self, tableau: stim.Tableau, targets: Iterable[int]) -> "PauliString":
        stim_pauli_string = self.to_stim_pauli_string(
            length=max(list(targets) + list(self.qubits.keys())) + 1
        )
        stim_pauli_string_after = stim_pauli_string.after(tableau, targets=targets)
        return PauliString.from_stim_pauli_string(stim_pauli_string_after)

    def intersects(self, other: "PauliString") -> bool:
        return bool(self.qubits.keys() & other.qubits.keys())

    def contains(self, other: "PauliString") -> bool:
        return self.qubits.items() >= other.qubits.items()

    def __hash__(self):
        return self._hash

    def __eq__(self, other):
        if not isinstance(other, PauliString):
            return NotImplemented
        return self.qubits == other.qubits


def iter_stim_circuit_by_moments(
    circuit: stim.Circuit,
) -> Iterable[stim.Circuit | stim.CircuitRepeatBlock]:
    """Iterate over the `stim.Circuit` by moments.

    A moment in a `stim.Circuit` is a sequence of instructions between two `TICK`
    instructions. Note that we always consider a `stim.CircuitRepeatBlock` as a
    single moment.

    Args:
        circuit: The circuit to iterate over.

    Yields:
        A `stim.Circuit` or a `stim.CircuitRepeatBlock` instance.
    """
    cur_moment = stim.Circuit()
    for inst in circuit:
        if isinstance(inst, stim.CircuitRepeatBlock):
            yield cur_moment
            cur_moment.clear()
            yield inst
        elif inst.name == "TICK":
            cur_moment.append(inst)
            yield cur_moment
            cur_moment.clear()
        else:
            cur_moment.append(inst)
    if cur_moment:
        yield cur_moment


def collapsing_inst_to_pauli_strings(
    inst: stim.CircuitInstruction,
) -> list[PauliString]:
    name = inst.name
    targets = inst.targets_copy()
    if name in ["RX", "MX", "MRX"]:
        return [PauliString({target.qubit_value: "X"}) for target in targets]
    if name in ["RY", "MY", "MRY"]:
        return [PauliString({target.qubit_value: "Y"}) for target in targets]
    if name in ["R", "RZ", "M", "MZ", "MR", "MRZ"]:
        return [PauliString({target.qubit_value: "Z"}) for target in targets]
    if name in ["MXX", "MYY", "MZZ"]:
        pauli = name[1]
        return [
            PauliString({t1.qubit_value: pauli, t2.qubit_value: pauli})
            for t1, t2 in zip(targets[::2], targets[1::2])
        ]
    if name == "MPP":
        stim_pauli_strings = [
            stim.PauliString(pauli) for pauli in str(inst).split(" ")[1:]
        ]
        return [PauliString.from_stim_pauli_string(s) for s in stim_pauli_strings]
    raise TQECException(f"Not a collapsing instruction: {name}.")


def has_measurement(
    moment: stim.Circuit, check_are_all_measurements: bool = False
) -> bool:
    """Check if a `stim.Circuit` moment contains measurement instructions.

    Args:
        moment: The moment to check.
        check_are_all_measurements: If `True`, when the moment contains a measurement, then all
            instructions except for annotations and noise instructions must be measurement
            instructions, otherwise exception is raised.
    """
    if not any(stim.gate_data(inst.name).produces_measurements for inst in moment):
        return False
    if not check_are_all_measurements:
        return True
    for inst in moment:
        if stim.gate_data(inst.name).is_noisy_gate or inst.name in ANNOTATIONS:
            continue
        if not stim.gate_data(inst.name).produces_measurements:
            raise TQECException(
                f"The measurement moment contains non-measurement instruction: {inst}."
            )
    return True


def has_reset(moment: stim.Circuit, check_are_all_resets: bool = False) -> bool:
    """Check if a `stim.Circuit` moment contains reset instructions.

    Args:
        moment: The moment to check.
        check_are_all_resets: If `True`, when the moment contains a reset, then all
            instructions except for annotations and noise instructions must be reset
            instructions, otherwise exception is raised.
    """
    if not any(stim.gate_data(inst.name).is_reset for inst in moment):
        return False
    if not check_are_all_resets:
        return True
    for inst in moment:
        # note that measurements are noisy gates by define in stim
        if (
            stim.gate_data(inst.name).is_noisy_gate
            and not stim.gate_data(inst.name).produces_measurements
            or inst.name in ANNOTATIONS
        ):
            continue
        if not stim.gate_data(inst.name).is_reset:
            raise TQECException(
                f"The reset moment contains non-reset instruction: {inst}."
            )
    return True


def collapse_pauli_strings_at_moment(moment: stim.Circuit, is_reset: bool) -> list[PauliString]:
    def predicate(inst: stim.CircuitInstruction) -> bool:
        if is_reset:
            return stim.gate_data(inst.name).is_reset
        return stim.gate_data(inst.name).produces_measurements

    return [
        pauli_string
        for inst in moment
        if predicate(inst)
        for pauli_string in collapsing_inst_to_pauli_strings(inst)
    ]


class Fragment:
    def __init__(
        self,
        circuit: stim.Circuit,
        end_stabilizer_sources: list[PauliString] = (),
        begin_stabilizer_sources: list[PauliString] = (),
        sources_for_next_fragment: list[PauliString] = (),
    ):
        """A sub-circuit guaranteed to span the locations between two nearest collapsing
        moments or those outside the error detection regions."""

        self.circuit = circuit
        self.end_stabilizer_sources = list(end_stabilizer_sources)
        self.begin_stabilizer_sources = list(begin_stabilizer_sources)
        self.sources_for_next_fragment = list(sources_for_next_fragment)

    @property
    def have_detector_sources(self) -> bool:
        return not (
            len(self.end_stabilizer_sources) == 0
            and len(self.begin_stabilizer_sources) == 0
            and len(self.sources_for_next_fragment) == 0
        )


class FragmentLoop:
    def __init__(
        self, fragments: Iterable[Fragment | "FragmentLoop"], repetitions: int
    ):
        self.fragments = tuple(fragments)
        self.repetitions = repetitions

    def with_repetitions(self, repetitions: int) -> "FragmentLoop":
        return FragmentLoop(fragments=self.fragments, repetitions=repetitions)

    @property
    def have_detector_sources(self) -> bool:
        return any(fragment.have_detector_sources for fragment in self.fragments)


@dataclasses.dataclass
class SplitState:
    cur_fragment: stim.Circuit = dataclasses.field(default_factory=stim.Circuit)
    end_stabilizer_sources: list[PauliString] = dataclasses.field(default_factory=list)
    sources_for_next_fragment: list[PauliString] = dataclasses.field(
        default_factory=list
    )
    begin_stabilizer_sources: list[PauliString] = dataclasses.field(
        default_factory=list
    )
    seen_reset_at_head: bool = False
    seen_measurement_at_tail: bool = False

    def clear(self) -> None:
        self.cur_fragment.clear()
        self.end_stabilizer_sources.clear()
        self.sources_for_next_fragment.clear()
        self.begin_stabilizer_sources.clear()
        self.seen_reset_at_head = False
        self.seen_measurement_at_tail = False

    def to_fragment(self) -> Fragment:
        return Fragment(
            circuit=self.cur_fragment.copy(),
            end_stabilizer_sources=list(self.end_stabilizer_sources),
            begin_stabilizer_sources=list(self.begin_stabilizer_sources),
            sources_for_next_fragment=list(self.sources_for_next_fragment),
        )


def split_stim_circuit_into_fragments(
    circuit: stim.Circuit,
) -> list[Fragment | FragmentLoop]:
    """Split the circuit into fragments."""
    fragments = []
    state = SplitState()
    for moment in iter_stim_circuit_by_moments(circuit):
        if isinstance(moment, stim.CircuitRepeatBlock):
            if state.cur_fragment:
                fragments.append(state.to_fragment())
                state.clear()
            body_fragments = split_stim_circuit_into_fragments(moment.body_copy())
            fragments.append(
                FragmentLoop(fragments=body_fragments, repetitions=moment.repeat_count)
            )
        elif has_measurement(moment, check_are_all_measurements=True):
            state.cur_fragment += moment
            state.begin_stabilizer_sources.extend(
                collapse_pauli_strings_at_moment(moment, is_reset=False)
            )
            state.seen_measurement_at_tail = True
            state.sources_for_next_fragment.extend(
                collapse_pauli_strings_at_moment(moment, is_reset=True)
                if has_reset(moment, check_are_all_resets=False)
                else []
            )
        elif has_reset(moment, check_are_all_resets=True):
            pauli_strings = collapse_pauli_strings_at_moment(moment, is_reset=True)
            if state.seen_measurement_at_tail:
                state.cur_fragment += moment
                state.sources_for_next_fragment.extend(pauli_strings)
            elif state.seen_reset_at_head:
                state.cur_fragment += moment
                state.end_stabilizer_sources.extend(pauli_strings)
            else:
                if state.cur_fragment:
                    fragments.append(state.to_fragment())
                    state.clear()
                state.cur_fragment += moment
                state.end_stabilizer_sources.extend(pauli_strings)
                state.seen_reset_at_head = True

        elif state.seen_measurement_at_tail:
            fragments.append(state.to_fragment())
            state.clear()
            state.cur_fragment += moment
        else:
            state.cur_fragment += moment
    if state.cur_fragment:
        fragments.append(state.to_fragment())
    return fragments


def pauli_string_mean_coords(
    pauli_string: PauliString, qubit_coords_map: dict[int, list[float]]
) -> tuple[float, ...]:
    all_coords_items = [qubit_coords_map[i] for i in pauli_string.qubits.keys()]
    return tuple(np.mean(np.asarray(all_coords_items), axis=0)) + (0.0,)

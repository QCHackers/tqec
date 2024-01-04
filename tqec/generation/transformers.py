import typing as ty
from functools import partial

import cirq

from tqec.plaquette.plaquette import Plaquette

GateSubclass = ty.TypeVar("GateSubclass", bound=cirq.Gate)


@cirq.transformer
def merge_adjacent(
    circuit: cirq.AbstractCircuit,
    *,
    gate_type: type[GateSubclass],
    context: cirq.TransformerContext | None = None,
) -> cirq.AbstractCircuit:
    def merge_func(
        op_left: cirq.Operation, op_right: cirq.Operation
    ) -> cirq.Operation | None:
        both_mergeable: bool = (
            Plaquette.get_mergeable_tag() in op_left.tags
            and Plaquette.get_mergeable_tag() in op_right.tags
        )
        same_gate: bool = isinstance(op_left.gate, gate_type) and isinstance(
            op_right.gate, gate_type
        )
        if both_mergeable and same_gate:
            return op_left
        else:
            return None

    return cirq.merge_operations(
        circuit,
        merge_func=merge_func,
        deep=context.deep if context else True,  # default to deep transformation
        tags_to_ignore=context.tags_to_ignore if context else (),
    )


merge_adjacent_measurements = partial(merge_adjacent, gate_type=cirq.MeasurementGate)

merge_adjacent_resets = partial(merge_adjacent, gate_type=cirq.ResetChannel)


@cirq.transformer
def remove_tag(
    circuit: cirq.AbstractCircuit,
    *,
    tag: str,
    context: cirq.TransformerContext | None = None,
) -> cirq.AbstractCircuit:
    def map_func(operation: cirq.Operation, _: int) -> cirq.OP_TREE:
        tags = set(operation.tags)
        if tag in tags:
            tags.remove(tag)
        return operation.untagged.with_tags(*tags)

    return cirq.map_operations(
        circuit,
        map_func=map_func,
        deep=context.deep if context else True,  # default to deep transformation
        tags_to_ignore=context.tags_to_ignore if context else (),
    )


remove_mergeable_tag = partial(remove_tag, tag=Plaquette.get_mergeable_tag())

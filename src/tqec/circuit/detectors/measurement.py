from dataclasses import dataclass


@dataclass(frozen=True)
class MeasurementLocation:
    """Represents a unique measurement.

    A simple qubit index is in general not enough to locate unambiguously a
    single measurement, but this structure will only be used internally and
    in conditions (explicited below) that makes this information unambiguous.

    The following conditions are checked:

    Any given fragment cannot have multiple measurements involving the same
    qubit.
    This restriction means that if we can link a MeasurementLocation with one
    fragment, the measurement it represents is unique.

    Now, because build_flows_from_fragments from flow.py returns a list with
    the same "shape" (see the function documentation for more explanations on
    the meaning of that word), we keep a link between the original fragment and
    its related flows.

    In the end, as long as we keep each flow with its represented fragment,
    the qubit index is a sufficient information to retrieve unambiguously a
    given measurement.
    """

    qubit: int

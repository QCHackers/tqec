"""Defines core classes and functions to represent and manipulate quantum
circuits.

This package defines the core class :class:`ScheduledCircuit` that is used to
represent a quantum circuit in the `tqec` library. It also defines a few core
functions:

- :func:`annotate_detectors_automatically` that takes a quantum circuit implementing
  a complete QEC circuit and adds `DETECTOR` annotations.
- :func:`generate_circuit` that takes a :class:`Template` instance and a description
  of plaquettes via a :class:`Plaquettes` instance and generates a
  :class:`ScheduledCircuit` instance that corresponds to the circuit described.
- :func:`merge_scheduled_circuits` that is a function that helps merging several
  :class:`ScheduledCircuit` instances containing gates that are potentially scheduled
  at the same time (but not on the same qubits).

Functions from this package are really the backbone of the `tqec` library and are
re-used in higher-level packages (such as `tqec.compile`).
"""

from .detectors.construction import (
    annotate_detectors_automatically as annotate_detectors_automatically,
)
from .generation import generate_circuit as generate_circuit
from .qubit_map import QubitMap as QubitMap
from .schedule import ScheduledCircuit as ScheduledCircuit
from .schedule import ScheduleException as ScheduleException
from .schedule import merge_scheduled_circuits as merge_scheduled_circuits

"""Defines :class:`~.circuit.ScheduledCircuit`, used to represent quantum circuits
all over the :mod:`tqec` package.

This module defines some of the most used classes across the :mod:`tqec` code
base.
"""

from .circuit import ScheduledCircuit as ScheduledCircuit
from .exception import ScheduleException as ScheduleException
from .manipulation import merge_scheduled_circuits as merge_scheduled_circuits
from .manipulation import (
    relabel_circuits_qubit_indices as relabel_circuits_qubit_indices,
)
from .manipulation import remove_duplicate_instructions as remove_duplicate_instructions
from .schedule import Schedule as Schedule

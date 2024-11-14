"""Defines all the necessary data-structures to represent a plaquette.

This package defines one of the core class of the `tqec` library:
:class:`~.plaquette.Plaquette`.
The :class:`~.plaquette.Plaquette` class represents what is commonly called a
"plaquette" in quantum error correction and is basically a
:class:`~tqec.circuit.schedule.circuit.ScheduledCircuit` instance
representing the computation defining the plaquette.

Because we do not have a module to perform simple geometry operations on qubits
(yet), the :mod:`tqec.plaquette.qubit` module is providing classes to represent
the qubits a plaquette is applied to and perform some operations on them (e.g.,
get the qubits on a specific side of the plaquette).
"""

from .enums import MeasurementBasis, PlaquetteOrientation, PlaquetteSide, ResetBasis
from .frozendefaultdict import FrozenDefaultDict
from .plaquette import Plaquette, Plaquettes, RepeatedPlaquettes
from .qubit import PlaquetteQubits, SquarePlaquetteQubits

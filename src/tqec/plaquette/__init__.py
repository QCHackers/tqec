"""Defines all the necessary data-structures to represent a plaquette.

This package defines one of the core class of the `tqec` library: :class:`Plaquette`.
The :class:`Plaquette` class represents what is commonly called a "plaquette" in
quantum error correction and is basically a :class:`ScheduledCircuit` instance
representing the computation defining the plaquette.

Because we do not have a module to perform simple geometry operations on qubits
(yet), the :mod:`tqec.plaquette.qubit` module is providing classes to represent
the qubits a plaquette is applied to and perform some operations on them (e.g.,
get the qubits on a specific side of the plaquette).
"""

from .enums import PlaquetteOrientation, PlaquetteSide, ResetBasis, MeasurementBasis
from .plaquette import Plaquette, Plaquettes, RepeatedPlaquettes
from .qubit import PlaquetteQubits, SquarePlaquetteQubits
from .frozendefaultdict import FrozenDefaultDict

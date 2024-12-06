from tqec.circuit.schedule import ScheduledCircuit
from tqec.circuit.qubit_map import QubitMap
from tqec.plaquette.plaquette import Plaquette
from tqec.plaquette.qubit import PlaquetteQubits
from tqec.plaquette.qubit import SquarePlaquetteQubits

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from stim import Circuit as stim_Circuit


class BasisEnum(Enum):
    X = 'x'
    Y = 'y'
    Z = 'z'


class ExtendedBasisEnum(Enum):
    X = BasisEnum.X.value
    Y = BasisEnum.Y.value
    Z = BasisEnum.Z.value
    H = 'h'


@dataclass
class RPNG:
    """Organize a single RPNG value

    ----
    Simplified RPNG format:

    -z1-
    rpng
    
    (r) data qubit reset basis or h or -  
    (p) data basis for the controlled operation (x means CNOT controlled on the ancilla and targeting the data qubit, y means CY, z means CZ)  
    (n) time step (positive integers, all distinct, typically in 1-5)  
    (g) data qubit measure basis or h or -

    Assumptions on the circuit:
    - if not otherwise stated, a basis can be {x,y,z}
    - the ancilla is always the control qubit for the CNOT, CY, or CZ gates
    - time step of r same as ancilla reset (always 0)
    - time step of g same as ancilla measurement (by default 6)

    ----
    Extended RPNG format:

    The extra field (a) is used together with (p) to determine the 2Q gate involving the
    ancilla and data qubits. For example:
    - a=z, p=x --> CNOT controlled by the ancilla and targeting the data
    - a=z, p=z --> CZ   controlled by the ancilla and targeting the data
    - a=y, p=z --> CY   controlled by the data    and targeting the ancilla
    By default a=z.
    """
    r: Optional[ExtendedBasisEnum]
    p: Optional[BasisEnum]
    n: Optional[int]
    g: Optional[ExtendedBasisEnum]
    a: BasisEnum = BasisEnum.Z

    @classmethod
    def from_string(cls, rpng_string: str) -> 'RPNG':
        """Initialize the RPNG object from a 4-character string
        
        Note that any character different from a BasisEnum / ExtendedBasisEnum
        value would result in the corresponding field being None.
        """
        if len(rpng_string) != 4:
            raise ValueError('The rpng string must be exactly 4-character long.')
        r_str, p_str, n_str, g_str = tuple(rpng_string)
        r = ExtendedBasisEnum(r_str) if r_str in ExtendedBasisEnum._value2member_map_ else None
        p = BasisEnum(p_str) if p_str in BasisEnum._value2member_map_ else None
        n = int(n_str) if n_str.isdigit() else None
        g = ExtendedBasisEnum(g_str) if g_str in ExtendedBasisEnum._value2member_map_ else None
        return cls(r, p, n, g)
    
    def get_r_op(self) -> Optional[str]:
        """Get the reset operation or Hadamard"""
        op = self.r
        if op == None:
            return None
        elif op.value in BasisEnum._value2member_map_:
            return f'R{op.value.upper()}'
        else:
            return f'{op.value.upper()}'

    def get_g_op(self) -> Optional[str]:
        """Get the measurement operation or Hadamard"""
        op = self.g
        if op == None:
            return None
        elif op.value in BasisEnum._value2member_map_:
            return f'R{op.value.upper()}'
        else:
            return f'{op.value.upper()}'


@dataclass
class RGN:
    """Organize the prep and meas bases for the ancilla, together with the meas time
    
    The init time is assumed to be 0.
    """
    r: BasisEnum = BasisEnum.X
    g: BasisEnum = BasisEnum.X
    n: int = 6

    @classmethod
    def from_string(cls, rgn_string: str) -> 'RGN':
        """Initialize the RGN object from a 3-character string"""
        if len(rgn_string) != 3:
            raise ValueError('The rgn string must be exactly 3-character long.')
        r_str, g_str, n_str = tuple(rgn_string)

        try:
            r = BasisEnum(r_str)
            g = BasisEnum(g_str)
            n = BasisEnum(n_str)
            return cls(r, g, n)
        except ValueError:
            raise ValueError('Invalid rgn string.')


@dataclass
class RPNGDescription:
    """Organize the description of a plaquette in RPNG format
    
    The corners of the square plaquette are listed following the order:
    tl, tr, bl, br
    If the ancilla RGN description is not specified, it is assumed 'xx6'
    """
    corners: tuple[RPNG, RPNG, RPNG, RPNG]
    ancilla: RGN = RGN()

    def __post_init__(self):
        """Validation of the initialization arguments
        
        Constraints:
        - the n values for the corners must be unique
        - the n values for the corners must be in the interval ]0, ancilla.n[
        """
        times = []
        for rpng in self.corners:
            if rpng.n:
                if rpng.n < 1 or rpng.n >= self.ancilla.n:
                    raise ValueError('The n values must be in ]0, ancilla meas time[')
                times.append(rpng.n)
        if len(times) != len(set(times)):
            raise ValueError('The n values for the corners must be unique')
        elif len(times) not in [0,2,4]:
            raise ValueError('Each plaquette must have 0, 2, or 4 2Q gates')

    @classmethod
    def from_string(cls, corners_rpng_string: str) -> 'RPNGDescription':
        """Initialize the RPNGDescription object from a (16+3)-character string"""
        rpng_objs = tuple([RPNG.from_string(s) for s in corners_rpng_string.split(' ')])
        if len(rpng_objs) != 4:
            raise ValueError('There must be 4 corners in the RPNG description.')
        return cls(rpng_objs)

    def get_r_op(self, data_idx: int) -> Optional[str]:
        """Get the reset operation or Hadamard for the specific data qubit"""
        return self.corners[data_idx].get_r_op()

    def get_n(self, data_idx: int):
        """Get the time of the 2Q gate involving the specific data qubit"""
        return self.corners[data_idx].n

    def get_g_op(self, data_idx: int) -> Optional[str]:
        """Get the measurement operation or Hadamard for the specific data qubit"""
        return self.corners[data_idx].get_g_op()
    
    def get_plaquette(self, qubits: PlaquetteQubits = SquarePlaquetteQubits()) -> Plaquette:
        """Get the plaquette corresponding to the RPNG description
        
        Note that the ancilla qubit is the last among the PlaquetteQubits and thus
        has index 4, while the data qubits have indices 0-3.
        """
        prep_time = 0
        meas_time = self.ancilla.n
        circuit_as_list = [''] * (meas_time - prep_time + 1)
        for q, rpng in enumerate(self.corners):
            # 2Q gates.
            if rpng.n and rpng.p:
                circuit_as_list[rpng.n] += f'C{rpng.p.value.upper()} 4 {q}\n'
            # Data reset or Hadamard.
            if rpng.r:
                circuit_as_list[0] += f'{rpng.get_r_op()} {q}\n'
            # Data measurement or Hadamard.
            if rpng.g:
                circuit_as_list[0] += f'{rpng.get_g_op()} {q}\n'
        # Ancilla reset and measurement.
        circuit_as_list[0] += f'R{self.ancilla.r.value.upper()} 4\n'
        circuit_as_list[-1] += f'M{self.ancilla.g.value.upper()} 4\n'
        q_map = QubitMap.from_qubits(qubits)
        circuit_as_str = "TICK\n".join(circuit_as_list)
        circuit = stim_Circuit(circuit_as_str)
        scheduled_circuit = ScheduledCircuit.from_circuit(circuit, qubit_map = q_map)
        return Plaquette(name = 'test', qubits = qubits, circuit = scheduled_circuit)

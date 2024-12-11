from tqec.circuit.schedule import ScheduledCircuit
from tqec.circuit.qubit_map import QubitMap
from tqec.plaquette.plaquette import Plaquette
from tqec.plaquette.qubit import PlaquetteQubits
from tqec.plaquette.qubit import SquarePlaquetteQubits

from dataclasses import dataclass
from enum import Enum

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


@dataclass(frozen=True)
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

    Attributes:
        r   data qubit reset basis or h or -  
        p   data basis for the controlled operation (assuming a=z, x means CNOT controlled on the ancilla and targeting the data qubit, y means CY, z means CZ)  
        n   time step (positive integers, all distinct, typically in 1-5)  
        g   data qubit measure basis or h or -
        a   ancilla basis for the controlled operation (x means that the controlled operation is applied if ancilla is in |+>, y if it is in |-y>, z if it is in |1>)
    """
    r: ExtendedBasisEnum | None
    p: BasisEnum | None
    n: int | None
    g: ExtendedBasisEnum | None
    a: BasisEnum = BasisEnum.Z

    @classmethod
    def from_string(cls, rpng_string: str) -> 'RPNG':
        """Initialize the RPNG object from a 4-character or 5-character string
        
        4-character -> simplified format -> RPNG
        5-character -> extended format -> RAPNG

        Note that the ancilla basis(a) is the second character, just before (p).

        Note that any character different from a BasisEnum / ExtendedBasisEnum
        value would result in the corresponding field being None.
        """
        a_str = 'z'
        if len(rpng_string) == 4:
            r_str, p_str, n_str, g_str = tuple(rpng_string)
        elif len(rpng_string) == 5:
            r_str, a_str, p_str, n_str, g_str = tuple(rpng_string)
        else:
            raise ValueError('The rpng string must be exactly 4- or 5-character long.')
        # Convert the characters into the enum attributes (or raise error).
        r = ExtendedBasisEnum(r_str) if r_str in ExtendedBasisEnum._value2member_map_ else None
        a = BasisEnum(a_str) if a_str in BasisEnum._value2member_map_ else None
        p = BasisEnum(p_str) if p_str in BasisEnum._value2member_map_ else None
        n = int(n_str) if n_str.isdigit() else None
        g = ExtendedBasisEnum(g_str) if g_str in ExtendedBasisEnum._value2member_map_ else None
        # Raise error if anythiong but '-' was used to indicate None.
        if not r and r_str != '-':
            raise ValueError('Unacceptable character for the R field.')
        if not p and p_str != '-':
            raise ValueError('Unacceptable character for the P field.')
        if p and not a:
            raise ValueError('Unacceptable ancilla basis in the extended format (i.e. rapng).')
        if not n and n_str != '-':
            raise ValueError('Unacceptable character for the N field.')
        if not g and g_str != '-':
            raise ValueError('Unacceptable character for the G field.')
        return cls(r, p, n, g, a)

    
    def get_r_op(self) -> str | None:
        """Get the reset operation or Hadamard"""
        op = self.r
        if op == None:
            return None
        elif op.value in BasisEnum._value2member_map_:
            return f'R{op.value.upper()}'
        else:
            return f'{op.value.upper()}'

    def get_g_op(self) -> str | None:
        """Get the measurement operation or Hadamard"""
        op = self.g
        if op == None:
            return None
        elif op.value in BasisEnum._value2member_map_:
            return f'M{op.value.upper()}'
        else:
            return f'{op.value.upper()}'


@dataclass(frozen=True)
class RGN:
    """Organize the prep and meas bases for the ancilla, together with the meas time
    
    The init time is assumed to be 0.

    Attributes:
        r   ancillaqubit reset basis  
        g   ancilla qubit measure basis
        n   time step of ancilla measurement
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
            n = int(n_str)
            return cls(r, g, n)
        except ValueError as err:
            raise ValueError('Invalid rgn string.') from err


@dataclass
class RPNGDescription:
    """Organize the description of a plaquette in RPNG format
    
    The corners of the square plaquette are listed following the order:
    top-left, top-right, bottom-left, bottom-right. That is a Z-shaped path on the plaquette data-qubits:
    
        +------------+
        | 1 -----> 2 |
        |        /   |
        |      /     |
        |    ∟       |
        | 3 -----> 4 |
        +------------+
    If the ancilla RGN description is not specified, it is assumed 'xx6'

    Attributes:
        corners RPNG description of the four corners of the plaquette
        ancilla RGN description of the ancilla
    """
    corners: tuple[RPNG, RPNG, RPNG, RPNG]
    ancilla: RGN = RGN()

    def __post_init__(self):
        """Validation of the initialization arguments
        
        Constraints:
        - the n values for the corners must be unique
        - the n values for the corners must be in the interval ]0, ancilla.n[
        - at least one betwween fields a and p in every corner is z
        """
        times = []
        for rpng in self.corners:
            if rpng.n:
                if rpng.n < 1 or rpng.n >= self.ancilla.n:
                    raise ValueError('The n values must be in ]0, ancilla meas time[.')
                times.append(rpng.n)
            # Confirm that at least one betwween fields a and p in every corner is z, if 2Q gate is present
            if rpng.p and rpng.a != BasisEnum.Z and rpng.p != BasisEnum.Z:
                raise ValueError('At least one between a and p must be "z" in every corner.')
        if len(times) != len(set(times)):
            raise ValueError('The n values for the corners must be unique.')
        elif len(times) not in [0,2,4]:
            raise ValueError('Each plaquette must have 0, 2, or 4 2Q gates.')


    @classmethod
    def from_string(cls, corners_rpng_string: str) -> 'RPNGDescription':
        """Initialize the RPNGDescription object from a (16+3)-character string"""
        rpng_objs = tuple([RPNG.from_string(s) for s in corners_rpng_string.split(' ')])
        if len(rpng_objs) != 4:
            raise ValueError('There must be 4 corners in the RPNG description.')
        return cls(rpng_objs)
    

    @classmethod
    def from_extended_string(cls, ancilla_and_corners_rpng_string: str) -> 'RPNGDescription':
        """Initialize the RPNGDescription object from a (16+3)-character string"""
        values = ancilla_and_corners_rpng_string.split(' ')
        ancilla_rgn = RGN.from_string(values[0])
        rpng_objs = tuple([RPNG.from_string(s) for s in values[1:]])
        if len(rpng_objs) != 4:
            raise ValueError('There must be 4 corners in the RPNG description.')
        return cls(rpng_objs, ancilla_rgn)


    def get_r_op(self, data_idx: int) -> str | None:
        """Get the reset operation or Hadamard for the specific data qubit"""
        return self.corners[data_idx].get_r_op()

    def get_n(self, data_idx: int):
        """Get the time of the 2Q gate involving the specific data qubit"""
        return self.corners[data_idx].n

    def get_g_op(self, data_idx: int) -> str | None:
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
                if rpng.a.value == 'z':
                    circuit_as_list[rpng.n] += f'C{rpng.p.value.upper()} 4 {q}\n'
                elif rpng.p.value == 'z':
                    circuit_as_list[rpng.n] += f'C{rpng.a.value.upper()} {q} 4\n'
                else:
                    circuit_as_list[rpng.n] += f'{rpng.a.value.upper()}C{rpng.p.value.upper()} 4 {q}\n'
            # Data reset or Hadamard.
            if rpng.r:
                circuit_as_list[0] += f'{rpng.get_r_op()} {q}\n'
            # Data measurement or Hadamard.
            if rpng.g:
                circuit_as_list[-1] += f'{rpng.get_g_op()} {q}\n'
        # Ancilla reset and measurement.
        circuit_as_list[0] += f'R{self.ancilla.r.value.upper()} 4\n'
        circuit_as_list[-1] += f'M{self.ancilla.g.value.upper()} 4\n'
        q_map = QubitMap.from_qubits(qubits)
        circuit_as_str = "TICK\n".join(circuit_as_list)
        circuit = stim_Circuit(circuit_as_str)
        scheduled_circuit = ScheduledCircuit.from_circuit(circuit, qubit_map = q_map)
        return Plaquette(name = 'test', qubits = qubits, circuit = scheduled_circuit)

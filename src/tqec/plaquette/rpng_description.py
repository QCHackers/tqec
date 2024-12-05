from tqec.circuit.schedule import ScheduledCircuit
from tqec.circuit.qubit_map import QubitMap
from tqec.plaquette.plaquette import Plaquette
from tqec.plaquette.qubit import PlaquetteQubits
from tqec.plaquette.qubit import SquarePlaquetteQubits

from stim import Circuit as stim_Circuit

_PLAQUETTE_PREP_TIME = 0
_PLAQUETTE_MEAS_TIME = 6

def validate_rpng_string(
        rpng_string: str,
        prep_time: int = _PLAQUETTE_PREP_TIME,
        meas_time: int = _PLAQUETTE_MEAS_TIME,
        debug_info: bool = True
    ) -> int:
    """Check the validity of a RPNG string

    ----
    Simplified RPNG format:

    -z1- -z2- -z3- -z4-
    rpng rpng rpng rpng
    
    (r) data qubit reset basis or h or -  
    (p) data basis for the controlled operation (x means CNOT controlled on the ancilla and targeting the data qubit, y means CY, z means CZ)  
    (n) time step (positive integers, all distinct, typically in 1-5)  
    (g) data qubit measure basis or h or -

    Assumptions on the circuit:
    - if not otherwise stated, a basis can be {x,y,z}
    - the ancilla is always initialized in |+> and measured in the X basis
    - the ancilla is always the control qubit for the CNOT and CZ gates
    - time step of r same as ancilla reset (default 0)
    - time step of g same as ancilla measurement (default 6)

    ----
    Extended RPNG format:

    z0z5 -xz1- -xz2- -xz3- -xz4-
    pnpn rppng rppng rppng rppng

    (p) ancilla init basis  
    (n) time step  
    (p) ancilla measure basis  
    (n) time step

    (r) data qubit reset basis or h or -  
    (pp) ancilla-data 2-qubit bases (xz means CNOT targeting the ancilla)
    (n) time step (positive integers, all distinct)
    (g) data qubit measure basis or h or -

    Assumptions on the circuit:
    - if not otherwise stated, a basis can be {x,y,z}
    - at least one of the (pp) must be z, indicating the control qubit
    - time step of r same as ancilla reset
    - time step of g same as ancilla measurement
    - the time step of every (pp) must be in [ancilla init time + 1, ancilla measure time -1]  

    ----
    Return values:
    0 -- invalide rpng string
    1 -- valide rpng string in the simplified format 
    2 -- valide rpng string in the extended format 
    """
    def debug_print(*args, **kwargs):
        if debug_info:
            print(*args, **kwargs)

    q_values = rpng_string.split(' ')
    acceptable_r = ['-', 'x', 'y', 'z', 'h']
    acceptable_p = ['-', 'x', 'y', 'z']
    acceptable_g = acceptable_r
    acceptable_r_ancilla = ['x', 'y', 'z']
    acceptable_g_ancilla = acceptable_r_ancilla
    if len(q_values) == 4:
        times = []
        for i, v in enumerate(q_values):
            if len(v) != 4:
                debug_print('Wrong number of RPNG values')
                return 0
            # Collect times.
            if v[2] != '-':
                if v[2].isdigit() and int(v[2]) > prep_time and int(v[2]) < meas_time:
                    times.append(int(v[2]))
                else:
                    debug_print(f'Wrong N field in value {v}')
                    return 0
            # In absence of a time, we impose that RPNG must be '----'.
            elif v != '----':
                debug_print('No reset or measurement without an operation')
                return 0
            else:
                continue
            is_valid = v[0] in acceptable_r and \
                       v[1] in acceptable_p and \
                       v[3] in acceptable_g
            if not is_valid:
                debug_print(f'Wrong basis for reset, gate or measurement in value {v}')
                return 0
        # Confirm unique time and that either 0, 2, or 4 data are involved in 2Q ops.
        if len(times) != len(set(times)):
            debug_print(f'Times are not unique')
            return 0
        elif len(times) in [0,2,4]:
            return 1
        else:
            debug_print(f'Number of 2Q gates different from {0,2,4}')
            return 0
    elif len(q_values) == 5:
        # Value for the ancilla qubit.
        v = q_values[0]
        if len(v) != 4:
            return 0
        # Update init time.
        if v[1].isdigit() and int(v[1]) >= prep_time and int(v[1]) < meas_time:
            prep_time = int(v[1])
        else:
            return 0
        # Update meas time.
        if v[3].isdigit() and int(v[3]) > prep_time and int(v[3]) <= meas_time:
            meas_time = int(v[3])
        else:
            return 0
        is_valid = v[0] in acceptable_r_ancilla and \
                   v[2] in acceptable_g_ancilla
        if not is_valid:
            return 0
        # values for the data qubits.
        times = []
        for i, v in enumerate(q_values[1:]):
            if len(v) != 5:
                debug_print('Wrong number of RPNG values')
                return 0
            # Collect times.
            if v[3] != '-':
                if v[3].isdigit() and int(v[3]) > prep_time and int(v[3]) < meas_time:
                    times.append(int(v[3]))
                else:
                    debug_print(f'Wrong N field in value {v}')
                    return 0
            # In absence of a time, we impose that RPNG must be '-----'.
            elif v != '-----':
                debug_print('No reset or measurement without an operation')
                return 0
            else:
                continue
            is_valid = v[0] in acceptable_r and \
                       v[1] in acceptable_p and \
                       v[2] in acceptable_p and \
                       v[4] in acceptable_g
            if not is_valid:
                debug_print(f'Wrong basis for reset, gate or measurement in value {v}')
                return 0
            if v[1] != 'z' and v[2] != 'z':
                debug_print(f'At least one basis of (pp) should be z. Error in value {v}')
                return 0
        # Confirm unique time and that either 0, 2, or 4 data are involved in 2Q ops.
        if len(times) != len(set(times)):
            debug_print(f'Times are not unique')
            return 0
        elif len(times) in [0,2,4]:
            return 2
        else:
            debug_print(f'Number of 2Q gates different from {0,2,4}')
            return 0
    else:
        return 0


def create_plaquette_from_rpng_string(
        rpng_string: str,
        qubits: PlaquetteQubits = SquarePlaquetteQubits(),
        prep_time: int = _PLAQUETTE_PREP_TIME,
        meas_time: int = _PLAQUETTE_MEAS_TIME
    ) -> Plaquette:
    """Create a plaquette from the RPNG format
    
    Assumptions:
    - the ancilla qubit is the last among the PlaquetteQubits (thus has index 4)
    """
    format = validate_rpng_string(rpng_string, prep_time=prep_time, meas_time=meas_time)
    circuit_as_list = []
    if format == 1:
        circuit_as_list = [''] * (meas_time - prep_time + 1)
        for q, v in enumerate(rpng_string.split(' ')):
            # 2Q gates.
            if v[2] != '-':
                circuit_as_list[int(v[2])] += f'C{v[1].upper()} 4 {q}\n'
            # Data reset or Hadamard.
            if v[0] == 'h':
                circuit_as_list[0] += f'H {q}\n'
            elif v[0] != '-':
                circuit_as_list[0] += f'R{v[0].upper()} {q}\n'
            # Data measurement or Hadamard.
            if v[3] == 'h':
                circuit_as_list[-1] += f'H {q}\n'
            elif v[3] != '-':
                circuit_as_list[-1] += f'M{v[3].upper()} {q}\n'
        # Ancilla reset and measurement.
        circuit_as_list[0] += 'RX 4\n'
        circuit_as_list[-1] += 'MX 4\n'
    elif format == 2:
        # Update prep and meas times.
        values = rpng_string.split(' ')
        prep_time = int(values[0][1])
        meas_time = int(values[0][3])
        circuit_as_list = [''] * (meas_time - prep_time + 1)
        for q, v in enumerate(values[1:]):
            # 2Q gates.
            if v[3] != '-':
                if v[1] == 'z':
                    circuit_as_list[int(v[3])] += f'C{v[2].upper()} 4 {q}\n'
                elif v[2] == 'z':
                    circuit_as_list[int(v[3])] += f'C{v[1].upper()} {q} 4\n'
            # Data reset or Hadamard.
            if v[0] == 'h':
                circuit_as_list[0] += f'H {q}\n'
            elif v[0] != '-':
                circuit_as_list[0] += f'R{v[0].upper()} {q}\n'
            # Data measurement or Hadamard.
            if v[4] == 'h':
                circuit_as_list[-1] += f'H {q}\n'
            elif v[4] != '-':
                circuit_as_list[-1] += f'M{v[4].upper()} {q}\n'
        # Ancilla reset and measurement.
        circuit_as_list[0] += 'RX 4\n'
        circuit_as_list[-1] += 'MX 4\n'
    elif format == 0:
        raise ValueError(f'invalide rpng string "{rpng_string}"')
    q_map = QubitMap.from_qubits(qubits)
    circuit_as_str = "TICK\n".join(circuit_as_list)
    circuit = stim_Circuit(circuit_as_str)
    scheduled_circuit = ScheduledCircuit.from_circuit(circuit, qubit_map = q_map)
    return Plaquette(name = 'test', qubits = qubits, circuit = scheduled_circuit)
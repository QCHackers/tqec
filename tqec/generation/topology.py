def compute_qubit_array_shape(number_of_plaquettes: int, plaquette_size: int) -> int:
    """Computes the underlying qubit array shape.

    This function computes the shape of the array that represent the qubits needed
    by a template that needs number_of_plaquettes plaquettes in the dimension of
    interest, each plaquette having plaquette_size qubits in this dimension.

    It takes into account the fact that plaquettes are sharing qubits at their
    interfaces.
    If we consider that a qubit shared by 2 plaquettes is owned by the plaquette
    before it (in the dimension of interest) then:
    - the first plaquette owns template_size qubits.
    - each following plaquettes owns template_size - 1 qubits.
    """
    return plaquette_size + (number_of_plaquettes - 1) * (plaquette_size - 1)


def get_plaquette_starting_index(plaquette_size: int, plaquette_index: int) -> int:
    """Compute starting index of a given plaquette on a grid of qubits

    This function assumes that **all** plaquette instances have the exact same size.
    This assumption is currently asserted in various parts of the code, and so should
    be valid.

    This function also assumes that plaquettes are square-like shapes and share qubits
    on their edges.

    :param plaquette_size: number of qubits required by the plaquette in the dimension
        of interest (x or y).
    :param plaquette_index: index of the plaquette we want to know the starting index of.
    """
    return plaquette_index * (plaquette_size - 1)

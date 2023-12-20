import numpy

from tqec.plaquette.plaquette import Plaquette
from tqec.templates.base import Template
from tqec.templates.orchestrator import TemplateOrchestrator

# As plaquettes are overlapping, there is a bit of math to do. For each dimension:
#   the 2 plaquettes on both ends will overlap with only one plaquette
#   all the other plaquettes will overlap with 2 plaquettes


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


def get_plaquette_starting_index(plaquette_size: int, index: int) -> int:
    return index * (plaquette_size - 1)


def compute_qubit_array(
    template: Template | TemplateOrchestrator, plaquettes: list[Plaquette]
) -> numpy.ndarray:
    """Computes and returns a boolean array representing the used qubits.

    The plaquettes provided as input to this function will be indexed starting from 1
    to avoid the confusion with 0 encoding "no plaquette".
    """
    # Instanciate the template to get the array of plaquette indices
    indices = list(range(1, len(plaquettes) + 1))
    scalable_template_instanciation = template.instanciate(*indices)
    stiy, stix = scalable_template_instanciation.shape

    # Get the qubit_array for each plaquette. For the moment we require each plaquette to
    # have the same qubit array as it is simpler. A more involved approach should likely be
    # used for the future.
    plaquettes_qubit_array = [p.to_qubit_array() for p in plaquettes]
    pqay, pqax = plaquettes_qubit_array[0].shape
    assert all(pqa.shape == (pqax, pqay) for pqa in plaquettes_qubit_array)

    # Instanciate the final array

    final_shape = (
        compute_qubit_array_shape(stiy, pqay),
        compute_qubit_array_shape(stix, pqax),
    )
    final_array = numpy.zeros(final_shape, dtype=bool)
    for y, line in enumerate(scalable_template_instanciation):
        for x, plaquette_index in enumerate(line):
            y_origin = get_plaquette_starting_index(pqay, y)
            x_origin = get_plaquette_starting_index(pqax, x)
            # plaquettes indices start at 1 and 0 means no plaquette.
            # So if we find a 0, there is no plaquette, we avoid.
            if plaquette_index == 0:
                continue
            final_array[
                y_origin : y_origin + pqay, x_origin : x_origin + pqax
            ] = plaquettes_qubit_array[plaquette_index - 1]
    return final_array


def get_qubit_array_str(
    array: numpy.ndarray, qubit_str: str = "x", nothing_str: str = " "
) -> str:
    return "\n".join(
        "".join(qubit_str if boolean else nothing_str for boolean in line)
        for line in array
    )

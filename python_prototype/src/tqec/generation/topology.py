import numpy

from tqec.plaquette.plaquette import Plaquette
from tqec.templates.base import Template
from tqec.templates.orchestrator import TemplateOrchestrator


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
    # As plaquettes are overlapping, there is a bit of math to do. For each dimension:
    #   the 2 plaquettes on both ends will overlap with only one plaquette
    #   all the other plaquettes will overlap with 2 plaquettes
    # If we consider that a qubit shared by 2 plaquettes is owned by the plaquette
    # on the left (resp. top) then:
    # - the first plaquette owns template_size qubits.
    # - each following plaquettes owns template_size - 1 qubits.
    def compute_shape(number_of_templates: int, template_size: int) -> int:
        return template_size + (number_of_templates - 1) * (template_size - 1)

    def get_global_index(template_size: int, index: int) -> int:
        return index * (template_size - 1)

    final_shape = (compute_shape(stiy, pqay), compute_shape(stix, pqax))
    final_array = numpy.zeros(final_shape, dtype=bool)
    for y, line in enumerate(scalable_template_instanciation):
        for x, plaquette_index in enumerate(line):
            y_origin = get_global_index(pqay, y)
            x_origin = get_global_index(pqax, x)
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

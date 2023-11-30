from tqec.templates.base import Template


def display(template: Template, *plaquette_indices: int) -> None:
    """Display a template instance with ASCII output.

    :param template: the Template instance to display.
    :param plaquette_indices: the plaquette indices that are forwarded to the
        call to template.instanciate to get the actual template representation.
    """
    arr = template.instanciate(*plaquette_indices)
    for line in arr:
        for element in line:
            element = str(element) if element != 0 else "."
            print(f"{element:>3}", end="")
        print()

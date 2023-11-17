from tqec.templates.base import Template


def display(template: Template, *plaquette_indices: int) -> None:
    arr = template.instanciate(*plaquette_indices)
    for line in arr:
        for element in line:
            element = str(element) if element != 0 else "."
            print(f"{element:>3}", end="")
        print()

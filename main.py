from tqec.templates.display import display_template
from tqec.templates.qubit import QubitTemplate

template = QubitTemplate()
display_template(template, 2)

k = 5
removed_plaquettes = {1, 2, 3, 4, 5, 8, 12, 14}
display_template(
    template, k, [i if i not in removed_plaquettes else 0 for i in range(1, 15)]
)

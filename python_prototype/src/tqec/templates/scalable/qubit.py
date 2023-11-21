from tqec.enums import ABOVE_OF, BELOW_OF, LEFT_OF, RIGHT_OF
from tqec.templates.base import TemplateWithPlaquettes
from tqec.templates.scalable.rectangle import ScalableRectangle
from tqec.templates.scalable.square import ScalableAlternatingSquare
from tqec.templates.orchestrator import TemplateOrchestrator


class ScalableQubitSquare(TemplateOrchestrator):
    def __init__(self, dim: int) -> None:
        self._template_instances = [
            # Central square, containing plaquettes of types 3 and 4
            TemplateWithPlaquettes(ScalableAlternatingSquare(dim), [3, 4]),
            # Top rectangle, containing plaquettes of type 1 only
            TemplateWithPlaquettes(ScalableRectangle(dim, 1), [0, 1]),
            # Left rectangle, containing plaquettes of type 2 only
            TemplateWithPlaquettes(ScalableRectangle(1, dim), [2, 0]),
            # Right rectangle, containing plaquettes of type 5 only
            TemplateWithPlaquettes(ScalableRectangle(1, dim), [0, 5]),
            # Bottom rectangle, containing plaquettes of type 6 only
            TemplateWithPlaquettes(ScalableRectangle(dim, 1), [0, 6]),
        ]
        TemplateOrchestrator.__init__(self, self._template_instances[1])
        self._construct()

    def _construct(self) -> None:
        self.add_template(self.ti(1), ABOVE_OF, self.ti(0)).add_template(
            self.ti(2), LEFT_OF, self.ti(0)
        ).add_template(self.ti(3), RIGHT_OF, self.ti(0)).add_template(
            self.ti(4), BELOW_OF, self.ti(0)
        )

    def ti(self, index: int) -> TemplateWithPlaquettes:
        return self._template_instances[index]


class ScalableQubitRectangle(TemplateOrchestrator):
    def __init__(self, width: int, height: int) -> None:
        self._template_instances = [
            # Central square, containing plaquettes of types 3 and 4
            TemplateWithPlaquettes(ScalableRectangle(width, height), [3, 4]),
            # Top rectangle, containing plaquettes of type 1 only
            TemplateWithPlaquettes(ScalableRectangle(width, 1), [0, 1]),
            # Left rectangle, containing plaquettes of type 2 only
            TemplateWithPlaquettes(ScalableRectangle(1, height), [2, 0]),
            # Right rectangle, containing plaquettes of type 5 only
            TemplateWithPlaquettes(ScalableRectangle(1, height), [0, 5]),
            # Bottom rectangle, containing plaquettes of type 6 only
            TemplateWithPlaquettes(ScalableRectangle(width, 1), [0, 6]),
        ]
        TemplateOrchestrator.__init__(self, self._template_instances[1])
        self._construct()

    def _construct(self) -> None:
        self.add_template(self.ti(1), ABOVE_OF, self.ti(0)).add_template(
            self.ti(2), LEFT_OF, self.ti(0)
        ).add_template(self.ti(3), RIGHT_OF, self.ti(0)).add_template(
            self.ti(4), BELOW_OF, self.ti(0)
        )

    def ti(self, index: int) -> TemplateWithPlaquettes:
        return self._template_instances[index]

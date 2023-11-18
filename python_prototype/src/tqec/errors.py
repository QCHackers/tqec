class TemplateNotInOrchestrator(Exception):
    def __init__(self, orchestrator, template) -> None:
        super().__init__(
            f"Template {template} is not in the Orchestrator instance {orchestrator}."
        )

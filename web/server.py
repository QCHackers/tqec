from copy import deepcopy

from fastapi import FastAPI
from tqec.circuit.schemas import SupportedCircuitTypeEnum
from tqec.plaquette.schemas import PlaquetteLibraryModel
from tqec.templates.schemas import InstantiableTemplateModel
from tqec.web.session import UserSession

app = FastAPI()
session = UserSession()


@app.get("/")
def read_root():
    return {"Hello": "Myself"}


@app.get("/plaquettes/list")
def get_plaquette_library() -> PlaquetteLibraryModel:
    return session.plaquette_library.to_model(SupportedCircuitTypeEnum.stim)


@app.get("/templates/list")
def get_instanciable_templates() -> list[InstantiableTemplateModel]:
    return session.template_library.get_descriptions()

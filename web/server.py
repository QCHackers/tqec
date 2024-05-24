from typing import Union

from fastapi import FastAPI
from tqec.templates.atomic.rectangle import AlternatingRectangleTemplate
from tqec.templates.scale import (
    Dimension,
    FixedDimension,
    LinearFunction,
    ScalableShape2D,
)
from tqec.templates.schemas import InstantiableTemplateModel

app = FastAPI()


@app.get("/")
def read_root():
    return {"Hello": "Myself"}


@app.get("/templates/list")
def get_instanciable_templates() -> list[InstantiableTemplateModel]:
    fixed_1 = FixedDimension(1)
    scaling_2k = Dimension(2, LinearFunction(2, 0))
    return [
        InstantiableTemplateModel(
            name="1x1",
            shape=ScalableShape2D(fixed_1, fixed_1),
            instantiation=[[1]],
        ),
        InstantiableTemplateModel(
            name="2kx1",
            shape=ScalableShape2D(scaling_2k, fixed_1),
            instantiation=AlternatingRectangleTemplate(scaling_2k, fixed_1)
            .instantiate([1, 2])
            .tolist(),
        ),
        InstantiableTemplateModel(
            name="1x2k",
            shape=ScalableShape2D(fixed_1, scaling_2k),
            instantiation=AlternatingRectangleTemplate(fixed_1, scaling_2k)
            .instantiate([1, 2])
            .tolist(),
        ),
        InstantiableTemplateModel(
            name="2kx2k",
            shape=ScalableShape2D(scaling_2k, scaling_2k),
            instantiation=AlternatingRectangleTemplate(scaling_2k, scaling_2k)
            .instantiate([1, 2])
            .tolist(),
        ),
    ]

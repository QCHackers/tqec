from __future__ import annotations

from typing import Annotated, Literal, Union

import networkx as nx
from pydantic import BaseModel, Field

from tqec.enums import CornerPositionEnum
from tqec.position import Displacement
from tqec.templates.scale import LinearFunction, PiecewiseLinearFunction, Scalable2D


class TemplateModel(BaseModel):
    default_increments: Displacement
    k: int


class TemplateWithIndicesModel(BaseModel):
    template: InstantiableTemplateModel
    indices: list[int]


class AlternatingRectangleTemplateModel(TemplateModel):
    tag: Literal["AlternatingRectangle"]
    width: LinearFunction
    height: LinearFunction


class RawRectangleTemplateModel(TemplateModel):
    tag: Literal["RawRectangle"]
    indices: list[list[int]]


class AlternatingSquareTemplateModel(TemplateModel):
    tag: Literal["AlternatingSquare"]
    dimension: LinearFunction


class AlternatingCornerSquareTemplateModel(TemplateModel):
    tag: Literal["AlternatingCornerSquare"]
    dimension: LinearFunction
    corner_position: CornerPositionEnum


class RelativePositionModel(BaseModel):
    start_idx: int
    end_idx: int
    start_corner: CornerPositionEnum
    end_corner: CornerPositionEnum


class RelativePositionsModel(BaseModel):
    positions: list[RelativePositionModel]

    def to_networkx(self) -> nx.DiGraph:
        G = nx.DiGraph()
        for relpos in self.positions:
            G.add_edge(
                relpos.start_idx,
                relpos.end_idx,
                relative_position=(relpos.start_corner, relpos.end_corner),
            )
        return G

    @staticmethod
    def from_networkx(G: nx.DiGraph) -> RelativePositionsModel:
        return RelativePositionsModel(
            positions=[
                RelativePositionModel(
                    start_idx=start_idx,
                    end_idx=end_idx,
                    start_corner=start_corner,
                    end_corner=end_corner,
                )
                for start_idx, end_idx, (
                    start_corner,
                    end_corner,
                ) in G.edges.data(
                    "relative_position"  # type: ignore
                )
            ]
        )


class ComposedTemplateModel(TemplateModel):
    tag: Literal["Composed"]
    templates: list[InstantiableTemplateModel]
    relative_positions: RelativePositionsModel



InstanciableTemplateModelsUnion = Union[
    AlternatingRectangleTemplateModel,
    AlternatingSquareTemplateModel,
    RawRectangleTemplateModel,
    # AlternatingCornerSquareTemplateModel,
    ComposedTemplateModel,
]
InstantiableTemplateModel = Annotated[
    InstanciableTemplateModelsUnion, Field(discriminator="tag")
]


class InstantiableTemplateDescriptionModel(BaseModel):
    name: str
    shape: Scalable2D
    instantiation: list[list[int]]


class TemplateLibraryModel(BaseModel):
    templates: list[InstantiableTemplateDescriptionModel]

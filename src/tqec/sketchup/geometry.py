from __future__ import annotations

import typing as ty
from dataclasses import dataclass
from enum import Enum

import numpy as np
import numpy.typing as npt

from tqec.sketchup.block_graph import BlockType, parse_block_type_from_str

_XYZ: list[ty.Literal["X", "Y", "Z"]] = ["X", "Y", "Z"]


class FaceType(Enum):
    X = "X"
    Z = "Z"
    H = "H"

    @staticmethod
    def from_string(face_type: str) -> "FaceType":
        return FaceType(face_type.upper())

    def opposite(self) -> "FaceType":
        if self == FaceType.X:
            return FaceType.Z
        if self == FaceType.Z:
            return FaceType.X
        return FaceType.H


@dataclass(frozen=True)
class Face:
    """A rectangle face in the 3d space.

    (axis_width, axis_height, axis_normal) is by the right-hand rule, which
    only has 3 possible values: (X, Y, Z) | (Y, Z, X) | (Z, X, Y).
    """

    face_type: FaceType
    width: float
    height: float
    normal_direction: ty.Literal["X", "Y", "Z"]
    translation: ty.Tuple[float, float, float] = (0, 0, 0)

    @staticmethod
    def get_triangle_indices() -> npt.NDArray[np.int_]:
        return np.array([0, 1, 2, 2, 0, 3], dtype=np.int_)

    def get_vertices(self) -> npt.NDArray[np.float_]:
        ax3_index = ["X", "Y", "Z"].index(self.normal_direction)
        ax1_index = (ax3_index + 1) % 3
        ax2_index = (ax3_index + 2) % 3
        # rectangle vertices
        vertices_position = np.array(
            [
                [0, 0, 0],
                [self.width, 0, 0],
                [self.width, self.height, 0],
                [0, self.height, 0],
            ],
            dtype=np.float_,
        )
        # permute the axes
        permutation = [0, 1, 2]
        permutation[ax3_index] = 2
        permutation[ax1_index] = 0
        permutation[ax2_index] = 1
        vertices_position = vertices_position[:, permutation]
        # translate the rectangle
        vertices_position += np.asarray(self.translation, dtype=np.float_)
        return vertices_position.flatten()

    def translated_by(self, dx: float, dy: float, dz: float) -> Face:
        return Face(
            self.face_type,
            self.width,
            self.height,
            self.normal_direction,
            (
                self.translation[0] + dx,
                self.translation[1] + dy,
                self.translation[2] + dz,
            ),
        )


Geometry = dict[BlockType, list[Face]]


def _create_cube_geometries() -> Geometry:
    """Create zxx, xzx, xxz, xzz, zxz, zzx cube geometries."""
    cube_geomeyries = {}
    width, height = 1, 1
    for name in ["zxx", "xzx", "xxz", "xzz", "zxz", "zzx"]:
        faces = []
        for i, face_type in enumerate(name):
            normal_direction = _XYZ[i]
            face = Face(
                FaceType.from_string(face_type), width, height, normal_direction
            )
            faces.append(face)
            translation = [0, 0, 0]
            translation[i] = 1
            faces.append(face.translated_by(*translation))
        cube_geomeyries[parse_block_type_from_str(name)] = faces
    return cube_geomeyries


def _create_no_h_pipe_geometries() -> Geometry:
    """Create ozx, oxz, xoz, zox, xzo, zxo pipe geometries."""
    pipe_geometries = {}
    for name in ["ozx", "oxz", "xoz", "zox", "xzo", "zxo"]:
        faces = []
        pipe_direction_index = name.index("o")
        for i, face_type in enumerate(name):
            if face_type == "o":
                continue
            if i == (pipe_direction_index - 1) % 3:
                width, height = 2, 1
            else:
                width, height = 1, 2
            normal_direction = _XYZ[i]
            face = Face(
                FaceType.from_string(face_type), width, height, normal_direction
            )
            faces.append(face)
            translation = [0, 0, 0]
            translation[i] = 1
            faces.append(face.translated_by(*translation))
        pipe_geometries[parse_block_type_from_str(name)] = faces
    return pipe_geometries


def _get_3d_translation(
    pipe_direction_index: int, value: float
) -> tuple[float, float, float]:
    assert 0 <= pipe_direction_index <= 2
    tmp: list[float] = [0, 0, 0]
    tmp[pipe_direction_index] = value
    return (tmp[0], tmp[1], tmp[2])


def _create_h_pipe_geometries() -> Geometry:
    """Create ozxh, oxzh, zoxh, xozh, zxoh, xzoh pipe geometries."""
    pipe_geometries = {}
    for name in ["ozxh", "oxzh", "zoxh", "xozh", "zxoh", "xzoh"]:
        faces: list[Face] = []
        pipe_direction_index = name.index("o")
        for i, face_type in enumerate(name[:-1]):
            if face_type == "o":
                continue
            if i == (pipe_direction_index - 1) % 3:
                w1, h1 = 0.9, 1.0
                w2, h2 = 0.2, 1.0
                w3, h3 = 0.9, 1.0
            else:
                w1, h1 = 1.0, 0.9
                w2, h2 = 1.0, 0.2
                w3, h3 = 1.0, 0.9
            normal_direction = _XYZ[i]
            face1 = Face(FaceType.from_string(face_type), w1, h1, normal_direction)
            face2_translation = _get_3d_translation(pipe_direction_index, 0.9)
            face2 = Face(FaceType.H, w2, h2, normal_direction, face2_translation)
            face3_translation = _get_3d_translation(pipe_direction_index, 1.1)
            face3 = Face(
                FaceType.from_string(face_type).opposite(),
                w3,
                h3,
                normal_direction,
                face3_translation,
            )
            faces.extend([face1, face2, face3])
            translation = [0, 0, 0]
            translation[i] = 1
            faces.extend(
                face.translated_by(*translation) for face in [face1, face2, face3]
            )
        pipe_geometries[parse_block_type_from_str(name)] = faces
    return pipe_geometries


def load_library_block_geometries() -> Geometry:
    """Load the geometries of all the library blocks."""
    geometry = {}
    # 6 cube blocks
    geometry.update(_create_cube_geometries())
    # 6 pipe blocks without H
    geometry.update(_create_no_h_pipe_geometries())
    # 6 pipe blocks with H
    geometry.update(_create_h_pipe_geometries())
    return geometry

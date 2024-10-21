from __future__ import annotations

import typing as ty
from dataclasses import dataclass
from enum import Enum

import numpy as np
import numpy.typing as npt

from tqec.position import Direction3D
from tqec.computation.block_graph import BlockKind, CubeKind, PipeKind


class FaceType(Enum):
    X = "X"
    Z = "Z"
    Y = "Y"
    H = "H"

    @staticmethod
    def from_string(face_type: str) -> FaceType:
        return FaceType(face_type.upper())

    def opposite(self) -> FaceType:
        if self == FaceType.X:
            return FaceType.Z
        if self == FaceType.Z:
            return FaceType.X
        return self


@dataclass(frozen=True)
class Face:
    """A rectangle face in the 3d space.

    (axis_width, axis_height, axis_normal) is by the right-hand rule, which
    only has 3 possible values: (X, Y, Z) | (Y, Z, X) | (Z, X, Y).

    Attributes:
        face_type: The type of the face.
        width: The width of the face.
        height: The height of the face.
        normal_direction: The normal direction of the face, which is the direction
            of the axis that the face is perpendicular to.
        positive_facing: Whether the normal direction is towards the positive direction
            of the axis.
        translation: The position translation of the face from the origin.
    """

    face_type: FaceType
    width: float
    height: float
    normal_direction: Direction3D
    positive_facing: bool = True
    translation: ty.Tuple[float, float, float] = (0, 0, 0)

    @staticmethod
    def get_triangle_indices() -> npt.NDArray[np.int_]:
        return np.array([0, 0, 2, 2, 1, 1, 2, 2, 0, 0, 3, 3], dtype=np.int_)

    def get_vertices(self) -> npt.NDArray[np.float64]:
        ax3_index = self.normal_direction.axis_index
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
            dtype=np.float64,
        )
        # permute the axes
        permutation = [0, 1, 2]
        permutation[ax3_index] = 2
        permutation[ax1_index] = 0
        permutation[ax2_index] = 1
        vertices_position = vertices_position[:, permutation]
        # translate the rectangle
        vertices_position += np.asarray(self.translation, dtype=np.float64)
        return vertices_position.flatten()

    def get_normal_vectors(self) -> npt.NDArray[np.float64]:
        normal = np.zeros(3, dtype=np.float64)
        ax3_index = self.normal_direction.axis_index
        normal[ax3_index] = 1 if self.positive_facing else -1
        return np.tile(normal, 4)

    def translated_by(self, dx: float, dy: float, dz: float) -> Face:
        return Face(
            self.face_type,
            self.width,
            self.height,
            self.normal_direction,
            self.positive_facing,
            (
                self.translation[0] + dx,
                self.translation[1] + dy,
                self.translation[2] + dz,
            ),
        )

    def with_opposite_facing(self) -> Face:
        return Face(
            self.face_type,
            self.width,
            self.height,
            self.normal_direction,
            not self.positive_facing,
            self.translation,
        )


def parse_block_type_from_str(block_type: str) -> BlockKind:
    """Parse a block type from a string."""
    if "o" in block_type:
        return PipeType(block_type.lower())
    else:
        return CubeType(block_type.lower())


Geometry = dict[BlockKind, list[Face]]


def _create_zx_cube_geometries() -> Geometry:
    """Create zxx, xzx, xxz, xzz, zxz, zzx cube geometries."""
    cube_geometries = {}
    width, height = 1.0, 1.0
    for name in ["zxx", "xzx", "xxz", "xzz", "zxz", "zzx"]:
        faces = []
        for i, face_type in enumerate(name):
            normal_direction = Direction3D.from_axis_index(i)
            face = Face(
                FaceType.from_string(face_type), width, height, normal_direction, False
            )
            faces.append(face)
            translation = [0.0, 0.0, 0.0]
            translation[i] = 1.0
            faces.append(face.translated_by(*translation).with_opposite_facing())
        cube_geometries[parse_block_type_from_str(name)] = faces
    return cube_geometries


def _create_y_cube_geometry() -> Geometry:
    """Create the y cube geometry."""
    faces = []
    for normal_direction in Direction3D.all():
        if normal_direction == Direction3D.X:
            width, height = 1.0, 0.5
        elif normal_direction == Direction3D.Y:
            width, height = 0.5, 1.0
        else:
            width, height = 1.0, 1.0
        face = Face(FaceType.Y, width, height, normal_direction, False)
        faces.append(face)
        translation = [0.0, 0.0, 0.0]
        translation[normal_direction.axis_index] = (
            1.0 if normal_direction != Direction3D.Z else 0.5
        )
        faces.append(face.translated_by(*translation).with_opposite_facing())
    return {CubeType.Y: faces}


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
                width, height = 2.0, 1.0
            else:
                width, height = 1.0, 2.0
            normal_direction = Direction3D.from_axis_index(i)
            face = Face(
                FaceType.from_string(face_type), width, height, normal_direction, False
            )
            faces.append(face)
            translation = [0.0, 0.0, 0.0]
            translation[i] = 1.0
            faces.append(face.translated_by(*translation).with_opposite_facing())
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
            normal_direction = Direction3D.from_axis_index(i)
            face1 = Face(
                FaceType.from_string(face_type), w1, h1, normal_direction, False
            )
            face2_translation = _get_3d_translation(pipe_direction_index, 0.9)
            face2 = Face(FaceType.H, w2, h2, normal_direction, False, face2_translation)
            face3_translation = _get_3d_translation(pipe_direction_index, 1.1)
            face3 = Face(
                FaceType.from_string(face_type).opposite(),
                w3,
                h3,
                normal_direction,
                False,
                face3_translation,
            )
            faces.extend([face1, face2, face3])
            translation = [0, 0, 0]
            translation[i] = 1
            faces.extend(
                face.translated_by(*translation).with_opposite_facing()
                for face in [face1, face2, face3]
            )
        pipe_geometries[parse_block_type_from_str(name)] = faces
    return pipe_geometries


def load_library_block_geometries() -> Geometry:
    """Load the geometries of all the library blocks."""
    geometry = {}
    # 6 x/z cube blocks
    geometry.update(_create_zx_cube_geometries())
    # 1 y cube block
    geometry.update(_create_y_cube_geometry())
    # 6 pipe blocks without H
    geometry.update(_create_no_h_pipe_geometries())
    # 6 pipe blocks with H
    geometry.update(_create_h_pipe_geometries())
    return geometry

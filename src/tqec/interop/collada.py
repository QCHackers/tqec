"""Handling interoperation with Collada DAE files."""

from __future__ import annotations

import pathlib
from typing import BinaryIO, Iterable, Mapping, cast
from dataclasses import dataclass

import collada
import collada.source
import numpy as np
import numpy.typing as npt

from tqec.computation.cube import Port, CubeKind, YCube, ZXCube
from tqec.computation.pipe import PipeKind
from tqec.exceptions import TQECException
from tqec.interop.color import DEFAULT_FACE_COLORS, RGBA
from tqec.position import FloatPosition3D, Position3D, SignedDirection3D
from tqec.computation.block_graph import BlockGraph, BlockKind
from tqec.interop.geometry import (
    Face,
    FaceKind,
    BlockGeometries,
)
from tqec.scale import round_or_fail


ASSET_AUTHOR = "TQEC Community"
ASSET_AUTHORING_TOOL_TQEC = "https://github.com/QCHackers/tqec"
ASSET_UNIT_NAME = "inch"
ASSET_UNIT_METER = 0.02539999969303608

MATERIAL_SYMBOL = "MaterialSymbol"


def _block_kind_from_str(string: str) -> BlockKind:
    """Parse a block kind from a string."""
    string = string.upper()
    if "O" in string:
        return PipeKind.from_str(string)
    elif string == "Y":
        return YCube()
    else:
        return ZXCube.from_str(string)


def read_block_graph_from_dae_file(
    filepath: str | pathlib.Path,
    graph_name: str = "",
) -> BlockGraph:
    """Read and construct the block graph from a Collada DAE file.

    Args:
        filepath: The input dae file path.

    Returns:
        The constructed block graph.
    """
    mesh = collada.Collada(str(filepath))
    # Check some invariants about the DAE file
    if mesh.scene is None:
        raise TQECException("No scene found in the DAE file.")
    scene: collada.scene.Scene = mesh.scene
    if not (len(scene.nodes) == 1 and scene.nodes[0].name == "SketchUp"):
        raise TQECException(
            "The <visual_scene> node must have a single child node with the name 'SketchUp'."
        )
    sketchup_node: collada.scene.Node = scene.nodes[0]
    pipe_length: float | None = None
    parsed_cubes: list[tuple[FloatPosition3D, CubeKind]] = []
    parsed_pipes: list[tuple[FloatPosition3D, PipeKind]] = []
    for node in sketchup_node.children:
        if (
            isinstance(node, collada.scene.Node)
            and node.matrix is not None
            and node.children is not None
            and len(node.children) == 1
            and isinstance(node.children[0], collada.scene.NodeNode)
        ):
            instance = cast(collada.scene.NodeNode, node.children[0])
            library_node: collada.scene.Node = instance.node
            kind = _block_kind_from_str(library_node.name)
            transformation = Transformation.from_4d_affine_matrix(node.matrix)
            translation = FloatPosition3D(*transformation.translation)
            if not np.allclose(transformation.rotation, np.eye(3), atol=1e-9):
                raise TQECException(
                    f"There is a non-identity rotation for {kind} block at position {translation}."
                )
            if isinstance(kind, PipeKind):
                pipe_direction = kind.direction
                scale = transformation.scale[pipe_direction.value]
                if pipe_length is None:
                    pipe_length = scale * 2.0
                elif not np.isclose(pipe_length, scale * 2.0, atol=1e-9):
                    raise TQECException("All pipes must have the same length.")
                expected_scale = np.ones(3)
                expected_scale[pipe_direction.value] = scale
                if not np.allclose(transformation.scale, expected_scale, atol=1e-9):
                    raise TQECException(
                        f"Only the dimension along the pipe can be scaled, which is not the case at {translation}."
                    )
                parsed_pipes.append((translation, kind))
            else:
                if not np.allclose(transformation.scale, np.ones(3), atol=1e-9):
                    raise TQECException(
                        f"Cube at {translation} has a non-identity scale."
                    )
                parsed_cubes.append((translation, kind))

    pipe_length = 2.0 if pipe_length is None else pipe_length

    def int_position_before_scale(pos: FloatPosition3D) -> Position3D:
        return Position3D(
            x=round_or_fail(pos.x / (1 + pipe_length)),
            y=round_or_fail(pos.y / (1 + pipe_length)),
            z=round_or_fail(pos.z / (1 + pipe_length)),
        )

    def offset_y_cube_position(pos: FloatPosition3D) -> FloatPosition3D:
        if np.isclose(pos.z - 0.5, np.floor(pos.z), atol=1e-9):
            pos = pos.shift_by(dz=-0.5)
        return FloatPosition3D(pos.x, pos.y, pos.z / (1 + pipe_length))

    # Construct the block graph
    graph = BlockGraph(graph_name)
    for pos, cube_kind in parsed_cubes:
        if isinstance(cube_kind, YCube):
            pos = offset_y_cube_position(pos)
        graph.add_cube(int_position_before_scale(pos), cube_kind)
    port_index = 0
    for pos, pipe_kind in parsed_pipes:
        head_pos = int_position_before_scale(
            pos.shift_in_direction(pipe_kind.direction, -1)
        )
        tail_pos = head_pos.shift_in_direction(pipe_kind.direction, 1)
        if head_pos not in graph:
            graph.add_cube(head_pos, Port(), label=f"Port{port_index}")
            port_index += 1
        if tail_pos not in graph:
            graph.add_cube(tail_pos, Port(), label=f"Port{port_index}")
            port_index += 1
        graph.add_pipe(graph[head_pos], graph[tail_pos], pipe_kind)
    return graph


def write_block_graph_to_dae_file(
    block_graph: BlockGraph,
    file_like: str | pathlib.Path | BinaryIO,
    pipe_length: float = 2.0,
    pop_faces_at_direction: SignedDirection3D | None = None,
    custom_face_colors: Mapping[FaceKind, RGBA] | None = None,
) -> None:
    """Write the block graph to a Collada DAE file.

    Args:
        block_graph: The block graph to write.
        file: The output file path or file-like object that supports binary write.
        pipe_length: The length of the pipe blocks. Default is 2.0.
        pop_faces_at_direction: The direction to pop the faces of the blocks. Default is None.
    """
    base = _BaseColladaData(pop_faces_at_direction, custom_face_colors)
    instance_id = 0

    def scale_position(pos: Position3D) -> FloatPosition3D:
        return FloatPosition3D(*(p * (1 + pipe_length) for p in pos.as_tuple()))

    for cube in block_graph.cubes:
        if cube.is_port:
            continue
        scaled_position = scale_position(cube.position)
        if cube.is_y_cube and block_graph.has_pipe_between(
            cube.position, cube.position.shift_by(dz=1)
        ):
            scaled_position = scaled_position.shift_by(dz=0.5)
        matrix = np.eye(4, dtype=np.float32)
        matrix[:3, 3] = scaled_position.as_tuple()
        pop_faces_at_directions = []
        for pipe in block_graph.pipes_at(cube.position):
            pop_faces_at_directions.append(
                SignedDirection3D(pipe.direction, cube == pipe.u)
            )
        base.add_instance_node(instance_id, matrix, cube.kind, pop_faces_at_directions)
        instance_id += 1
    for pipe in block_graph.pipes:
        head_pos = scale_position(pipe.u.position)
        pipe_pos = head_pos.shift_in_direction(pipe.direction, 1.0)
        matrix = np.eye(4, dtype=np.float32)
        matrix[:3, 3] = pipe_pos.as_tuple()
        scales = [1.0, 1.0, 1.0]
        # We divide the scaling by 2.0 because the pipe's default length is 2.0.
        scales[pipe.direction.value] = pipe_length / 2.0
        matrix[:3, :3] = np.diag(scales)
        base.add_instance_node(instance_id, matrix, pipe.kind)
        instance_id += 1
    base.mesh.write(file_like)


@dataclass(frozen=True)
class LibraryNodeKey:
    """The key to access the library node in the Collada DAE file."""

    kind: BlockKind
    pop_faces_at_directions: frozenset[SignedDirection3D] = frozenset()

    def __str__(self) -> str:
        string = f"{self.kind}"
        if self.pop_faces_at_directions:
            string += " without "
            string += " ".join(str(d) for d in self.pop_faces_at_directions)
        return string


class _BaseColladaData:
    def __init__(
        self,
        pop_faces_at_direction: SignedDirection3D | None = None,
        custom_face_colors: Mapping[FaceKind, RGBA] | None = None,
    ) -> None:
        """The base model template including the definition of all the library
        nodes and the necessary material, geometry definitions."""
        self.mesh = collada.Collada()
        self.geometries = BlockGeometries()

        self.materials: dict[FaceKind, collada.material.Material] = {}
        self.geometry_nodes: dict[Face, collada.scene.GeometryNode] = {}
        self.root_node = collada.scene.Node("SketchUp", name="SketchUp")
        self.library_nodes: dict[LibraryNodeKey, collada.scene.Node] = {}
        self._pop_faces_at_direction: frozenset[SignedDirection3D] = (
            frozenset({pop_faces_at_direction})
            if pop_faces_at_direction
            else frozenset()
        )
        custom_face_colors = (
            dict(custom_face_colors) if custom_face_colors is not None else dict()
        )

        self._face_colors = DEFAULT_FACE_COLORS | custom_face_colors

        self._create_scene()
        self._add_asset_info()
        self._add_materials()

    def _create_scene(self) -> None:
        scene = collada.scene.Scene("scene", [self.root_node])
        self.mesh.scenes.append(scene)
        self.mesh.scene = scene

    def _add_asset_info(self) -> None:
        if self.mesh.assetInfo is None:
            return
        self.mesh.assetInfo.contributors.append(
            collada.asset.Contributor(
                author=ASSET_AUTHOR, authoring_tool=ASSET_AUTHORING_TOOL_TQEC
            ),
        )
        self.mesh.assetInfo.unitmeter = ASSET_UNIT_METER
        self.mesh.assetInfo.unitname = ASSET_UNIT_NAME
        self.mesh.assetInfo.upaxis = collada.asset.UP_AXIS.Z_UP

    def _add_materials(self) -> None:
        """Add all the materials for different faces."""
        for face_type in FaceKind:
            rgba = self._face_colors[face_type].as_floats()
            effect = collada.material.Effect(
                f"{face_type.value}_effect",
                [],
                "lambert",
                diffuse=rgba,
                emission=None,
                specular=None,
                transparent=None,
                ambient=None,
                reflective=None,
                double_sided=True,
            )
            self.mesh.effects.append(effect)

            effect.transparency = None
            material = collada.material.Material(
                f"{face_type.value}_material", f"{face_type.value}_material", effect
            )
            self.mesh.materials.append(material)
            self.materials[face_type] = material

    def _add_face_geometry_node(self, face: Face) -> None:
        if face in self.geometry_nodes:
            return
        # Create geometry
        id_str = f"FaceID{len(self.geometry_nodes)}"
        positions = collada.source.FloatSource(
            id_str + "_positions", face.get_vertices(), ("X", "Y", "Z")
        )
        normals = collada.source.FloatSource(
            id_str + "_normals", face.get_normal_vectors(), ("X", "Y", "Z")
        )

        geom = collada.geometry.Geometry(
            self.mesh, id_str, id_str, [positions, normals]
        )
        input_list = collada.source.InputList()
        input_list.addInput(0, "VERTEX", "#" + positions.id)
        input_list.addInput(1, "NORMAL", "#" + normals.id)
        triset = geom.createTriangleSet(
            Face.get_triangle_indices(), input_list, MATERIAL_SYMBOL
        )
        geom.primitives.append(triset)
        self.mesh.geometries.append(geom)
        # Create geometry node
        inputs = [("UVSET0", "TEXCOORD", "0")]
        material = self.materials[face.kind]
        geom_node = collada.scene.GeometryNode(
            geom, [collada.scene.MaterialNode(MATERIAL_SYMBOL, material, inputs)]
        )
        self.geometry_nodes[face] = geom_node

    def _add_library_node(
        self,
        block_kind: BlockKind,
        pop_faces_at_directions: Iterable[SignedDirection3D] = (),
    ) -> LibraryNodeKey:
        pop_faces_at_directions = (
            frozenset(pop_faces_at_directions) | self._pop_faces_at_direction
        )
        key = LibraryNodeKey(block_kind, pop_faces_at_directions)
        if key in self.library_nodes:
            return key
        faces = self.geometries.get_geometry(block_kind, pop_faces_at_directions)
        for face in faces:
            self._add_face_geometry_node(face)
        children = [self.geometry_nodes[face] for face in faces]
        key_str = str(key)
        node = collada.scene.Node(key_str, children, name=str(key.kind))
        self.mesh.nodes.append(node)
        self.library_nodes[key] = node
        return key

    def add_instance_node(
        self,
        instance_id: int,
        transform_matrix: npt.NDArray[np.float32],
        block_kind: BlockKind,
        pop_faces_at_directions: Iterable[SignedDirection3D] = (),
    ) -> None:
        """Add an instance node to the root node."""
        key = self._add_library_node(block_kind, pop_faces_at_directions)
        child_node = collada.scene.Node(
            f"ID{instance_id}",
            name=f"instance_{instance_id}",
            transforms=[collada.scene.MatrixTransform(transform_matrix.flatten())],
        )
        point_to_node = self.library_nodes[key]
        instance_node = collada.scene.NodeNode(point_to_node)
        child_node.children.append(instance_node)
        self.root_node.children.append(child_node)


@dataclass(frozen=True)
class Transformation:
    """Transformation data class to store the translation, scale, rotation, and
    the composed affine matrix.

    For the reference of the transformation matrix, see https://en.wikipedia.org/wiki/Transformation_matrix.

    Attributes:
        translation: The length-3 translation vector.
        scale: The length-3 scaling vector, which is the scaling factor along each axis.
        rotation: The 3x3 rotation matrix.
        affine_matrix: The 4x4 affine matrix composed of the translation, scaling, and rotation.
    """

    translation: npt.NDArray[np.float32]
    scale: npt.NDArray[np.float32]
    rotation: npt.NDArray[np.float32]
    affine_matrix: npt.NDArray[np.float32]

    @staticmethod
    def from_4d_affine_matrix(mat: npt.NDArray[np.float32]) -> Transformation:
        translation = mat[:3, 3]
        scale = np.linalg.norm(mat[:3, :3], axis=1)
        rotation = mat[:3, :3] / scale[:, None]
        return Transformation(translation, scale, rotation, mat)

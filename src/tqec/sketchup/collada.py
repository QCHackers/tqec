"""Handling interoperation with Collada DAE files."""

from __future__ import annotations

import pathlib
import typing as ty
from dataclasses import dataclass

import collada
import collada.source
import numpy as np
import numpy.testing as npt

from tqec.exceptions import TQECException
from tqec.sketchup.geometry import Face, FaceType, load_library_block_geometries
from tqec.sketchup.block_graph import (
    Position3D,
    CubeType,
    PipeType,
    BlockType,
    BlockGraph,
    parse_block_type_from_str,
)

LIGHT_RGBA = (1.0, 1.0, 1.0, 1.0)
DARK_RGBA = (0.1176470588235294, 0.1176470588235294, 0.1176470588235294, 1.0)
YELLOW_RGBA = (1.0, 1.0, 0.396078431372549, 1.0)

ASSET_AUTHOR = "TQEC Community"
ASSET_AUTHORING_TOOL_TQEC = "TQEC Python Package"
ASSET_AUTHORING_TOOL_SKETCHUP = "SketchUp 8.0.15158"
ASSET_UNIT_NAME = "inch"
ASSET_UNIT_METER = 0.02539999969303608

MATERIAL_SYMBOL = "MaterialSymbol"


_FloatPosition = tuple[float, float, float]


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
    uniform_pipe_scale: float | None = None
    parsed_cubes: list[tuple[_FloatPosition, CubeType]] = []
    parsed_pipes: list[tuple[_FloatPosition, CubeType]] = []
    for node in sketchup_node.children:
        if (
            isinstance(node, collada.scene.Node)
            and node.matrix is not None
            and node.children is not None
            and len(node.children) == 1
            and isinstance(node.children[0], collada.scene.NodeNode)
        ):
            instance_block = ty.cast(collada.scene.NodeNode, node.children[0])
            # Get block type
            library_block: collada.scene.Node = instance_block.node
            block_type = parse_block_type_from_str(library_block.name)
            # Get instance transformation
            transformation = Transformation.from_4d_affine_matrix(node.matrix)
            translation: _FloatPosition = tuple(transformation.translation)
            # NOTE: Currently rotation is not allowed
            if not np.allclose(transformation.rotation, np.eye(3), atol=1e-9):
                raise TQECException(
                    f"There is a non-identity rotation for {block_type.value} block at position {translation}."
                )
            if isinstance(block_type, PipeType):
                scale_index = block_type.direction.axis_index
                scale = transformation.scale[block_type.direction.axis_index]
                if uniform_pipe_scale is None:
                    uniform_pipe_scale = scale * 2.0
                elif not np.isclose(uniform_pipe_scale, scale * 2.0, atol=1e-9):
                    raise TQECException("All the pipes must have the same scaling.")
                expected_scale = np.ones(3)
                expected_scale[scale_index] = scale
                if not np.allclose(transformation.scale, expected_scale, atol=1e-9):
                    raise TQECException(
                        "Only the dimension along the connector can be scaled."
                    )
                parsed_pipes.append((translation, block_type))
            elif not np.allclose(transformation.scale, np.ones(3), atol=1e-9):
                raise TQECException("Scaling of cubes is not allowed.")
            else:
                parsed_cubes.append((translation, block_type))
        else:
            raise TQECException(
                "All the children of the 'SketchUp' node must have attributes like the following example:\n"
                "<node id='ID2' name='instance_0'>\n"
                "    <matrix>1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1</matrix>\n"
                "    <instance_node url='#ID3' />\n"
                "</node>\n"
            )

    def int_position_before_scale(pos: _FloatPosition) -> Position3D:
        int_pos_before_scale = []
        for p in pos:
            p_before_scale = p / (1 + uniform_pipe_scale)
            if not np.isclose(p_before_scale, round(p_before_scale), atol=1e-9):
                raise TQECException("The position must be integers before scaling.")
            int_pos_before_scale.append(int(round(p_before_scale)))
        return Position3D(*int_pos_before_scale)

    # Construct the block graph
    graph = BlockGraph(graph_name)
    for pos, cube_type in parsed_cubes:
        graph.add_cube(int_position_before_scale(pos), cube_type)
    for pos, pipe_type in parsed_pipes:
        pipe_direction_idx = pipe_type.direction.axis_index
        scaled_src_pos_list = list(pos)
        scaled_src_pos_list[pipe_direction_idx] -= 1
        src_pos = int_position_before_scale(tuple(scaled_src_pos_list))
        dst_pos_list = list(src_pos.as_tuple())
        dst_pos_list[pipe_direction_idx] += 1
        dst_pos = Position3D(*dst_pos_list)
        if src_pos not in graph:
            graph.add_cube(src_pos, CubeType.VIRTUAL)
        if dst_pos not in graph:
            graph.add_cube(dst_pos, CubeType.VIRTUAL)
        graph.add_pipe(src_pos, dst_pos, pipe_type)
    return graph


def write_block_graph_to_dae_file(
    block_graph: BlockGraph,
    filepath: str | pathlib.Path,
    pipe_length: float = 2.0,
) -> None:
    """Write the block graph to a Collada DAE file.

    Args:
        block_graph: The block graph to write.
        filepath: The output file path.
        pipe_length: The length of the pipe blocks. Default is 2.0.
    """
    base = _load_base_collada_data()
    instance_id = 0

    def scale_position(pos: tuple[int, int, int]) -> tuple[float, float, float]:
        return tuple(p * (1 + pipe_length) for p in pos)

    for cube in block_graph.cubes:
        if cube.is_virtual:
            continue
        scaled_position = scale_position(cube.position.as_tuple())
        matrix = np.eye(4, dtype=np.float_)
        matrix[:3, 3] = scaled_position
        base.add_instance_node(instance_id, matrix, cube.cube_type)
        instance_id += 1
    for pipe in block_graph.pipes:
        src_pos = scale_position(pipe.u.position.as_tuple())
        pipe_pos = list(src_pos)
        pipe_pos[pipe.direction.axis_index] += 1.0
        matrix = np.eye(4, dtype=np.float_)
        matrix[:3, 3] = pipe_pos
        scales = [1.0, 1.0, 1.0]
        # We divide the scaling by 2.0 because the pipe's default length is 2.0.
        scales[pipe.direction.axis_index] = pipe_length / 2.0
        matrix[:3, :3] = np.diag(scales)
        base.add_instance_node(instance_id, matrix, pipe.pipe_type)
        instance_id += 1
    base.mesh.write(filepath)


class _BaseColladaData:
    def __init__(
        self,
        mesh: collada.Collada,
        root_node: collada.scene.Node,
        library_node_handles: dict[BlockType, collada.scene.Node],
    ) -> None:
        """The base model template including the definition of all the library nodes and
        the necessary material, geometry definitions."""
        self.mesh = mesh
        self.root_node = root_node
        self.library_node_handles = library_node_handles

    def add_instance_node(
        self, instance_id: int, transform_matrix: np.ndarray, block_type: BlockType
    ) -> None:
        """Add an instance node to the root node."""
        child_node = collada.scene.Node(
            f"ID{instance_id}",
            name=f"instance_{instance_id}",
            transforms=[collada.scene.MatrixTransform(transform_matrix.flatten())],
        )
        point_to_node = self.library_node_handles[block_type]
        instance_node = collada.scene.NodeNode(point_to_node)
        child_node.children.append(instance_node)
        self.root_node.children.append(child_node)


def _create_lambert_effect(
    id_str: str, rgba: tuple[float, float, float, float]
) -> collada.material.Effect:
    effect = collada.material.Effect(
        id_str,
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
    effect.transparency = None
    return effect


def _add_asset_info(mesh: collada.Collada) -> None:
    if mesh.assetInfo is None:
        return
    mesh.assetInfo.contributors.extend(
        [
            collada.asset.Contributor(
                author=ASSET_AUTHOR, authoring_tool=ASSET_AUTHORING_TOOL_TQEC
            ),
            collada.asset.Contributor(authoring_tool=ASSET_AUTHORING_TOOL_SKETCHUP),
        ]
    )
    mesh.assetInfo.unitmeter = ASSET_UNIT_METER
    mesh.assetInfo.unitname = ASSET_UNIT_NAME
    mesh.assetInfo.upaxis = collada.asset.UP_AXIS.Z_UP


def _add_face_geometry_node(
    mesh: collada.Collada,
    face: Face,
    materials: dict[FaceType, collada.material.Material],
    geom_node_dict: dict[Face, collada.scene.GeometryNode],
) -> None:
    """Note: currently we completely ignore the normals."""
    if face in geom_node_dict:
        return
    # Create geometry
    id_str = f"FaceID{len(geom_node_dict)}"
    vert_src = collada.source.FloatSource(
        id_str + "_verts", face.get_vertices(), ("X", "Y", "Z")
    )
    geom = collada.geometry.Geometry(mesh, id_str, id_str, [vert_src])
    input_list = collada.source.InputList()
    input_list.addInput(0, "VERTEX", "#" + vert_src.id)
    triset = geom.createTriangleSet(
        Face.get_triangle_indices(), input_list, MATERIAL_SYMBOL
    )
    geom.primitives.append(triset)
    mesh.geometries.append(geom)
    # Create geometry node
    inputs = [("UVSET0", "TEXCOORD", "0")]
    material = materials[face.face_type]
    geom_node = collada.scene.GeometryNode(
        geom, [collada.scene.MaterialNode(MATERIAL_SYMBOL, material, inputs)]
    )
    geom_node_dict[face] = geom_node


def _load_base_collada_data() -> _BaseColladaData:
    mesh = collada.Collada()
    # Add asset info
    _add_asset_info(mesh)
    # Add effects(light <--> Z, dark <--> X, yellow <--> H)
    light_effect = _create_lambert_effect("light_effect", LIGHT_RGBA)
    dark_effect = _create_lambert_effect("dark_effect", DARK_RGBA)
    yellow_effect = _create_lambert_effect("yellow_effect", YELLOW_RGBA)
    mesh.effects.extend([light_effect, dark_effect, yellow_effect])
    # Add materials
    light_material = collada.material.Material(
        "light_material", "light_material", light_effect
    )
    dark_material = collada.material.Material(
        "dark_material", "dark_material", dark_effect
    )
    yellow_material = collada.material.Material(
        "yellow_material", "yellow_material", yellow_effect
    )
    materials = {
        FaceType.X: dark_material,
        FaceType.Z: light_material,
        FaceType.H: yellow_material,
    }
    mesh.materials.extend([light_material, dark_material, yellow_material])
    # Add geometries
    geom_node_dict: dict[Face, collada.scene.GeometryNode] = {}
    library_geometry = load_library_block_geometries()
    for block_type, faces in library_geometry.items():
        for face in faces:
            _add_face_geometry_node(mesh, face, materials, geom_node_dict)
    # Add library nodes
    node_handles: dict[BlockType, collada.scene.Node] = {}
    for block_type, faces in library_geometry.items():
        children = [geom_node_dict[face] for face in faces]
        name = block_type.value
        node = collada.scene.Node(name, children, name=name)
        mesh.nodes.append(node)
        node_handles[block_type] = node

    # Create scene
    root_node = collada.scene.Node("SketchUp", name="SketchUp")
    scene = collada.scene.Scene("scene", [root_node])
    mesh.scenes.append(scene)
    mesh.scene = scene
    return _BaseColladaData(mesh, root_node, node_handles)


@dataclass(frozen=True)
class Transformation:
    translation: npt.NDArray[np.float_]
    scale: npt.NDArray[np.float_]
    rotation: npt.NDArray[np.float_]
    affine_matrix: npt.NDArray[np.float_]

    @staticmethod
    def from_4d_affine_matrix(mat: npt.NDArray[np.float_]) -> "Transformation":
        translation = mat[:3, 3]
        scale = np.linalg.norm(mat[:3, :3], axis=1)
        rotation = mat[:3, :3] / scale[:, None]
        return Transformation(translation, scale, rotation, mat)

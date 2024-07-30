"""Handling interoperation with Collada DAE files."""

from __future__ import annotations

import pathlib
import typing as ty
from dataclasses import dataclass

import collada
import collada.source
import numpy as np

from tqec.exceptions import TQECException
from tqec.sketchup.geometry import Face, FaceType, load_library_block_geometries
from tqec.sketchup.block_graph import CubeType, PipeType, BlockType, BlockGraph

LIGHT_RGBA = (1.0, 1.0, 1.0, 1.0)
DARK_RGBA = (0.1176470588235294, 0.1176470588235294, 0.1176470588235294, 1.0)
YELLOW_RGBA = (1.0, 1.0, 0.396078431372549, 1.0)

ASSET_AUTHOR = "TQEC Community"
ASSET_AUTHORING_TOOL_TQEC = "TQEC Python Package"
ASSET_AUTHORING_TOOL_SKETCHUP = "SketchUp 8.0.15158"
ASSET_UNIT_NAME = "inch"
ASSET_UNIT_METER = 0.02539999969303608

MATERIAL_SYMBOL = "MaterialSymbol"


def write_block_graph_to_dae_file(
    block_graph: BlockGraph,
    filepath: str | pathlib.Path,
    pipe_scaling: float = 2.0,
) -> None:
    """Write the block graph to a Collada DAE file.

    Args:
        block_graph: The block graph to write.
        filepath: The output file path.
        pipe_scaling: The length scaling for the pipe blocks. The length equals to the
            cube's edge length times the scaling factor.
    """
    base = _load_base_collada_data()
    instance_id = 0

    def scale_position(pos: tuple[int, int, int]) -> tuple[float, float, float]:
        return tuple(p * (1 + pipe_scaling) for p in pos)

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
        matrix[:3, 3] = scaled_position
        scales = [1.0, 1.0, 1.0]
        scales[pipe.direction.axis_index] = pipe_scaling
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

from __future__ import annotations

import pathlib
import typing as ty
from dataclasses import dataclass

import collada
import collada.source
import networkx as nx
import numpy as np
import numpy.typing as npt

from tqec.exceptions import TQECException
from tqec.sketchup.block import BlockType, Face, FaceType, load_library_blocks

LIGHT_RGBA = (1, 1, 1, 1)
DARK_RGBA = (0.1176470588235294, 0.1176470588235294, 0.1176470588235294, 1)
YELLOW_RGBA = (1, 1, 0.396078431372549, 1)

ASSET_AUTHOR = "TQEC Community"
ASSET_AUTHORING_TOOL_TQEC = "TQEC Python Package"
ASSET_AUTHORING_TOOL_SKETCHUP = "SketchUp 8.0.15158"
ASSET_UNIT_NAME = "inch"
ASSET_UNIT_METER = 0.02539999969303608

MATERIAL_SYMBOL = "MaterialSymbol"


@dataclass(frozen=True)
class InstancePosition:
    """The position of an instance block in the 3D space."""

    x: float
    y: float
    z: float

    def offset_by(self, dx: float, dy: float, dz: float) -> InstancePosition:
        """Offset the position by (dx, dy, dz)."""
        return InstancePosition(self.x + dx, self.y + dy, self.z + dz)

    def to_tuple(self) -> tuple[float, float, float]:
        """Convert the position to a tuple."""
        return self.x, self.y, self.z

    def norm2(self) -> float:
        """Return the squared norm of the position."""
        return self.x**2 + self.y**2 + self.z**2

    def __eq__(self, other: object) -> bool:
        return isinstance(other, InstancePosition) and all(
            abs(i - j) < 1e-12 for i, j in zip(self.to_tuple(), other.to_tuple())
        )

    def __str__(self) -> str:
        return f"({self.x}, {self.y}, {self.z})"


@dataclass(frozen=True)
class BlockInstance:
    """An instance of a block in the 3D space.

    Attributes:
        id: The unique id of the instance.
        block_type: The type of the block.
        position: The position of the block.
        scale: The scale of the block. The scale is only valid for connector blocks
            and should be non-negative. The length of the connector will be 2 * scale.
    """

    id: int
    block_type: BlockType
    position: InstancePosition
    scale: float = 1.0


class SketchUpModel:
    def __init__(self) -> None:
        """The class to represent a SketchUp model.

        Currently, we only support a single connected component of the model and
        the model is represented as a directed graph. The nodes of the graph are
        the cube instances and the edges are the connector instances. The position
        of the instances can be inferred from the connectivity of the graph.
        """
        self._instance_graph = nx.DiGraph()
        # A monotonic increasing id for instances
        self._instance_id = 0
        self._connector_to_endpoints: dict[int, tuple[int, int]] = {}
        self._root: int | None = None

    @property
    def num_cubes(self) -> int:
        """Return the number of cube instances."""
        return ty.cast(int, self._instance_graph.number_of_nodes())

    @property
    def num_connectors(self) -> int:
        """Return the number of connector instances."""
        return ty.cast(int, self._instance_graph.number_of_edges())

    @property
    def num_instances(self) -> int:
        """Return the total number of instances."""
        return self.num_cubes + self.num_connectors

    @property
    def cube_ids(self) -> list[int]:
        """Return the ids of the cube instances."""
        return sorted(self._instance_graph.nodes)

    def add_cube(self, block_type: BlockType, is_root: bool = False) -> int:
        """Add a cube instance to the model.

        Args:
            block_type: The type of the cube.
            is_root: Whether the cube is the root of the model. The root is the
                reference point of the model and the position of the root will be
                set to (0, 0, 0) when instantiating the model.

        Returns:
            The id of the cube instance
        """
        if block_type.is_connector:
            raise TQECException(
                f"The block type {block_type} is a connector while requiring a cube."
            )
        instance_id = self._instance_id
        if is_root:
            if self._root is not None:
                raise TQECException("The root is already set.")
            self._root = instance_id
        self._instance_graph.add_node(instance_id, block_type=block_type)
        self._instance_id += 1
        return instance_id

    def get_cube(self, cube_id: int) -> BlockType:
        """Return the type of the cube.

        Args:
            cube_id: The id of the cube instance.
        """
        return ty.cast(BlockType, self._instance_graph.nodes[cube_id]["block_type"])

    def add_connector(
        self, block_type: BlockType, src: int, dst: int, scale: float = 1.0
    ) -> int:
        """Add a connector instance to the model.

        Args:
            block_type: The type of the connector.
            src: The id of the source cube.
            dst: The id of the destination cube.
            scale: The scale of the connector. The scale should be non-negative.
                The length of the connector will be 2 * scale.

        Returns:
            The id of the connector instance.
        """
        if not block_type.is_connector:
            raise TQECException(
                f"The block type {block_type} is a cube while requiring a connector."
            )
        if not self._instance_graph.has_node(src):
            raise TQECException(f"The source {src} cube does not exist.")
        if not self._instance_graph.has_node(dst):
            raise TQECException(f"The destination {dst} cube does not exist.")
        if self._instance_graph.has_edge(src, dst) or self._instance_graph.has_edge(
            dst, src
        ):
            raise TQECException(
                f"The connection between {src} and {dst} already exists."
            )
        instance_id = self._instance_id
        self._instance_graph.add_edge(
            src, dst, connector_id=instance_id, block_type=block_type, scale=scale
        )
        self._connector_to_endpoints[instance_id] = (src, dst)
        self._instance_id += 1
        return instance_id

    def get_connector(self, connector_id: int) -> tuple[BlockType, float]:
        """Return the type and scale of the connector.

        Args:
            connector_id: The id of the connector instance.

        Returns:
            A tuple of the type and scale of the connector.
        """
        src, dst = self._connector_to_endpoints[connector_id]
        edge = self._instance_graph.edges[src][dst]
        return edge["block_type"], edge["scale"]

    def set_connector_scale(self, connector_id: int, scale: float) -> None:
        """Set the scale of the connector.

        Args:
            connector_id: The id of the connector instance.
            scale: The scale of the connector. The scale should be non-negative.
                The length of the connector will be 2 * scale.
        """
        if scale < 0:
            raise TQECException("The scale must be non-negative.")
        src, dst = self._connector_to_endpoints[connector_id]
        self._instance_graph[src][dst]["scale"] = scale

    def set_scale_for_all_connectors(self, scale: float) -> None:
        """Set the same scale for all the connectors.

        Args:
            scale: The scale of the connectors. The scale should be non-negative.
                The length of the connector will be 2 * scale.
        """
        if scale < 0:
            raise TQECException("The scale must be non-negative.")
        for edge in self._instance_graph.edges:
            self._instance_graph.edges[edge]["scale"] = scale

    def _instantiate_instances(self) -> dict[int, BlockInstance]:
        """Instantiate the instances and infer the positions of the instances."""
        # Currently we assume that the graph is a single connected component
        if not nx.is_connected(self._instance_graph.to_undirected(as_view=True)):
            raise TQECException("The graph is not a single connected component.")
        instances: dict[int, BlockInstance] = {}
        # if the root is not set, we use the first cube as the root
        root = self._root if self._root is not None else self.cube_ids[0]
        instances[root] = BlockInstance(
            root, self.get_cube(root), InstancePosition(0, 0, 0)
        )
        # traverse through the graph to infer the position of instances
        for src, dst, _ in nx.edge_bfs(
            self._instance_graph, [root], orientation="ignore"
        ):
            edge = self._instance_graph[src][dst]
            connector_id = edge["connector_id"]
            connector_type = edge["block_type"]
            scale = edge["scale"]
            if src in instances:
                src_pos = instances[src].position
                connector_pos = src_pos.offset_by(
                    *_get_offset_by_connection(connector_type, False, True, scale)
                )
                dst_pos = src_pos.offset_by(
                    *_get_offset_by_connection(connector_type, True, True, scale)
                )
                if dst in instances:
                    if instances[dst].position != dst_pos:
                        raise TQECException(
                            f"Cannot resolve the position of cube {dst}."
                        )
                else:
                    instances[dst] = BlockInstance(dst, self.get_cube(dst), dst_pos)
            else:
                dst_pos = instances[dst].position
                connector_pos = dst_pos.offset_by(
                    *_get_offset_by_connection(connector_type, False, False, scale)
                )
                src_pos = dst_pos.offset_by(
                    *_get_offset_by_connection(connector_type, True, False, scale)
                )
                if src in instances:
                    if instances[src].position != src_pos:
                        raise TQECException(
                            f"Cannot resolve the position of cube {src}."
                        )
                else:
                    instances[src] = BlockInstance(src, self.get_cube(src), src_pos)
            instances[connector_id] = BlockInstance(
                connector_id, connector_type, connector_pos, scale
            )
        return instances

    def write(self, filepath: str | pathlib.Path) -> None:
        """Write the model to a DAE file.

        Args:
            filepath: The path to the DAE file.
        """
        base_model = _create_base_model()
        instances = sorted(self._instantiate_instances().values(), key=lambda i: i.id)
        for instance in instances:
            matrix = np.eye(4, dtype=np.float_)
            matrix[:3, 3] = instance.position.to_tuple()
            if instance.block_type.is_connector and instance.scale != 1.0:
                scales = _get_scale_tuple(instance.block_type, instance.scale)
                matrix[:3, :3] = np.diag(scales)
            child_node = collada.scene.Node(
                f"ID{instance.id}",
                name=f"instance_{instance.id}",
                transforms=[collada.scene.MatrixTransform(matrix.flatten())],
            )
            point_to_node = base_model.library_node_handles[instance.block_type]
            instance_node = collada.scene.NodeNode(point_to_node)
            child_node.children.append(instance_node)
            base_model.root_node.children.append(child_node)
        base_model.mesh.write(filepath)

    @staticmethod
    def from_dae_file(filepath: str | pathlib.Path) -> "SketchUpModel":
        """Parse a DAE file and return a :class:`SketchUpModel`.

        This function assumes that the DAE file is exported from SketchUp or
        constructed properly with :class:`SketchUpModel`. Currently we assume
        that the all the connectors should be connected to cubes and the formed
        graph should be a single connected component.

        Args:
            filepath: Path to the DAE file.

        Returns:
            A:class:`SketchUpModel` object.
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
        cube_instances: list[BlockInstance] = []
        connector_instances: list[BlockInstance] = []
        for ni, node in enumerate(sketchup_node.children):
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
                block_type = BlockType.from_string(library_block.name)
                # Get instance transformation
                transformation = Transformation.from_4d_affine_matrix(node.matrix)
                position = InstancePosition(*transformation.translation)
                # NOTE: Currently rotation is not allowed
                if not np.allclose(transformation.rotation, np.eye(3), atol=1e-9):
                    raise TQECException(
                        f"There is a non-identity rotation for {block_type.value} block at position {position}."
                    )
                if block_type.is_connector:
                    scale_index = block_type.value.index("o")
                    scale = transformation.scale[scale_index]
                    expected_scale = np.ones(3)
                    expected_scale[scale_index] = scale
                    if not np.allclose(transformation.scale, expected_scale, atol=1e-9):
                        raise TQECException(
                            "Only the dimension along the connector can be scaled."
                        )
                    connector_instances.append(
                        BlockInstance(ni, block_type, position, scale)
                    )
                elif not np.allclose(transformation.scale, np.ones(3), atol=1e-9):
                    raise TQECException("Scaling of cubes is not allowed.")
                else:
                    cube_instances.append(BlockInstance(ni, block_type, position))
            else:
                raise TQECException(
                    "All the children of the 'SketchUp' node must have attributes like the following example:\n"
                    "<node id='ID2' name='instance_0'>\n"
                    "    <matrix>1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1</matrix>\n"
                    "    <instance_node url='#ID3' />\n"
                    "</node>\n"
                )
        # Check the connectivity of the instances
        model = SketchUpModel()
        # select the root node as the one with the smallest norm
        root_pos = min(cube_instances, key=lambda c: c.position.norm2())
        # instance ids will be shuffled when creating the model graph
        id_old_to_new: dict[int, int] = {}
        for connector in connector_instances:
            src_pos, dst_pos = _get_endpoint_cube_positions(connector)
            src = _find_instance_with_position(cube_instances, src_pos)
            dst = _find_instance_with_position(cube_instances, dst_pos)
            if src is None or dst is None:
                raise TQECException(
                    f"There is an endpoint of connector {connector} not filled with a cube."
                )
            for cube in [src, dst]:
                if cube.id in id_old_to_new:
                    continue
                new_id = model.add_cube(cube.block_type, cube.position == root_pos)
                id_old_to_new[cube.id] = new_id
            connector_id = model.add_connector(
                connector.block_type,
                id_old_to_new[src.id],
                id_old_to_new[dst.id],
                connector.scale,
            )
            id_old_to_new[connector.id] = connector_id
        if len(id_old_to_new) != len(cube_instances) + len(connector_instances):
            raise TQECException(
                "The graph from the DAE file is not a single connected component."
            )
        return model


class _BaseSketchUpModel:
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
        shininess=0,
        reflectivity=0,
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


def _create_base_model() -> _BaseSketchUpModel:
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
    library_blocks = load_library_blocks()
    for block in library_blocks:
        for face in block.faces:
            _add_face_geometry_node(mesh, face, materials, geom_node_dict)
    # Add library nodes
    node_handles: dict[BlockType, collada.scene.Node] = {}
    for block in library_blocks:
        children = [geom_node_dict[face] for face in block.faces]
        name = block.block_type.value
        node = collada.scene.Node(name, children, name=name)
        mesh.nodes.append(node)
        node_handles[block.block_type] = node

    # Create scene
    root_node = collada.scene.Node("SketchUp", name="SketchUp")
    scene = collada.scene.Scene("scene", [root_node])
    mesh.scenes.append(scene)
    mesh.scene = scene
    return _BaseSketchUpModel(mesh, root_node, node_handles)


def _get_offset_by_connection(
    connector_type: BlockType,
    for_cube: bool,
    forward: bool,
    scale: float = 1.0,
) -> tuple[float, float, float]:
    offset: list[float] = [0, 0, 0]
    offset_index = connector_type.value.index("o")
    if for_cube:
        if forward:
            offset_val = 1 + 2 * scale
        else:
            offset_val = -1 - 2 * scale
    else:
        if forward:
            offset_val = 1
        else:
            offset_val = -2 * scale
    offset[offset_index] = offset_val
    return (offset[0], offset[1], offset[2])


def _get_scale_tuple(block_type: BlockType, scale: float) -> tuple[float, float, float]:
    if not block_type.is_connector:
        raise TQECException("The block type must be a connector to be scalable.")
    scales: list[float] = [1, 1, 1]
    scale_index = block_type.value.index("o")
    scales[scale_index] = scale
    return (scales[0], scales[1], scales[2])


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


def _get_endpoint_cube_positions(
    connector: BlockInstance,
) -> tuple[InstancePosition, InstancePosition]:
    src_offset: list[float] = [0, 0, 0]
    dst_offset: list[float] = [0, 0, 0]
    offset_index = connector.block_type.value.index("o")
    src_offset[offset_index] = -1
    dst_offset[offset_index] = 2 * connector.scale
    return (
        connector.position.offset_by(*src_offset),
        connector.position.offset_by(*dst_offset),
    )


def _find_instance_with_position(
    instances: list[BlockInstance], position: InstancePosition
) -> BlockInstance | None:
    for instance in instances:
        # NOTE: we use the __eq__ method of InstancePosition
        # to compare the float numbers
        if instance.position == position:
            return instance
    return None

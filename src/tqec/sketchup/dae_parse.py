from __future__ import annotations

import typing as ty
from dataclasses import dataclass
import pathlib

import numpy as np
import collada
import collada.scene as cs

from tqec.exceptions import TQECException

# All predefined valid library nodes
LIBRARY_NODE_TYPES: set[str] = {
    "xoz",
    "zox",
    "ozxh",
    "oxzh",
    "zoxh",
    "ozx",
    "xzx",
    "zxoh",
    "zxz",
    "oxz",
    "xzoh",
    "xozh",
    "zzx",
    "xxz",
    "zxx",
    "xzo",
    "xzz",
    "zxo",
}


@dataclass(frozen=True)
class NodePosition:
    """Position of a node in 3D space.

    The (x,y,z) axis correspond to the (R,G,B) axis in the SketchUp model.
    """

    x: int
    y: int
    z: int

    def __str__(self):
        return f"({self.x}, {self.y}, {self.z})"

    def to_tuple(self):
        return (self.x, self.y, self.z)


@dataclass(frozen=True)
class Node:
    """A node in the SketchUp model with a specific type and position."""

    node_type: str
    position: NodePosition

    def __post_init__(self):
        if self.node_type not in LIBRARY_NODE_TYPES:
            raise TQECException(f"Invalid node type: {self.node_type}.")

    def __str__(self) -> str:
        return f"{self.node_type} at {self.position}"


def parse_dae_file_to_nodes(filepath: str | pathlib.Path) -> list[Node]:
    """Parse a SketchUp exported DAE file and return a list of nodes.

    This function assumes that the DAE file is exported from SketchUp and
    the structure of the DAE file is consistent with the SketchUp export.

    Args:
        filepath: Path to the DAE file.

    Returns:
        A list of Node objects representing the nodes in the SketchUp model.
    """
    mesh = collada.Collada(str(filepath))
    # Check some invariants about the DAE file
    if mesh.scene is None:
        raise TQECException("No scene found in the DAE file.")
    scene: cs.Scene = mesh.scene
    if not (len(scene.nodes) == 1 and scene.nodes[0].name == "SketchUp"):
        raise TQECException(
            "The <visual_scene> node must have a single child node with the name 'SketchUp'."
        )
    sketchup_node: cs.Node = scene.nodes[0]

    constructed_nodes: list[Node] = []
    for node in sketchup_node.children:
        if (
            isinstance(node, cs.Node)
            and node.matrix is not None
            and node.children is not None
            and len(node.children) == 1
            and isinstance(node.children[0], cs.NodeNode)
        ):
            node_position = _get_position_from_transform_matrix(node.matrix)
            instance_node = ty.cast(cs.NodeNode, node.children[0])
            library_node: cs.Node = instance_node.node
            node_type = library_node.name
            if node_type not in LIBRARY_NODE_TYPES:
                raise TQECException(f"Invalid library node type: {node_type}.")
            constructed_nodes.append(Node(node_type, node_position))
        else:
            raise TQECException(
                "All the children of the 'SketchUp' node must have attributes like the following example:\n"
                "<node id='ID2' name='instance_0'>\n"
                "    <matrix>1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1</matrix>\n"
                "    <instance_node url='#ID3' />\n"
                "</node>"
            )
    return constructed_nodes


FLOAT_CAST_INT_TOLERANCE = 1e-12


def _can_cast_to_int_safely(x: float) -> bool:
    return abs(round(x) - x) <= FLOAT_CAST_INT_TOLERANCE


def _get_position_from_transform_matrix(matrix: np.ndarray) -> NodePosition:
    # We only care about the translation component of the transformation matrix
    # so we ignore the rotation, scaling and perspective components.
    x, y, z = matrix[:3, 3]
    for value in (x, y, z):
        if not _can_cast_to_int_safely(value):
            raise TQECException(
                f"The translation component of the transform matrix must be integers, but got {(x, y, z)}."
            )
    return NodePosition(int(round(x)), int(round(y)), int(round(z)))

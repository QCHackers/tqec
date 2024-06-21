from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass
import pathlib

import numpy as np

from tqec.exceptions import TQECException


# All library nodes defined in the template file
LIBRARY_NODE_TYPES = {
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

    Args:
        filepath: Path to the DAE file.

    Returns:
        A list of Node objects representing the nodes in the SketchUp model.
    """
    nodes = []
    tree = ET.parse(filepath)

    _remove_namespace(tree)
    root = tree.getroot()
    existing_library_nodes = _find_library_nodes(root)
    nodes = _construct_nodes(root, None, existing_library_nodes)
    return nodes


def _remove_namespace(tree: ET.ElementTree):
    for elem in tree.iter():
        if "}" in elem.tag:
            elem.tag = elem.tag.split("}", 1)[1]


def _find_library_nodes(root: ET.Element) -> dict[str, str]:
    library_nodes = {}
    if root.tag == "library_nodes":
        for node in root.findall("node"):
            node_id = node.get("id")
            node_name = node.get("name")
            if node_id and node_name:
                library_nodes[node_id] = node_name

    # Recursively search child elements
    for child in root:
        library_nodes.update(_find_library_nodes(child))
    return library_nodes


FLOAT_CAST_INT_TOLERANCE = 1e-12


def _can_cast_to_int_safely(x: float) -> bool:
    return abs(round(x) - x) <= FLOAT_CAST_INT_TOLERANCE


def _get_position_from_matrix_text(matrix_text: str) -> NodePosition:
    matrix = np.fromstring(matrix_text, dtype=float, sep=" ")
    if matrix.size != 16:
        raise TQECException("The transformation matrix must have exactly 16 elements.")
    x, y, z = matrix[3], matrix[7], matrix[11]
    for value in (x, y, z):
        if not _can_cast_to_int_safely(value):
            raise TQECException(
                f"The translation component of the transformation matrix must be integers, but got {(x, y, z)}."
            )
    return NodePosition(int(round(x)), int(round(y)), int(round(z)))


def _construct_nodes(
    root: ET.Element, parent: ET.Element | None, existing_library_nodes: dict[str, str]
) -> list[Node]:
    nodes = []
    # Check for instance_node references
    if root.tag == "instance_node":
        url = root.get("url")
        if url and url.startswith("#"):
            node_id = url[1:]  # Skip the '#' character
            # Find the transformation matrix
            if node_id in existing_library_nodes and parent is not None:
                matrix_element = parent.find("matrix")
                if matrix_element is not None:
                    matrix_text = matrix_element.text
                    if matrix_text is None:
                        raise TQECException(
                            "Matrix text must be specified for a valid instance_node."
                        )
                    matrix_values = _get_position_from_matrix_text(matrix_text)
                    nodes.append(Node(existing_library_nodes[node_id], matrix_values))

    # Recursively search child elements
    for child in root:
        nodes.extend(_construct_nodes(child, root, existing_library_nodes))
    return nodes

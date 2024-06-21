import pathlib

from tqec.sketchup.dae_parse import parse_dae_file_to_nodes, Node

TEST_DIR = pathlib.Path(__file__).parent / "dae_parse_test"


def _group_nodes_by_type(nodes: list[Node]) -> dict[str, list[tuple[int, int, int]]]:
    nodes_by_type = {}
    for node in nodes:
        nodes_by_type.setdefault(node.node_type, []).append(node.position.to_tuple())
    for node_type, positions in nodes_by_type.items():
        nodes_by_type[node_type] = sorted(positions)
    return nodes_by_type


def test_parse_templates_nodes():
    library_nodes = parse_dae_file_to_nodes(TEST_DIR / "templates.dae")
    nodes_by_type = _group_nodes_by_type(library_nodes)
    assert nodes_by_type == {
        "xoz": [(7, 2, 0)],
        "zox": [(9, 2, 0)],
        "ozxh": [(4, 6, 1)],
        "oxzh": [(4, 4, 1)],
        "zoxh": [(9, 5, 1)],
        "ozx": [(4, 2, 0)],
        "xzx": [(2, 2, 0)],
        "zxoh": [(2, 6, 0)],
        "zxz": [(0, 0, 0)],
        "oxz": [(4, 0, 0)],
        "xzoh": [(2, 8, 0)],
        "xozh": [(7, 5, 1)],
        "zzx": [(2, 4, 0)],
        "xxz": [(0, 4, 0)],
        "zxx": [(0, 2, 0)],
        "xzo": [(0, 8, 0)],
        "xzz": [(2, 0, 0)],
        "zxo": [(0, 6, 0)],
    }


def test_parse_cnot_nodes():
    cnot_nodes = parse_dae_file_to_nodes(TEST_DIR / "cnot.dae")
    nodes_by_type = _group_nodes_by_type(cnot_nodes)
    assert nodes_by_type == {
        "oxz": [(1, 3, 6)],
        "zxx": [(0, 3, 3)],
        "zox": [(0, 3, 3)],
        "zxo": [
            (0, 0, 1),
            (0, 0, 4),
            (0, 0, 7),
            (0, 3, 4),
            (3, 3, 1),
            (3, 3, 4),
            (3, 3, 7),
        ],
        "zxz": [
            (0, 0, 0),
            (0, 0, 3),
            (0, 0, 6),
            (0, 0, 9),
            (0, 3, 6),
            (3, 3, 0),
            (3, 3, 3),
            (3, 3, 6),
            (3, 3, 9),
        ],
    }

import packaging.version

import tqec


def test_version() -> None:
    assert (
        packaging.version.Version("0.0.0")
        < packaging.version.parse(symboliq.__version__)
        < packaging.version.Version("1.0.0")
    )

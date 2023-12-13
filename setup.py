import io

from setuptools import find_packages, setup

# This reads the __version__ variable from tqec/_version.py
__version__ = ""
exec(open("tqec/_version.py").read())

name = "tqec"

description = "tqec is a framework for Topological Quantum Error Correction"

# README file as long_description.
long_description = io.open("README.md", encoding="utf-8").read()

# Read in requirements
requirements = open("requirements.txt").readlines()
requirements = [r.strip() for r in requirements]

# Read in dev requirements, installed with 'pip install symbolic[dev]'
dev_requirements = open("dev-requirements.txt").readlines()
dev_requirements = [r.strip() for r in dev_requirements]

symbolic_packages = ["tqec"] + ["tqec." + package for package in find_packages(where="tqec")]

# Sanity check
assert __version__, "Version string cannot be empty"

setup(
    name=name,
    version=__version__,
    url="https://github.com/QCHackers/tqec",
    author="TQEC community",
    author_email="tqec-design-automation@googlegroups.com",
    python_requires=(">=3.11.0"),
    install_requires=requirements,
    extras_require={"dev": dev_requirements},
    license="Apache 2",
    description=description,
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=symbolic_packages,
    package_data={"tqec": ["py.typed"]},
)

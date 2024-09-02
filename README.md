
# tqec

[![Unitary Fund](https://img.shields.io/badge/Supported%20By-UNITARY%20FUND-brightgreen.svg?style=for-the-badge)](https://unitary.fund)

Design automation software tools for Topological Quantum Error Correction

Live endpoint: [https://tqec.app](https://tqec.app)

## Installation

### Backend (Python package)

In order to install the `tqec` package, you can follow the following
instructions.

First, clone this repository on your computer and go in the newly created
folder:

```sh
git clone https://github.com/QCHackers/tqec.git
cd tqec
```

If not already done, create a clean Python virtual environment to avoid any
version clash between packages. You can use the default Python package `venv` to
do that:

```sh
python -m venv venv        # Create a "venv" directory in the current directory.
source venv/bin/activate   # On Unix. For Windows users, use activate.bat
```

You might see a `(venv)` appearing on your terminal prompt, showing that the
virtual environment has been activated.

The next step is to install the package and its dependencies using

```sh
python -m pip install "."
```

If you want to help developing the `tqec` Python package, you should install the development environment by using instead

```sh
python -m pip install ".[dev]"
pre-commit install
```

If no errors happen, the package is installed!

#### Error when installing pycryptosat

On some OSes (basically anything that is not a Linux), `pycryptosat` does not have pre-compiled binaries and `pip` will fallback to compile the package locally. This requires you to have a working C and C++ development environment and in particular a working compiler toolchain.

On MacOS, you might need to add

```sh
export AR=/usr/bin/ar
```

before installing the `tqec` package. See [#311](https://github.com/QCHackers/tqec/issues/311) for more information.

### Frontend

Refer to [this folder](https://github.com/QCHackers/tqec/tree/main/frontend) for instructions.

## Architecture

Refer to [this wiki page](https://github.com/QCHackers/tqec/wiki/TQEC-Architecture) for more information.

## Helpful Links

1. [Google group](https://groups.google.com/g/tqec-design-automation)
2. [Introduction to TQEC](https://docs.google.com/presentation/d/1RufCoTyPFE0EJfC7fbFMjAyhfNJJKNybaixTFh0Qnfg/edit?usp=sharing)
3. [Overview of state of the art 2D QEC](https://docs.google.com/presentation/d/1xYBfkVMpA1YEVhpgTZpKvY8zeOO1VyHmRWvx_kDJEU8/edit?usp=sharing)
4. [Backend deep dive](https://drive.google.com/file/d/1HQEQrln2uVBbs3zbBzrEBm24LDD7PE26/view)
5. [Developer documentation for the `tqec` project](https://qchackers.github.io/tqec/)

## Before you commit

`nbdime` is a great tool for looking at the git diff for jupyter notebooks.

For jupyterlab there is a market place extension which you need to enable first
and that will let you search and install extensions from within jupyter lab. You
can enable the marketplace extension with the following code:

# tqec

Design automation software tools for Topological Quantum Error Correction

## How to install (Python package)

In order to install the `tqec` package, you can follow the following
instructions.

First, clone this repository on your computer and go in the newly created
folder:

```sh
git clone https://github.com/QCHackers/tqec.git

cd tqec
```

Then, create a new Python virtual environment and install the package and its
dependencies:

```sh
conda create -n tqec python==3.11.0

pip install -e .

```

If not already done, create a clean Python virtual environment to avoid any
version clash between packages. You can use the default Python package `venv` to
do that:

```sh
python -m venv venv      # Create a "venv" directory in the current directory.
source venv/bin/activate # On Linux. For MacOS or Windows users, use activate.bat or the MacOS equivalent of that.
```

You might see a `(venv)` appearing on your terminal prompt, showing that the
virtual environment has been activated.

The next step is to install the package and its dependencies using

```sh
python -m pip install "."
```

If you want to run the
[`logical_qubit_memory_experiment.ipynb`](./notebooks/logical_qubit_memory_experiment.ipynb)
notebook, you will also have to install a few other packages:

```sh
python -m pip install ".[dev]"
```

> [!CAUTION] It is advised to follow the above 2-step process for the
> installation. `pip` being quite inefficient, trying to install everything in
> one command will result in a (very) long installation time.

If no errors happen, the package is installed! You can try to launch a jupyter
lab server

```sh
python -m jupyter lab
```

and to run some of the notebooks in the [`notebooks`](./notebooks/) directory.

## Helpful Links

1. [Google group](https://groups.google.com/g/tqec-design-automation)
2. [Introduction to TQEC](https://docs.google.com/presentation/d/1RufCoTyPFE0EJfC7fbFMjAyhfNJJKNybaixTFh0Qnfg/edit?usp=sharing)
3. [Overview of state of the art 2D QEC](https://docs.google.com/presentation/d/1xYBfkVMpA1YEVhpgTZpKvY8zeOO1VyHmRWvx_kDJEU8/edit?usp=sharing)

## Before you commit

`nbstripout` is a great option for clearing the output of the jupyter notebooks.
It can be installed using `pip install nbstripout`. For more info see below in
[before you commit section](#beforecommit)

`nbdime` is a great tool for looking at the git diff for jupyter notebooks.

For jupyterlab there is a market place extension which you need to enable first
and that will let you search and install extensions from within jupyter lab. You
can enable the marketplace extension with the following code:

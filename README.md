# tqec
Design automation software tools for Topological Quantum Error Correction

## How to install (Python package)

In order to install the `tqec` package, you can follow the following instructions.

First, clone this repository on your computer and go in the newly created folder:
```sh
git clone https://github.com/QCHackers/tqec.git
cd tqec
```

If not already done, create a clean Python virtual environment to avoid any version clash between packages. You can use the default Python package `venv` to do that:
```sh
python -m venv venv      # Create a "venv" directory in the current directory.
source venv/bin/activate # On Linux. For MacOS or Windows users, use activate.bat or the MacOS equivalent of that.
```

You might see a `(venv)` appearing on your terminal prompt, showing that the virtual environment has been activated.

The next step is to install the package and its dependencies using
```sh
python -m pip install "."
```

If you want to run the [`logical_qubit_memory_experiment.ipynb`](./notebooks/logical_qubit_memory_experiment.ipynb) notebook, you will also have to install a few other packages:
```sh
python -m pip install ".[dev]"
```

If no errors happen, the package is installed! You can try to launch a jupyter lab server 
```sh
python -m jupyter lab
```
and to run some of the notebooks in the [`notebooks`](./notebooks/) directory.

## Helpful Links
1. [Google group](https://groups.google.com/g/tqec-design-automation)
2. [Introduction to TQEC](https://docs.google.com/presentation/d/1RufCoTyPFE0EJfC7fbFMjAyhfNJJKNybaixTFh0Qnfg/edit?usp=sharing)
3. [Overview of state of the art 2D QEC](https://docs.google.com/presentation/d/1xYBfkVMpA1YEVhpgTZpKvY8zeOO1VyHmRWvx_kDJEU8/edit?usp=sharing)

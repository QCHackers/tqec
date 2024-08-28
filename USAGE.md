# Usage

How to use `tqec` to build, scale and simulate error correction codes.

## Preconditions

To run `tqec` you need to:

- (Optional) Install SketchUp freeware version 8 (see [here](https://google-sketchup.en.lo4d.com/download)), only available on Windows. Be sure to install the correct version. The [online version](https://www.sketchup.com/en/products/sketchup-for-web) of SketchUp do not offer `.dae` format export for free. This is used for building 3d models of the computation you want to do.
- Install the `tqec` library, see the [readme](./README.md). `tqec` detects observables, scales up your error correction codes and runs the simulation by interfacing with [`stim`](https://github.com/quantumlib/stim).

## Intended workflow

The simulation of an error correction code consists of the steps below.
Steps 2 and 3 are automated by `tqec`.

### 1. Define the base model 

You can define the base model using two different methods: via SketchUp and directly in Python.

#### Using SketchUp

If you have SketchUp installed, you can start by making a copy of either [./notebooks/assets/clean_exportable_template.skp](./notebooks/assets/clean_exportable_template.skp) or [./notebooks/assets/clean_exportable_template.dae](./notebooks/assets/clean_exportable_template.dae) file and open this copy in SketchUp to build your computation.

When the computation is complete, delete everything except the model you just created and save the computation in `.dae` format.

You can check that the `tqec` tool is able to correctly read your SketchUp `.dae` export using the `dae2observables` command line.

#### Using Python

The Python method is described in [./notebooks/sketchup_demo.ipynb](./notebooks/sketchup_demo.ipynb). It requires to describe using the `tqec` library and Python code the SketchUp model.

Example:
```py
from tqec.sketchup import ZXGraph, Position3D, NodeType, BlockGraph

# Define the computation
example_zx_graph = ZXGraph("Example ZX Graph")
example_zx_graph.add_z_node(Position3D(0, 0, 0))
example_zx_graph.add_z_node(Position3D(0, 0, 1))
example_zx_graph.add_edge(Position3D(0, 0, 0), Position3D(0, 0, 1))

# Draw using matplotlib:
example_zx_graph.draw()

# Not working at the moment, but exports to BlockGraph structure
# that represents a SketchUp computation.
example_block_graph = example_zx_graph.to_block_graph("Example Block Graph")

# If in a Jupyter Notebook, display interactively the SketchUp computation.
example_block_graph.display()

# Export to a file.
example_block_graph.to_dae_file("example.dae", pipe_length=1.0)
```

### 2. Check the model

You can use the `tqec_check_dae` command line tool to check if your `.dae` file is correctly read and understood by the `tqec` library. The `tqec_check_dae` should be installed alongside the `tqec` library and can be used using
```sh
tqec_check_dae [filename]
```

### 3. Observables

#### Getting `AbstractObservable` instances in Python

Once you have a `BlockGraph` instance representing your computation (see code snippet in [Define the base model > Using Python](#using-python) section), you can recover `AbstractObservable` instances representing all the observables found by `tqec` using:

```py
block_graph = # See code in previous section
observables = block_graph.get_abstract_observables()
```

These `AbstractObservable` instance can then be forwarded to the `tqec` library to add your 

#### Visualizing observables

You can use the `dae2observables` command line tool to have a look at the observable that can be automatically found.

The `dae2observables` command line tool should be installed alongside the `tqec` library. It accepts a few options described below:
```
>>> dae2observables --help
usage: dae2observables [-h] [--out-dir OUT_DIR] dae_file

Takes a .dae file in and list all the observables that has been found.

positional arguments:
  dae_file           A valid .dae file representing a computation.

options:
  -h, --help         show this help message and exit`
  --out-dir OUT_DIR  An optional argument providing the directory in which to export PNG images representing the
                     observables found.
```

Providing a `.dae` file without an output directory:
```
>>> dae2observables ./notebooks/assets/clean_exportable_cnot.dae 
Found 3 correlation surfaces. Please provide an output directory by using the '--out-dir' argument to visualize them.
```

Providing a `.dae` file with an output directory:
```
>>> dae2observables ./notebooks/assets/clean_exportable_cnot.dae --out-dir ./test
Saving correlation surface number 0 to '/workspaces/tqec/test/0.png'.
Saving correlation surface number 1 to '/workspaces/tqec/test/1.png'.
Saving correlation surface number 2 to '/workspaces/tqec/test/2.png'.
```
with the following images being added to the folder provided with `--out-dir`:
![0](https://github.com/user-attachments/assets/24fe2c9c-26a7-48b3-b982-a24ea0803308)
![1](https://github.com/user-attachments/assets/afe88d8f-97cf-477f-b687-0041ccb0014f)
![2](https://github.com/user-attachments/assets/84d6a21b-1b48-490c-b0fd-24268fabec7e)


3. Convert the modeled instance to a generic model
	- Find possible observables to investigate
	- Generate a scalable computation

4. Transform the computation to an executable `stim` circuit
	- build scalable version of various sizes
	- build scalable observables
	- find detectors
	- create `stim` files

5. Run the simulations, repeat for multiple different parameters and investigate interesting areas.

## Current state

This section explains the current state of the above pipline.
Currently no cli commands are exposed.

### Model Definition

Conversion of SketchUp models has to be done in code. 
See the [SketchUp demo](./notebooks/sketchup_demo.ipynb) for converting `.dae` to `BlockGraph` and `ZXGraph` structures.

Additionally, the above notebook also contains instructions how to programmatically define the model.

### Conversion

Observables can be found using `find_correlation_subgraphs()` on the defined models.
Currently, there is no way to directly convert a 3d structure to multiple layers of 2d computation.

### Scaling

Automatic scaling can be achieved programmatically, circuits can be executed through the `stim` python interface.
For an example, refer to the [memory experiment](./notebooks/logical_qubit_memory_experiment.ipynb).

## Todos:

- Examples folder where we have an end to end example
- Fix end-to-end example including
	- .dae input
	- Show observables (according to structure)
	- show computation (as executed)
	- show plots (multiple combinations)
- Specify how to select / re-simulate specific areas

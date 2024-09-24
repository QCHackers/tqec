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

You can either build the model directly with `BlockGraph` or build a simple ZX-diagram using `ZXGraph` then convert it into a `BlockGraph`.

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

#### Check the model

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

These `AbstractObservable` instance can then be forwarded to the `tqec` library to be used in simulations.

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

### 3. Compile the `BlockGraph` and generate circuits

To get the circuits for simulating the computation, you need to compile your `BlockGraph` into a `CompiledGraph`, which can be used to generate scalable circuits.
Then you can generate the `stim.Circuit` with different scales for simulation:

```python
compiled_graph = compile_block_graph(block_graph)
# Generate circuits with code distance 3, 5, 7
circuits = [
  compiled_graph.generate_stim_circuit(k, observables="auto")
  for k in range(1, 4)
]
```

Note that you can specify the specific observables to be included by passing the `AbstractObservable`s as a parameter or just
let the library construct all of the possible observables for you. The possible minimal set of detectors will be constructed
automatically.

NOTE: the scalable detector automation approach is still work in process. You can disable it in `generate_stim_circuit` by setting
`detection_region=None`. And post-process the circuit to add the detectors with `annotate_detectors_automatically`.

### 4. Run the simulation and collect data

Now you can run the simulation with the circuits using sampling tools like `sinter` and collect the data for further analyzing.


## Todos:

- Scalable approach to construct detectors automatically based on `CompiledGraph`. And the structure of a `CompiledGraph` may be changed
further for this purpose.

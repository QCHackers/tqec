# Usage

How to use `tqec` to build, scale and simulate error correction codes.

## Preconditions

To run `tqec` you need to:
- (Optional) Install SketchUp version 8, requires Windows.
	This is used for building 3d models of the computation you want to do.
- Install the `tqec` library, see the [readme](./README.md).
	`tqec` detects observables, scales up your error correction codes and runs the simulation by interfacing with [`stim`](https://github.com/quantumlib/stim).

## Intended workflow

The simulation of an error correction code consists of the steps below.
Steps 2 and 3 are automated by `tqec`.

1. Define the base model with one of two ways
	- SketchUp:  build a model in SketchUp, export it to  a `.dae` file, and  import in `tqec` using `pycollada`.
	- Python: build model programmatically in `tqec`

2. Convert the modeled instance to a generic model
	- Find possible observables to investigate
	- Generate a scalable computation

3. Transform the computation to an executable `stim` circuit
	- build scalable version of various sizes
	- build scalable observables
	- find detectors
	- create `stim` files

4. Run the simulations, repeat for multiple different parameters and investigate interesting areas.

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

# Usage

How to use this tool.

## Preconditions

- Sketchup version 8
- Install Library, see

## What do we want to do

Simulate an error correction do

1. Define the base model
a) Sketchup -> build a model -> export do `.dae` import using pycollada
b) python -> build model

2. Model should look like an abstrtact model
-> Need to find observables

3. Tranform this to a stim circuit
- build scalable version
- build scalable observables
- find detectors
- create stim files

4. Repeat for multiple different parameters

## Current state

### Dae Conversion

Currently no cli command is exposed, has to be used directly. See `./notebooks/sketchup_demo.ipynb` for converting `.dae` to `Blockgrahps` and `ZXGraph`

-

### Scaling

See `logical_qubit_memory_experiment`

## Todos:

- Examples folder where we have an end to end example
- Fix end-to-end example including
	- .dae input
	- Show observables (according to structure)
	- show computation (as executed)
	- show plots ()
- Specify how to select / resimulate
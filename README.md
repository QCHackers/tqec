
# tqec

[![Unitary Fund](https://img.shields.io/badge/Supported%20By-UNITARY%20FUND-brightgreen.svg?style=for-the-badge)](https://unitary.fund)

Design automation software tools for Topological Quantum Error Correction

## Installation

```sh
python -m pip install git+https://github.com/QCHackers/tqec.git
```

For a more in-depth explanation, see the [installation procedure](https://qchackers.github.io/tqec/installation.html).

## Quick start

Download the example file [logical_cnot.dae](https://github.com/QCHackers/tqec/tree/main/docs/media/quick_start/logical_cnot.dae).

You can generate `stim.Circuit` instances representing that computation using

```py
from tqec import (
    BlockGraph, compile_block_graph, annotate_detectors_automatically,
)
from tqec.noise_models import NoiseModel

block_graph = BlockGraph.from_dae_file("logical_cnot.dae")
observables, _ = block_graph.get_abstract_observables()
compiled_computation = compile_block_graph(block_graph, observables=[observables[1]])

circuit = compiled_computation.generate_stim_circuit(
    # Can be changed to whatever value you want. Large values will
    # take a lot of time.
    k=2,
    # The noise applied and noise levels can be changed.
    noise_model=NoiseModel.uniform_depolarizing(0.001),
)
circuit_with_detectors = annotate_detectors_automatically(circuit)
print(circuit_with_detectors)
```

See the [quick start tutorial](https://qchackers.github.io/tqec/quick_start.html) for a
more in-depth explanation.

## Contributing

Pull requests and issues are more than welcomed!

See the [contributing page](https://qchackers.github.io/tqec/contributing.html) for specific instructions to start contributing.

## Helpful Links

1. [Google group](https://groups.google.com/g/tqec-design-automation)
2. [Developer documentation for the `tqec` project](https://qchackers.github.io/tqec/)
3. [Introduction to TQEC](https://docs.google.com/presentation/d/1RufCoTyPFE0EJfC7fbFMjAyhfNJJKNybaixTFh0Qnfg/edit?usp=sharing)
4. [Overview of state of the art 2D QEC](https://docs.google.com/presentation/d/1xYBfkVMpA1YEVhpgTZpKvY8zeOO1VyHmRWvx_kDJEU8/edit?usp=sharing)
5. [Backend deep dive](https://drive.google.com/file/d/1HQEQrln2uVBbs3zbBzrEBm24LDD7PE26/view)

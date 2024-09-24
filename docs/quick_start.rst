Quick start using ``tqec``
==========================

1. Define your computation
--------------------------

The first step should be to define the error-corrected computation you want
to implement. For the sake of simplicity, we will take an error-corrected CNOT
implementation that has been defined using SketchUp and available at
:download:`media/quick_start/clean_exportable_cnot.dae <./media/quick_start/clean_exportable_cnot.dae>`.

.. only:: builder_html

    You can also interactively visualise the CNOT implementation below.

    .. raw:: html

        <iframe
        src="_static/media/quick_start/cnot_sketchup.html"
        title="Interactive visualisation of an error-corrected topological CNOT implementation"
        width=100%
        height=500
        ></iframe>

2. Import your computation
--------------------------

In order to use the computation with the ``tqec`` library you need to import it
using ``tqec.BlockGraph``:

.. code-block:: python

    from tqec import BlockGraph

    block_graph = BlockGraph.from_dae_file("clean_exportable_cnot.dae")

3. Choose the observable(s) of interest
---------------------------------------

The ``tqec`` library can automatically search for valid observables in the
imported computation. To get a list of all the valid observables, you can
use the following code

.. code-block:: python

    observables = block_graph.get_abstract_observables()

Any observable can be plotted using the ``tqec dae2observables`` command line. For our
specific example, the command line

.. code-block:: bash

    tqec dae2observables --out-dir observables/ clean_exportable_cnot.dae

should populate the ``observables`` directory with 3 ``.png`` images representing the
3 valid observables found.

4. Compile and export the computation
-------------------------------------

In order to get a ``stim.Circuit`` instance, the computation first need to be compiled.

.. code-block:: python

    from tqec import compile_block_graph

    compiled_computation = compile_block_graph(block_graph)

From this compiled computation, the final ``stim.Circuit`` instance can be generated.

.. code-block:: python

    from tqec.noise_models import (
        AfterCliffordDepolarizingNoise, DepolarizingNoiseOnIdlingQubit,
    )

    circuit = compiled_computation.generate_stim_circuit(
        k=2,
        observables=[observables[1]],
        noise_models=[
            AfterCliffordDepolarizingNoise(0.001),
            DepolarizingNoiseOnIdlingQubit(0.001),
        ],
    )

5. Annotate the circuit with detectors
--------------------------------------

For the moment, detectors should be added once the full quantum circuit has been
generated.

.. code-block:: python

    from tqec import annotate_detectors_automatically

    circuit_with_detectors = annotate_detectors_automatically(circuit)


6. Enjoy
--------

The quantum circuit can now be used in simulations using ``stim``.

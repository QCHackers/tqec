Quick start using ``tqec``
==========================

1. Define your computation
--------------------------

The first step should be to define the error-corrected computation you want
to implement. For the sake of simplicity, we will take an error-corrected CNOT
implementation that has been defined using SketchUp and available at
:download:`media/quick_start/logical_cnot.dae <./media/quick_start/logical_cnot.dae>`.

.. only:: builder_html

    You can also interactively visualise the CNOT implementation below.

    .. raw:: html

        <iframe
        src="_static/media/quick_start/logical_cnot.html"
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

    block_graph = BlockGraph.from_dae_file("logical_cnot.dae")

3. Choose the observable(s) of interest
---------------------------------------

The ``tqec`` library can automatically search for valid observables in the
imported computation. To get a list of all the valid observables, you can
use the following code

.. code-block:: python

    observables, _ = block_graph.get_abstract_observables()

Any observable can be plotted using the ``tqec dae2observables`` command line. For our
specific example, the command line

.. code-block:: bash

    tqec dae2observables --out-dir observables/ logical_cnot.dae

should populate the ``observables`` directory with 3 ``.png`` images representing the
3 valid observables found.

4. Compile and export the computation
-------------------------------------

In order to get a ``stim.Circuit`` instance, the computation first need to be compiled.

.. code-block:: python

    from tqec import compile_block_graph

    # You can pick any number of observables from the output of
    # block_graph.get_abstract_observables() and provide them here.
    # In this example, picking only the second observable for demonstration
    # purposes.
    compiled_computation = compile_block_graph(block_graph, observables=[observables[1]])

From this compiled computation, the final ``stim.Circuit`` instance can be generated.

.. code-block:: python

    from tqec.noise_models import NoiseModel

    circuit = compiled_computation.generate_stim_circuit(
        k=2,
        noise_model=NoiseModel.uniform_depolarizing(0.001),
    )

5. Annotate the circuit with detectors
--------------------------------------

For the moment, detectors should be added once the full quantum circuit has been
generated.

.. code-block:: python

    from tqec import annotate_detectors_automatically

    circuit_with_detectors = annotate_detectors_automatically(circuit)

And that's all! You now have a quantum circuit representing the topological
error-corrected implementation of a CNOT gate shown at the beginning of this page.

You can download the circuit in a ``stim`` format here:
:download:`media/quick_start/logical_cnot.stim <./media/quick_start/logical_cnot.stim>`.

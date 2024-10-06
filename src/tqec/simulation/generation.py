import functools
import itertools
from concurrent.futures import ProcessPoolExecutor
from typing import Callable, Iterable, Iterator

import stim

from tqec.circuit.detectors.construction import annotate_detectors_automatically
from tqec.compile.compile import CompiledGraph
from tqec.noise_models.noise_model import NoiseModel


def _parallel_func(
    kp: tuple[int, float],
    *,
    compiled_graph: CompiledGraph,
    noise_model_factory: Callable[[float], NoiseModel],
) -> tuple[stim.Circuit, int, float]:
    k, p = kp
    noise_model = noise_model_factory(p)
    return (
        annotate_detectors_automatically(
            compiled_graph.generate_stim_circuit(k, noise_model)
        ),
        k,
        p,
    )


def generate_stim_circuits_with_detectors(
    compiled_graph: CompiledGraph,
    ks: Iterable[int],
    ps: Iterable[float],
    noise_model_factory: Callable[[float], NoiseModel],
    max_workers: int | None = None,
) -> Iterator[tuple[stim.Circuit, int, float]]:
    """Generate stim circuits in parallel.

    This function generate the `stim.Circuit` instances for all the combinations
    of the given `ks` and `ps` with a noise model that depends on `p` and
    computed with `noise_model_factory`.

    It is equivalent to:

    ```py
    for p in ps:
        for k in ks:
            yield (
                compiled_graph.generate_stim_circuit(k, noise_model_factory(p)), k, p
            )
    ```

    except that the order in which the results are returned is not guaranteed.

    Args:
        compiled_graph: computation to export to `stim.Circuit` instances.
        ks: values of `k` to consider.
        ps: values of `p`, the noise strength, to consider.
        noise_model_factory: a callable that builds a noise model from an input
            strength `p`.
        max_workers: The maximum number of processes that can be used to
            execute the given calls. If None or not given then as many
            worker processes will be created as the machine has processors.

    Yields:
        a tuple containing the resulting circuit, the value of `k` that
        corresponds to the returned circuit and the value of `p` that corresponds
        to the returned circuit.
    """
    with ProcessPoolExecutor(max_workers) as executor:
        yield from executor.map(
            functools.partial(
                _parallel_func,
                compiled_graph=compiled_graph,
                noise_model_factory=noise_model_factory,
            ),
            itertools.product(ks, ps),
        )

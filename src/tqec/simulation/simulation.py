import multiprocessing
from typing import Callable, Iterable, Iterator, Mapping, Sequence

import sinter

from tqec.compile.compile import compile_block_graph
from tqec.compile.specs.base import CubeSpec, SpecRule
from tqec.compile.substitute import (
    DEFAULT_SUBSTITUTION_RULES,
    SubstitutionKey,
    SubstitutionRule,
)
from tqec.computation.block_graph import AbstractObservable, BlockGraph
from tqec.noise_models.noise_model import NoiseModel
from tqec.simulation.generation import generate_sinter_tasks


def start_simulation_using_sinter(
    block_graph: BlockGraph,
    ks: Sequence[int],
    ps: Sequence[float],
    noise_model_factory: Callable[[float], NoiseModel],
    cube_specifications: Mapping[CubeSpec, SpecRule],
    substitution_rules: Mapping[SubstitutionKey, SubstitutionRule] | None = None,
    observables: list[AbstractObservable] | None = None,
    num_workers: int = multiprocessing.cpu_count(),
    progress_callback: Callable[[sinter.Progress], None] | None = None,
    max_shots: int | None = None,
    max_errors: int | None = None,
    decoders: Iterable[str] = ("pymatching",),
    print_progress: bool = False,
    custom_decoders: dict[str, sinter.Decoder | sinter.Sampler] | None = None,
) -> Iterator[list[sinter.TaskStats]]:
    """Helper to run `stim` simulations using `sinter`.

    This function is the preferred entry-point to run `sinter` computations using
    `stim` from circuits generated by `tqec`.

    It remove the need to generate the `stim.Circuit` instances in parallel (due
    to the relative inefficiency of detector annotation at the moment) by
    importing and calling :func:`generate_sinter_tasks`. It also forwards
    several parameters to :func:`sinter.collect`, but without showing in its
    signature arguments that we do not envision using.

    Args:
        block_graph: a representation of the QEC computation to simulate.
        ks: values of the scaling parameter `k` to use in order to generate the
            circuits.
        ps: values of the noise parameter `p` to use to instantiate a noise
            model using the provided `noise_model_factory`.
        noise_model_factory: a callable that is used to instantiate a noise
            model from each of the noise parameters in `ps`.
        cube_specification: a description of the different cubes that are
            used by the provided `block_graph`.
        substitution_rules: a description of the rules that should be applied
            to connect two cubes with a pipe.
        observables: a list of observables to generate statistics for. If
            `None`, all the observables of the provided computation are used.
        num_workers: The number of worker processes to use.
        progress_callback: Defaults to None (unused). If specified, then each
            time new sample statistics are acquired from a worker this method
            will be invoked with the new `sinter.TaskStats`.
        max_shots: Defaults to None (unused). Stops the sampling process
            after this many samples have been taken from the circuit.
        max_errors: Defaults to None (unused). Stops the sampling process
            after this many errors have been seen in samples taken from the
            circuit. The actual number sampled errors may be larger due to
            batching.
        decoders: Defaults to None (specified by each Task). The names of the
            decoders to use on each Task. It must either be the case that each
            Task specifies a decoder and this is set to None, or this is an
            iterable and each Task has its decoder set to None.
        print_progress: When True, progress is printed to stderr while
            collection runs.
        custom_decoders: Named child classes of `sinter.decoder`, that can be
            used if requested by name by a task or by the decoders list.
            If not specified, only decoders with support built into sinter, such
            as 'pymatching' and 'fusion_blossom', can be used.

    Returns:
        a list containing one simulation result (of type
        `list[sinter.TaskStats]`) per provided observable in `observables`.
    """
    if observables is None:
        observables = block_graph.get_abstract_observables()
    if substitution_rules is None:
        substitution_rules = DEFAULT_SUBSTITUTION_RULES

    for i, observable in enumerate(observables):
        if print_progress:
            print(
                f"Generating statistics for observable {i+1}/{len(observables)}",
                end="\r",
            )
        compiled_graph = compile_block_graph(
            block_graph,
            spec_rules=cube_specifications,
            substitute_rules=substitution_rules,
            observables=[observable],
        )
        stats = sinter.collect(
            num_workers=num_workers,
            tasks=generate_sinter_tasks(
                compiled_graph, ks, ps, noise_model_factory, max_workers=num_workers
            ),
            progress_callback=progress_callback,
            max_shots=max_shots,
            max_errors=max_errors,
            decoders=decoders,
            print_progress=print_progress,
            custom_decoders=custom_decoders,
            hint_num_tasks=len(ks) * len(ps),
        )
        yield stats

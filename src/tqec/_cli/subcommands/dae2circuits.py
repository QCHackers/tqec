from __future__ import annotations

import argparse
from pathlib import Path
from typing_extensions import override

from tqec._cli.subcommands.base import TQECSubCommand
from tqec._cli.subcommands.dae2observables import save_correlation_surfaces_to
from tqec.computation.block_graph import BlockGraph
from tqec.compile.compile import compile_block_graph
from tqec import annotate_detectors_automatically


class Dae2CircuitsTQECSubCommand(TQECSubCommand):
    @staticmethod
    @override
    def add_subcommand(
        main_parser: argparse._SubParsersAction[argparse.ArgumentParser],
    ) -> None:
        parser: argparse.ArgumentParser = main_parser.add_parser(
            "dae2circuits",
            description=(
                "Convert a .dae file representing a logical "
                "computation into concrete stim circuits."
            ),
        )
        parser.add_argument(
            "dae_file",
            help="A valid .dae file representing a computation.",
            type=Path,
        )
        parser.add_argument(
            "--out-dir",
            help="Directory to save the generated stim circuits.",
            type=Path,
            required=True,
        )
        parser.add_argument(
            "-k",
            help="The scale factors applied to the circuits.",
            nargs="+",
            type=int,
            required=True,
        )
        parser.add_argument(
            "--obs-include",
            help=(
                "The observable indices to be included in the circuits. "
                "If not provided, all potential observables will be included."
            ),
            nargs="*",
            type=int,
        )
        parser.add_argument(
            "--add-detectors",
            help="Whether to add detectors to the circuits.",
            action="store_true",
        )
        # TODO: add noise models
        parser.set_defaults(func=Dae2CircuitsTQECSubCommand.execute)

    @staticmethod
    @override
    def execute(args: argparse.Namespace) -> None:
        dae_absolute_path: Path = args.dae_file.resolve()
        out_dir: Path = args.out_dir.resolve()
        if not out_dir.exists():
            out_dir.mkdir(parents=True)

        # Construct the block graph from the given .dae file
        block_graph = BlockGraph.from_dae_file(
            dae_absolute_path, graph_name=str(dae_absolute_path.name)
        )

        # Convert to ZX graph and find observables
        zx_graph = block_graph.to_zx_graph()
        correlation_surfaces = zx_graph.find_correlation_subgraphs()
        obs_indices: list[int] = args.obs_include
        if not obs_indices:
            obs_indices = list(range(len(correlation_surfaces)))
        if max(obs_indices) >= len(correlation_surfaces):
            raise ValueError(
                f"Found {len(correlation_surfaces)} observables, but requested indices up to {max(obs_indices)}."
            )

        # Save the plotted observables to a subdirectory
        observable_out_dir = out_dir / "observables"
        observable_out_dir.mkdir(exist_ok=True)
        save_correlation_surfaces_to(
            zx_graph,
            observable_out_dir,
            [correlation_surfaces[i] for i in obs_indices],
        )
        # TODO: avoid recomputing the observables
        abstract_observables = block_graph.get_abstract_observables()

        # Compile the block graph and generate stim circuits
        circuits_out_dir = out_dir / "circuits"
        circuits_out_dir.mkdir(exist_ok=True)
        compiled_graph = compile_block_graph(
            block_graph,
            observables=[abstract_observables[i] for i in obs_indices],
        )
        ks: list[int] = args.k
        add_detectors: bool = args.add_detectors
        for k in ks:
            circuit = compiled_graph.generate_stim_circuit(k)
            if add_detectors:
                circuit = annotate_detectors_automatically(circuit)
            circuit.to_file(circuits_out_dir / f"{k=}.stim")
            print(f"Write circuit to {circuits_out_dir}.")

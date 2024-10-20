from __future__ import annotations

import argparse
import logging
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
import sinter
from typing_extensions import override

from tqec import annotate_detectors_automatically
from tqec._cli.subcommands.base import TQECSubCommand
from tqec._cli.subcommands.dae2observables import save_correlation_surfaces_to
from tqec.compile.compile import compile_block_graph
from tqec.compile.specs.library.css import CSS_BLOCK_BUILDER, CSS_SUBSTITUTION_BUILDER
from tqec.compile.specs.library.zxxz import (
    ZXXZ_BLOCK_BUILDER,
    ZXXZ_SUBSTITUTION_BUILDER,
)
from tqec.gallery import logical_cnot_block_graph
from tqec.noise_models import NoiseModel
from tqec.simulation.plotting.inset import plot_observable_as_inset
from tqec.simulation.simulation import start_simulation_using_sinter


class RunExamplesTQECSubCommand(TQECSubCommand):
    @staticmethod
    @override
    def add_subcommand(
        main_parser: argparse._SubParsersAction[argparse.ArgumentParser],
    ) -> None:
        parser: argparse.ArgumentParser = main_parser.add_parser(
            "run-examples",
            description=(
                "Runs the full pipeline on the CNot example."
                ".dae -> stim circuits and observables -> simulation -> plots"
            ),
        )
        parser.add_argument(
            "--out-dir",
            help="Directory to save the generated outputs.",
            type=Path,
            required=True,
        )
        parser.add_argument(
            "-k",
            help="The scale factors applied to the circuits.",
            nargs="+",
            type=int,
            default=[1, 2, 3, 4],
        )

        parser.add_argument(
            "-p",
            help="The noise leves applied to the simulation.",
            nargs="+",
            type=float,
            default=list(np.logspace(-4, -1, 10)),
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
        parser.add_argument(
            "--generate-only",
            help="Whether to run generation only.",
            action="store_true",
        )
        parser.add_argument(
            "--code-style",
            help="Use the CSS or ZXXZ code style.",
            choices=["css", "zxxz"],
        )
        parser.add_argument(
            "--include-z-basis",
            help="Whether to include the Z basis in the simulation.",
            action="store_true",
        )
        parser.set_defaults(func=RunExamplesTQECSubCommand.execute)

    @staticmethod
    @override
    def execute(args: argparse.Namespace) -> None:
        # Parse args
        logging.info("Parsing arguments.")
        out_dir: Path = args.out_dir.resolve()
        obs_indices: list[int] = args.obs_include
        style: str = args.code_style
        z_basis: bool = args.include_z_basis
        ks: list[int] = args.k
        ps: list[float] = args.p
        add_detectors: bool = args.add_detectors

        # Set up the output directories
        logging.info("Setting up output directories.")
        if not out_dir.exists():
            out_dir.mkdir(parents=True)

        observable_out_dir = out_dir / "observables"
        observable_out_dir.mkdir(exist_ok=True)
        circuits_out_dir = out_dir / "circuits"
        circuits_out_dir.mkdir(exist_ok=True)
        simulations_out_dir = out_dir / "simulations"
        simulations_out_dir.mkdir(exist_ok=True)
        plots_out_dir = out_dir / "plots"
        plots_out_dir.mkdir(exist_ok=True)

        logging.info("Generating CNot block graph and zx graph.")
        block_graph = logical_cnot_block_graph(z_basis)
        zx_graph = block_graph.to_zx_graph()

        # observables to a subdirectory
        logging.info("Find the observables.")
        observables, correlation_surfaces = block_graph.get_abstract_observables()
        if not obs_indices:
            obs_indices = list(range(len(observables)))
        if max(obs_indices) >= len(observables):
            raise ValueError(
                f"Found {len(observables)} observables,"
                + f"but requested indices up to {max(obs_indices)}."
            )

        block_builder = CSS_BLOCK_BUILDER if style == "css" else ZXXZ_BLOCK_BUILDER
        substitution_builder = (
            CSS_SUBSTITUTION_BUILDER if style == "css" else ZXXZ_SUBSTITUTION_BUILDER
        )

        logging.info("Start the simulation, this might take some time.")
        stats = start_simulation_using_sinter(
            block_graph,
            ks,
            ps,
            NoiseModel.uniform_depolarizing,
            block_builder=block_builder,
            substitution_builder=substitution_builder,
            observables=observables,
            num_workers=20,
            max_shots=10_000_000,
            max_errors=5_000,
            decoders=["pymatching"],
            print_progress=True,
        )
        logging.info("Simulation finished.")

        # Store outputs
        logging.info("Write all the outputs...")
        logging.info("Write observables to %s.", observable_out_dir)
        save_correlation_surfaces_to(
            zx_graph,
            observable_out_dir,
            [correlation_surfaces[i] for i in obs_indices],
        )

        logging.info("Write circuits to %s.", circuits_out_dir)
        compiled_graph = compile_block_graph(
            block_graph,
            CSS_BLOCK_BUILDER,
            CSS_SUBSTITUTION_BUILDER,
            observables=[observables[i] for i in obs_indices],
        )
        for k in ks:
            circuit = compiled_graph.generate_stim_circuit(k)
            if add_detectors:
                circuit = annotate_detectors_automatically(circuit)
            circuit.to_file(circuits_out_dir / f"{k=}.stim")

        logging.info("Write plots to %s.", plots_out_dir)
        for i, stat in enumerate(stats):
            basis_str = "Z" if z_basis else "X"
            with open(
                simulations_out_dir
                / f"{style}_logical_cnot_result_{basis_str}_observable_{i}.csv",
                "w+",
                encoding="utf-8",
            ) as stats_file:
                stats_file.write(sinter.CSV_HEADER)
                for sub_stat in stat:
                    stats_file.write(sub_stat.to_csv_line())

            fig, ax = plt.subplots()
            sinter.plot_error_rate(
                ax=ax,
                stats=stat,
                x_func=lambda stat: stat.json_metadata["p"],
                group_func=lambda stat: stat.json_metadata["d"],
            )
            plot_observable_as_inset(ax, zx_graph, correlation_surfaces[i])
            ax.grid(axis="both")
            ax.legend()
            ax.loglog()
            ax.set_title(f"{style.upper()} Logical CNOT Error Rate")
            fig.savefig(
                plots_out_dir
                / f"{style}_logical_cnot_result_{basis_str}_observable_{i}.png"
            )

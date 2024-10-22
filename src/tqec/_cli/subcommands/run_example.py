from __future__ import annotations

import argparse
import logging
from multiprocessing import cpu_count
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import sinter
from typing_extensions import override

from tqec._cli.subcommands.base import TQECSubCommand
from tqec.compile.specs.library.css import CSS_BLOCK_BUILDER, CSS_SUBSTITUTION_BUILDER
from tqec.compile.specs.library.zxxz import (
    ZXXZ_BLOCK_BUILDER,
    ZXXZ_SUBSTITUTION_BUILDER,
)
from tqec.gallery import logical_cnot_block_graph
from tqec.noise_models import NoiseModel
from tqec.simulation.plotting.inset import plot_observable_as_inset
from tqec.simulation.simulation import start_simulation_using_sinter


class RunExampleTQECSubCommand(TQECSubCommand):
    @staticmethod
    @override
    def add_subcommand(
        main_parser: argparse._SubParsersAction[argparse.ArgumentParser],
    ) -> None:
        parser: argparse.ArgumentParser = main_parser.add_parser(
            "run-example",
            description=(
                "Runs the full pipeline on the CNOT example. "
                "block graph -> stim circuits and observables -> simulation -> plots"
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
            help="The noise levels applied to the simulation.",
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
            "--code-style",
            help="Use the CSS or ZXXZ code style.",
            choices=["CSS", "ZXXZ"],
            default="CSS",
        )
        parser.add_argument(
            "--basis",
            help="Which basis to use for simulation.",
            choices=["X", "Z"],
            default="X",
        )
        parser.set_defaults(func=RunExampleTQECSubCommand.execute)

    @staticmethod
    @override
    def execute(args: argparse.Namespace) -> None:
        # Parse args
        logging.info("Parsing arguments.")
        out_dir: Path = args.out_dir.resolve()
        obs_indices: list[int] = args.obs_include
        style: str = args.code_style
        basis_str: str = args.basis
        z_basis: bool = basis_str == "Z"
        ks: list[int] = args.k
        ps: list[float] = args.p

        # Set up the output directories
        logging.info("Setting up output directories.")
        if not out_dir.exists():
            out_dir.mkdir(parents=True)

        simulations_out_dir = out_dir / "simulations"
        simulations_out_dir.mkdir(exist_ok=True)
        plots_out_dir = out_dir / "plots"
        plots_out_dir.mkdir(exist_ok=True)

        logging.info("Generating CNOT block graph and zx graph.")
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

        block_builder = CSS_BLOCK_BUILDER if style == "CSS" else ZXXZ_BLOCK_BUILDER
        substitution_builder = (
            CSS_SUBSTITUTION_BUILDER if style == "CSS" else ZXXZ_SUBSTITUTION_BUILDER
        )

        logging.info("Start the simulation, this might take some time.")
        stats = start_simulation_using_sinter(
            block_graph,
            ks,
            ps,
            NoiseModel.uniform_depolarizing,
            manhattan_radius=2,
            block_builder=block_builder,
            substitution_builder=substitution_builder,
            observables=[observables[i] for i in obs_indices],
            num_workers=cpu_count(),
            max_shots=10_000_000,
            max_errors=5_000,
            decoders=["pymatching"],
            print_progress=True,
        )
        logging.info("Simulation finished.")

        logging.info("Write plots to %s.", plots_out_dir)
        for i, stat in enumerate(stats):
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
            ax.set_title(f"{style} Logical CNOT Error Rate")
            fig.savefig(
                plots_out_dir
                / f"{style}_logical_cnot_result_{basis_str}_observable_{i}.png"
            )

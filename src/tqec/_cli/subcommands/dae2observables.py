from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import cast

import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.axes3d import Axes3D
from typing_extensions import override

from tqec._cli.subcommands.base import TQECSubCommand
from tqec.computation.block_graph import BlockGraph
from tqec.computation.correlation import CorrelationSurface
from tqec.computation.zx_plot import draw_correlation_surface_on, draw_zx_graph_on
from tqec.computation.zx_graph import ZXGraph


class Dae2ObservablesTQECSubCommand(TQECSubCommand):
    @staticmethod
    @override
    def add_subcommand(
        main_parser: argparse._SubParsersAction[argparse.ArgumentParser],
    ) -> None:
        parser: argparse.ArgumentParser = main_parser.add_parser(
            "dae2observables",
            description="Takes a .dae file in and list all the observables that has been found.",
        )
        parser.add_argument(
            "dae_file", help="A valid .dae file representing a computation.", type=Path
        )
        parser.add_argument(
            "--out-dir",
            help="An optional argument providing the directory in which to export images representing the observables found.",
            type=Path,
        )
        parser.set_defaults(func=Dae2ObservablesTQECSubCommand.execute)

    @staticmethod
    @override
    def execute(args: argparse.Namespace) -> None:
        dae_absolute_path: Path = args.dae_file.resolve()
        block_graph = BlockGraph.from_dae_file(
            dae_absolute_path, graph_name=str(dae_absolute_path)
        )
        zx_graph = block_graph.to_zx_graph()
        correlation_surfaces = zx_graph.find_correration_surfaces()

        if args.out_dir is None:
            print(
                f"Found {len(correlation_surfaces)} observables. Please provide an output "
                "directory by using the '--out-dir' argument to visualize them."
            )
        else:
            if not args.out_dir.exists():
                os.makedirs(args.out_dir)
            save_correlation_surfaces_to(zx_graph, args.out_dir, correlation_surfaces)


def save_correlation_surfaces_to(
    zx_graph: ZXGraph, out_dir: Path, correlation_surfaces: list[CorrelationSurface]
) -> None:
    for i, correlation_surface in enumerate(correlation_surfaces):
        fig = plt.figure(figsize=(5, 6))
        ax = cast(Axes3D, fig.add_subplot(111, projection="3d"))
        draw_zx_graph_on(zx_graph, ax)
        draw_correlation_surface_on(correlation_surface, ax)
        fig.tight_layout()
        save_path = (out_dir / f"{i}.png").resolve()
        print(f"Saving correlation surface number {i} to '{save_path}'.")
        fig.savefig(save_path)
        fig.clear()

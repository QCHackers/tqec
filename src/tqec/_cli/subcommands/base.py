from __future__ import annotations

import argparse
from abc import ABC, abstractmethod


class TQECSubCommand(ABC):
    """Interface that should be implemented by subcommands of the tqec CLI."""

    @staticmethod
    @abstractmethod
    def add_subcommand(
        main_parser: argparse._SubParsersAction[argparse.ArgumentParser],
    ) -> None:
        pass

    @staticmethod
    @abstractmethod
    def execute(args: argparse.Namespace) -> None:
        pass

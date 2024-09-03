import argparse

from tqec._cli.subcommands.check_dae import CheckDaeTQECSubCommand
from tqec._cli.subcommands.dae2observables import Dae2ObservablesTQECSubCommand


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="tqec",
        description="The main tqec command-line tool.",
    )
    subparser = parser.add_subparsers(title="subcommands")

    Dae2ObservablesTQECSubCommand.add_subcommand(subparser)
    CheckDaeTQECSubCommand.add_subcommand(subparser)

    args = parser.parse_args()
    args.func(args)

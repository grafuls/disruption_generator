# -*- coding: utf-8 -*-

"""Console script for disruption_generator."""
import asyncio
import asyncssh
import sys
import click
import logging

from . import __version__
from .parsers.experiment_parser import ExperimentParser
from .listener.alistener import Alistener
from .trigger.trigger import Trigger
from os import walk, path

logger = logging.getLogger(__name__)


@click.command()
@click.option(
    "--experiments-path",
    "-e",
    type=click.Path(
        exists=True, file_okay=False, readable=True, resolve_path=True
    ),
    help="Path to experiments yamls",
    default="./experiments/",
)
@click.option(
    "--ssh-host-key",
    "-s",
    type=click.Path(
        exists=True, file_okay=True, readable=True, resolve_path=True
    ),
    help="File with SSH private key to use a server host key",
    default=None,
)
@click.version_option(version=__version__)
def main(experiments_path, ssh_host_key):
    """Console script for disruption_generator."""
    click.echo("!!! DISRUPTION AS A SERVICE !!!")
    click.echo("!!!    USE WITH CAUTION     !!!")
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(execute(experiments_path, ssh_host_key))
    except (OSError, asyncssh.Error) as exc:
        sys.exit("SSH connection failed: " + str(exc))


async def execute(experiments_path, ssh_host_key):
    ssh_host_key = [ssh_host_key] if ssh_host_key else ssh_host_key
    _files = []
    for (dirpath, dirnames, filenames) in walk(experiments_path):
        _files = [
            path.join(dirpath, _file)
            for _file in filenames
            if _file.endswith(".yaml")
        ]
        break  # Gets only root level directory files
    _scenarios = []
    for _file in _files:
        _parser = ExperimentParser(yaml_path=_file)
        scenario = _parser.parse()
        _scenarios.extend(scenario)
    for scenario in _scenarios:
        click.echo("Scenario: %s" % scenario.name)
        alistener = Alistener(scenario.listener.target, ssh_host_key)

        for action in scenario.actions:
            result = await alistener.tail(
                scenario.listener.log, scenario.listener.re, action.timeout
            )

            if result:
                click.echo("Triggering: %s" % action.name)
                trigger = Trigger(action, ssh_host_key)
                try:
                    disruption = getattr(trigger, action.name)
                except AssertionError as err:
                    logger.info(err)
                    return 1
                await disruption()

    return 0


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover

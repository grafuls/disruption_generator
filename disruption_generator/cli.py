# -*- coding: utf-8 -*-

"""Console script for disruption_generator."""
import asyncio
import asyncssh
import sys
import click
import logging.config
import yaml

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
    type=click.Path(exists=True, file_okay=False, readable=True, resolve_path=True),
    help="Path to experiments yamls",
    default="./experiments/",
)
@click.option(
    "--ssh-host-key",
    "-k",
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
    parse_log_config(default_config_file="default_logging.yaml", custom_config_file="custom_config.yaml")
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(execute(experiments_path, ssh_host_key))
    except (OSError, asyncssh.Error) as exc:
        sys.exit("SSH connection failed: " + str(exc))


async def execute(experiments_path, ssh_host_key):
    ssh_host_key = ssh_host_key or [ssh_host_key]
    _files = []
    for (dirpath, dirnames, filenames) in walk(experiments_path):
        _files = [
            path.join(dirpath, _file)
            for _file in filenames
            if _file.endswith((".yaml", ".yml"))
        ]
        logger.debug("Experiment files to be parsed: {}".format(_files))
        _ignored = [
            path.join(dirpath, _file)
            for _file in filenames
            if not _file.endswith((".yaml", ".yml"))
        ]
        if _ignored:
            logger.debug(
                "The following files where found but ignored: {}".format(
                    _ignored
                )
            )
        break  # Gets only root level directory files
    _scenarios = []
    for _file in _files:
        _parser = ExperimentParser(yaml_path=_file)
        scenario = _parser.parse()
        _scenarios.extend(scenario)
    logger.debug("Scenarios to play: {}".format(_scenarios))
    for scenario in _scenarios:
        logger.info("Scenario: {}".format(scenario.name))
        alistener = Alistener(
            scenario.listener.target,
            scenario.listener.username,
            scenario.listener.password,
            ssh_host_key,
        )

        for action in scenario.actions:
            result = await alistener.tail(scenario.listener.log, scenario.listener.re, action.timeout)

            if result:
                logger.info("Triggering: {}".format(action.name))
                _username = action.username if action.username else "root"
                trigger = Trigger(
                    action, _username, action.password, ssh_host_key
                )
                try:
                    disruption = getattr(trigger, action.name)
                except AssertionError as err:
                    logger.error(err)
                    return 1
                await disruption()

    return 0


def parse_log_config(default_config_file, custom_config_file):
    """
    This will look at logging configuration files and load the config using native abilities of
    python logging.config module. In the first instance, default logging config provided by
    Disruption Generator developers is loaded. After that custom configuration provided by user is
    loaded and it overwrites the default configuration.
    Args:
        default_config_file (str): Path to file hodling default configuration
        custom_config_file (str): Path to file hodling user configuration
    Returns:
        None
    """
    try:
        with open(default_config_file, "r") as f:
            default_config = yaml.safe_load(f)
            logging.config.dictConfig(default_config)
    except FileNotFoundError:
        sys.exit("{} not found. Logging cannot be configured.".format(default_config_file))
    try:
        with open(custom_config_file, "r") as f:
            custom_config = yaml.safe_load(f)
            logging.config.dictConfig(custom_config)
    except FileNotFoundError:
        # If custom config file is not found, it's no probem. Default config will be used.
        pass


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover

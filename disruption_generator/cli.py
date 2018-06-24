# -*- coding: utf-8 -*-

"""Console script for disruption_generator."""
import sys
import click

from disruption_generator import disruption_generator


@click.command()
def main(args=None):
    """Console script for disruption_generator."""
    click.echo(
        "Replace this message by putting your code into "
        "disruption_generator.cli.main"
    )
    click.echo("See click documentation at http://click.pocoo.org/")
    return 0


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover

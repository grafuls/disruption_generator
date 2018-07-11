import pytest

from click.testing import CliRunner

from disruption_generator import cli


@pytest.fixture(scope='module')
def runner():
    return CliRunner()


def test_help_message(runner):
    help_result = runner.invoke(cli.main, args=['--help'])
    assert help_result.exit_code == 0
    assert "Show this message and exit." in help_result.output

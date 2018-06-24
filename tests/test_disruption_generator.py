#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `disruption_generator` package."""

import asyncio
import pytest

from click.testing import CliRunner

from disruption_generator import cli
from disruption_generator.listener.alistener import Alistener


@pytest.fixture
def response():
    """Sample pytest fixture.

    See more at: http://doc.pytest.org/en/latest/fixture.html
    """
    # import requests
    # return requests.get('https://github.com/audreyr/cookiecutter-pypackage')


def test_content(response):
    """Sample pytest test function with the pytest fixture as an argument."""
    # from bs4 import BeautifulSoup
    # assert 'GitHub' in BeautifulSoup(response.content).title.string


def test_command_line_interface():
    """Test the CLI."""
    runner = CliRunner()
    result = runner.invoke(cli.main)
    assert result.exit_code == 0
    assert "disruption_generator.cli.main" in result.output
    help_result = runner.invoke(cli.main, ["--help"])
    assert help_result.exit_code == 0
    assert "--help  Show this message and exit." in help_result.output


@pytest.yield_fixture()
def event_loop():
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()


@pytest.mark.asyncio
async def test_alistener():
    localhost = Alistener(event_loop, "localhost")
    await localhost.tail("/tmp/localping")
    await asyncio.sleep(1)

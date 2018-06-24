#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `disruption_generator` package."""

import asyncssh
import pytest

from click.testing import CliRunner

from disruption_generator import cli
from disruption_generator.listener.alistener import Alistener


def test_command_line_interface():
    """Test the CLI."""
    runner = CliRunner()
    help_result = runner.invoke(cli.main, ["--help"])
    assert help_result.exit_code == 0
    assert "Show this message and exit." in help_result.output


@pytest.mark.asyncio
async def test_alistener():
    localhost = Alistener("localhost")
    async with await asyncssh.connect("localhost") as conn:
        await conn.open_session("ping localhost >> /tmp/pinglocal")
        result = await localhost.tail("/tmp/pinglocal", "icmp")
    assert result

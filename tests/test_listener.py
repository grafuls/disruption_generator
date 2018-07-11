import asyncssh
import pytest

from disruption_generator.listener.alistener import Alistener


@pytest.mark.asyncio
async def test_alistener():
    localhost = Alistener("localhost")
    async with await asyncssh.connect("localhost") as conn:
        async with conn.create_process("ping localhost >> /tmp/pinglocal & sleep 5 ; kill $!") as proc:
            await proc.stdout.readline()
            result = await localhost.tail("/tmp/pinglocal", "icmp")

    assert result

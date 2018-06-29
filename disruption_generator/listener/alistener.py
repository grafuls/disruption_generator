# -*- coding: utf-8 -*-

import asyncio
import re
import logging

from asyncssh import SSHClient, create_connection

logger = logging.getLogger(__name__)


class AlistenerException(Exception):
    pass


class Alistener(object):
    def __init__(self, hostname, ssh_host_key):
        self.hostname = hostname
        self.ssh_host_key = ssh_host_key
        self.files = []

    async def run_client(self, filepath, expression, timeout):
        conn, client = await create_connection(
            SSHClient,
            host=self.hostname,
            known_hosts=None,
            client_keys=self.ssh_host_key,
            username="root",
        )
        async with conn:
            logger.debug("Connected to %s", self.hostname)
            stdin, stdout, stderr = await conn.open_session(
                "tail -F %s" % filepath
            )

            async def match():
                while True:
                    output = await stdout.readline()
                    m = re.search(expression, output)
                    if m and m.group(0):
                        logger.debug("Found occurrence: %s", output)
                        stdin.write("\x03")
                        return True

            try:
                return await asyncio.wait_for(match(), timeout)
            except asyncio.TimeoutError:
                logger.debug("Found no results")
                return False

    async def tail(self, filepath, expression, timeout=3):
        if not filepath.lower() in self.files:
            self.files.append(filepath.lower())
            result = await self.run_client(filepath, expression, timeout)
            return result

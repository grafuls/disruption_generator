# -*- coding: utf-8 -*-

import asyncssh
import re
import time
import logging

logger = logging.getLogger(__name__)


class AlistenerException(Exception):
    pass


class Alistener(object):
    def __init__(self, hostname):
        self.hostname = hostname
        self.files = []

    async def run_client(self, filepath, expression, timeout):
        async with await asyncssh.connect(self.hostname) as conn:
            logger.debug("Connected to %s", self.hostname)
            stdin, stdout, stderr = await conn.open_session("tail -f %s" % filepath)
            start = time.time()
            while time.time() - start < timeout:
                output = await stdout.readline()
                m = re.search(expression, output)
                if m and m.group(0):
                    logger.debug("Found occurrance: %s", output)
                    return True
            logger.debug("Found no results")
            return False

    async def tail(self, filepath, expression, timeout=3):
        if not filepath.lower() in self.files:
            self.files.append(filepath.lower())
            result = await self.run_client(filepath, expression, timeout)
            return result

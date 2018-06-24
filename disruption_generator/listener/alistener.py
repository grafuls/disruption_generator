# -*- coding: utf-8 -*-

import asyncio
import asyncssh
import sys


class MySSHClientSession(asyncssh.SSHClientSession):
    def data_received(self, data):
        print(data, end='')

    def connection_lost(self, exc):
        if exc:
            print('SSH session error: ' + str(exc), file=sys.stderr)


class AlistenerException(Exception):
    pass


class Alistener(object):
    def __init__(self, loop, hostname):
        self.loop = loop
        self.hostname = hostname
        self.files = []

    @classmethod
    async def run_client(cls, filepath):
        conn, client = await asyncssh.create_connection(asyncssh.SSHClient, cls.hostname)

        async with conn:
            chan, session = await conn.create_session(MySSHClientSession, 'tail -f %s' % filepath)
            await chan.wait_closed()

    async def tail(self, filepath):
        if not filepath.lower() in self.files:
            self.files.append(filepath.lower())
            self.loop.create_task(self.run_client(filepath))


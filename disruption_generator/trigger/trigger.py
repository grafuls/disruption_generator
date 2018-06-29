import logging

from asyncssh import SSHClient, create_connection

ALL_ACTIONS = ["restart_service"]

logger = logging.getLogger(__name__)


class Trigger(object):
    def __init__(self, action, ssh_host_key):
        self.action = action
        self.ssh_host_key = ssh_host_key

    def __getattr__(self, item):
        attr_err_msg = (
            "Unexpected disruptive action other than %s"
            % ", ".join(ALL_ACTIONS)
        )
        assert item in ALL_ACTIONS, attr_err_msg
        return self.__getattribute__(item)

    async def run_client(self, cmd):
        conn, client = await create_connection(
            SSHClient,
            host=self.action.target_host,
            known_hosts=None,
            client_keys=self.ssh_host_key,
            username="root",
        )

        async with conn:
            logger.debug("Connected to %s", self.action.target_host)
            logger.info("Running: '%s %s'" % (cmd, self.action.params))
            result = await conn.run("%s %s" % (cmd, self.action.params))
            if result.exit_status == 0:
                return True
            else:
                return False

    async def restart_service(self):
        cmd = "systemctl restart"
        result = await self.run_client(cmd)
        return result

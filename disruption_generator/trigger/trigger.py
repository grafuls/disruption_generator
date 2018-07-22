import asyncio
import asyncssh
import logging

ALL_ACTIONS = ["restart_service", "latency"]

logger = logging.getLogger(__name__)


class Trigger(object):
    def __init__(self, action, username, password, ssh_host_key):
        self.action = action
        self.username = username
        self.password = password
        self.ssh_host_key = ssh_host_key

    def __getattr__(self, item):
        attr_err_msg = "Unexpected disruptive action other than {}".format(
            ", ".join(ALL_ACTIONS)
        )
        assert item in ALL_ACTIONS, attr_err_msg
        return self.__getattribute__(item)

    async def run_client(self, cmd):
        conn, client = await create_connection(
            SSHClient,
            host=self.action.target_host,
            known_hosts=None,
            username=self.username,
            password=self.password,
            client_keys=self.ssh_host_key,
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
        """
        Restart a service on a remote host

        Returns:
            result (bool): Result of the restart
        """
        cmd = "systemctl restart"
        result = await self.run_client(cmd)
        return result

    async def latency(self):
        """
        Add latency to a remote hosts link

        Returns:
            result (bool): True if successful, False otherwise
        """
        cmd_add = "tc qdisc add dev eth0 root netem delay"
        cmd_del = "tc qdisc del dev eth0 root netem delay"
        result = await self.run_client(cmd_add)
        wait = self.action.wait if self.action.wait else 10
        await asyncio.sleep(wait)
        if result:
            rollback = await self.run_client(cmd_del)
            if not rollback:
                logger.info("Rollback was not successful")

        return result

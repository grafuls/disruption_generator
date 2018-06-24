import asyncssh
import logging

ALL_ACTIONS = ["restart_service"]

logger = logging.getLogger(__name__)


class Trigger(object):
    def __init__(self, action):
        self.action = action

    def __getattr__(self, item):
        attr_err_msg = "Unexpected disruptive action other than %s" % ", ".join(
            ALL_ACTIONS
        )
        assert item in ALL_ACTIONS, attr_err_msg
        return self.__getattribute__(item)

    async def run_client(self, cmd):
        async with await asyncssh.connect(self.action.target_host) as conn:
            logger.debug("Connected to %s", self.action.target_host)
            result = await conn.run('%s %s' % (cmd, self.action.params))
            if result.exit_status == 0:
                return True
            else:
                return False

    async def restart_service(self):
        cmd = "systemctl restart"
        result = await self.run_client(cmd)
        return result

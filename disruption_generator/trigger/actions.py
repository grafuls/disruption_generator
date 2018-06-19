import logging

ALL_ACTIONS = ["restart_service"]

logger = logging.getLogger("Action")


class Action:

    def __init__(self, executor):
        self.executor = executor

    def __getattr__(self, item):
        attr_err_msg = "Unexpected disruptive action other than %s" % ", ".join(
            ALL_ACTIONS
        )
        assert item in ALL_ACTIONS, attr_err_msg
        return self.__getattribute__(item)

    def restart_service(self, service):
        # TODO: make this OS independent
        _cmd = ["systemctl", "restart", service]
        self.executor.execute_command(_cmd, self.username, self.password)

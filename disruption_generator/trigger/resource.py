import logging
from rrmngmnt.host import Host as HostResource
from rrmngmnt.user import User

DEFAULT_WAIT = 10
DEFAULT_TIMEOUT = 240

logger = logging.getLogger("resource")


class Resource:
    """
    Trigger class execute disruptive actions remotely via ssh
    """
    def __init__(
            self,
            target,
            username,
            password,
            wait=DEFAULT_WAIT,
            timeout=DEFAULT_TIMEOUT
    ):
        self.ssh = None
        self.channel = None
        self.executor = None
        self.target = target
        self.username = username
        self.password = password
        self.wait = wait
        self.timeout = timeout
        logger.info(
            "Initiating executor for resource: %s with username %s and "
            "password %s" % (target, username, password)
        )
        self.initiate_executor(target, username, password)

    def initiate_executor(self, ip, username, password):
        """
        Initiate an executor instance
        """
        if ip:
            host = HostResource(ip=ip)
            user = User(username, password)
            host.users.append(user)
            self.executor = host.executor(user)
            self.ssh = self.executor.session()
            transport = self.ssh._ssh.get_transport()
            if transport is None:
                self.ssh.close()
                self.ssh.open()
                transport = self.ssh._ssh.get_transport()
            self.channel = transport.open_session()

    def execute_command(
            self,
            command_to_exec,
            remote_username,
            remote_password
    ):
        """
        Executes command on a local or remote machine -
        if "ip_for_execute_command" is None then command will be executed on
        the same host as the file
        """
        rc = None
        if self.target:
            self.initiate_executor(
                self.target, remote_username, remote_password
            )
        logger.info(
            "run command %s on resource %s", command_to_exec,
            self.target
        )
        rc, out, err = self.executor.run_cmd(
            cmd=command_to_exec, io_timeout=90
        )
        assert rc, (
            "Failed to execute command %s with err %s and output %s" %
            (command_to_exec, err, out)
        )
        return rc

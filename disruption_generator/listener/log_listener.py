import re
import shlex
import subprocess
import logging
import os
import time
from rrmngmnt.host import Host as HostResource
from rrmngmnt.user import User
import argparse

DEFAULT_TIMEOUT = 240

#####################################
# Set up logging for this component #
#####################################

# TODO: Generate this based on the module's name or the main class of component
LOGGER_NAME = "log_listener"

# TODO: Let user set log level for file/console via config file and/or CLI args
logger = logging.getLogger(LOGGER_NAME)
logger.setLevel(logging.DEBUG)

# Set logging to file
log_file_handler = logging.FileHandler("{}.{}".format(LOGGER_NAME, "log"))
log_file_handler.setFormatter(logging.Formatter("%(asctime)s %(message)s"))

# Set logging to console
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter("%(asctime)s %(message)s"))
console_handler.setLevel(logging.INFO)

logger.addHandler(log_file_handler)
logger.addHandler(console_handler)


class LogListener:
    """
    listener class, watch files for changes (look for requested pattern) and
    executes a command (given by the user).
    The file can be on your local machine or on a remote one.
    The command that should be executed can executed also,
    on your local machine or on a remote machine
    """

    def __init__(self, ip_for_files, username, password, time_out=DEFAULT_TIMEOUT):
        self.ssh = None
        self.channel = None
        self.executor = None
        self.time_out = time_out
        logger.info(
            "Initiating executor for ip: %s with username %s and "
            "password %s" % (ip_for_files, username, password)
        )
        self.initiate_executor(ip_for_files, username, password)

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
        run_locally,
        command_to_exec,
        ip_for_execute_command=None,
        remote_username=None,
        remote_password=None,
    ):
        """
        Executes command on a local or remote machine -
        if "ip_for_execute_command" is None then command will be executed on
        the same host as the file
        """
        rc = None
        if not run_locally:
            if ip_for_execute_command:
                self.initiate_executor(
                    ip_for_execute_command, remote_username, remote_password
                )
            logger.info(
                "run command %s on ip %s", command_to_exec, ip_for_execute_command
            )
            rc, out, err = self.executor.run_cmd(
                cmd=shlex.split(command_to_exec), io_timeout=90
            )
            assert rc, (
                "Failed to execute command %s with err %s and output %s"
                % (command_to_exec, err, out)
            )
        else:
            try:
                logger.info("run command %s locally", command_to_exec)
                # os.system returns an exit status code.
                # 0 means that there weren't any errors.
                # converting 0 to bool --> False --> not False --> True
                # when no errors
                rc = not bool(os.system(command_to_exec))
            except RuntimeError as ex:
                logger.info("Can't run command %s, exception: %s", command_to_exec, ex)
        return rc

    @staticmethod
    def follow(file_to_follow):
        """
        Read lines from file in almost real-time fashion.
        Args:
            file_to_follow: _io.TextIOWrapper object obtained by open() builtin
        """
        file_to_follow.seek(0, 2)
        while True:
            line = file_to_follow.readline()
            if not line:
                # TODO: Might be solved by: https://pypi.org/project/inotify/
                time.sleep(0.1)
                continue
            yield line

    def follow_local_file(self, file_to_watch, regex):
        """
        This is different implementation of watch_for_local_changes.
        If am not 100 % sure that this is the correct way to go.
        Therefore keeping both implementations for now.

        Returns:
            re.Match object if regex was found, False otherwise
        """
        start_time = time.time()
        with open(file_to_watch) as f:
            loglines = self.follow(f)
            for line in loglines:
                logger.debug(
                    'Looking for "%s" in line "%s" in file %s',
                    regex,
                    line.strip(),
                    file_to_watch,
                )
                if self.time_out > time.time() - start_time:
                    match = re.search(regex, line)
                    if match:
                        logger.info(
                            "Found match (%s) in file %s",
                            match.string.strip(),
                            file_to_watch,
                        )
                        return match
                else:
                    logger.info('No match for "%s" found until timeout', regex)
                    return False

    def watch_for_remote_changes(self, files_to_watch, regex):
        """
        Method that runs "tail -f 'file_name'" command remotely.
        Execute the "tail -f" command through communication_
        components_list[1] (channel)

        Args:
            files_to_watch (str): Paths to files to watch
            regex (str): Regular expression to look for

        Returns:
            str: The regex if there's a match, empty string otherwise
        """
        start_time = time.time()
        try:
            logger.info("run 'tail -f' command on file/s %s", files_to_watch)
            self.channel.exec_command("tail -f " + files_to_watch)
        except RuntimeError as ex:
            logger.info("Can't run command %s, exception is %s", "tail -f", ex)

        recv = ""
        while self.time_out > time.time() - start_time:
            try:
                # receive the output from the channel
                recv = "".join([recv, self.channel.recv(1024)])
                reg = re.search(regex, recv)

                if reg:
                    logger.info("regex %s found..", regex)
                    return reg

            except KeyboardInterrupt:
                self.channel.close()
                self.ssh.close()
                raise Exception("close connections")
        return ""

    def watch_for_local_changes(self, files_to_watch, regex):
        """
        Method that runs "tail -f 'file_name'" command locally

        Args:
            files_to_watch (str): Paths to files to watch
            regex (str): Regular expression to look for

        Returns:
            str: The regex if there's a match, empty string otherwise
        """
        start_time = time.time()
        try:
            logger.info("run 'tail -f' command on file/s %s", files_to_watch)
            f = subprocess.Popen(
                ["tail", "-F", files_to_watch, "| stdbuf -o0"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

        except RuntimeError as ex:
            logger.info(
                "Can't run command %s on %s, exception is %s",
                "tail",
                files_to_watch,
                ex,
            )
        recv = ""
        while True:
            if self.time_out:
                if self.time_out < time.time() - start_time:
                    return ""
            try:
                line = f.stdout.readline()
                recv = "".join([recv, str(line)])
                reg = re.search(regex, recv)

                if reg:
                    logger.info("regex %s found..", regex)
                    return reg

            except KeyboardInterrupt:
                raise RuntimeError("Caught control-C")
        return ""

    def watch_for_changes(self, run_locally, files_to_watch, regex):
        """
        Method that runs "tail -f 'file_name'" command

        Args:
            run_locally (bool): If the command should run in the local host
            or remotely
            files_to_watch (str): Paths to files to watch
            regex(str): Regular expression to look for

        Returns:
            str: The regex if there's a match, empty string otherwise
        """
        logger.info("watching for regex: %s", regex)

        if not run_locally:
            logger.info("on remote machine")
            return self.watch_for_remote_changes(files_to_watch, regex)

        else:
            logger.info("on local machine")
            return self.follow_local_file(files_to_watch, regex)
            # return self.watch_for_local_changes(files_to_watch, regex)


def watch_logs(
    files_to_watch,
    regex,
    command_to_exec=None,
    time_out=None,
    ip_for_files=None,
    username=None,
    password=None,
    ip_for_execute_command=None,
    remote_username=None,
    remote_password=None,
):
    """
    When importing this module, this function can be used to watch log file
    for specific event , and executes commands.

    Parameters:
        * files_to_watch - a list of full pathes of a files that need to be
        watched
        * regex - a regular expression that need to be watched for
        * command_to_exec - the command that need to execute when event in
        the file occurs. If not needed, pass None
        * ip_for_files - in case that the files are located on a remote
        machine - the IP of that machine
        * username - the user name for the remote machine
        * password - the password for the remote machine
        * ip_for_execute_command - in case that the command needs to execute
        on remote machine - IP for
          that machine
        * remote_username - the user name for the remote machine that the
        command executes on
        * remote_password - the password for the remote machine that the
        command executes on

    Returns: (found_regex,cmd_rc)

            found_regex - (str) if there's a match, None otherwise
            cmd_rc - True if command exit successfully , False otherwise

    -  In case that "ip_for_execute_command" is None -> assign "ip" to it so
       that
       the command will executes on same machine that the "files_to_watch"
       is on
    """
    run_locally = False
    if not ip_for_execute_command:
        if not ip_for_files:
            # indicates if the command should executes locally
            run_locally = True
        else:
            ip_for_execute_command = ip_for_files
        remote_username = username
        remote_password = password

    listener = LogListener(ip_for_files, username, password, time_out)

    cmd_rc = None
    found_regex = listener.watch_for_changes(run_locally, files_to_watch, regex)

    if found_regex:
        if command_to_exec:
            cmd_rc = listener.execute_command(
                run_locally,
                command_to_exec,
                ip_for_execute_command,
                remote_username,
                remote_password,
            )
    else:
        logger.debug("Didn't find regex %s in files %s" % (regex, files_to_watch))
    return found_regex, cmd_rc


def main():
    """
    In case of manual execution -
    (files_to_watch,regex,command_to_exec,ip,username,password,
    ip_for_execute_command,remote_username,remote_password,time_out)

    1. in case of remote machine:
        - ip: the remote machine IP
        - username/password: authentication

    2. for all cases (local & remote)
        - files_to_watch: absolute path of the file that should be watched (
          start with "/")
        - regex: regular expression to look for
        - command_to_exec: the command that should be executed in case that
          the regex has found. If not needed, pass None
        - ip_for_execute_command: the !!! IP !!! of the machine that the
          command should exec on
        - remote_username: username for the second machine
        - remote_password: password for the second machine
        - time_out: limited time for watching

    Options -
        * -m, --machine : if the file is on remote machine then '-m' followed
          by ip,username & password
          (e.g. -m 10.0.0.0 root P@SSW0RD)
        * -f,--files : option that followed by the absolute path of the files
          that need to watch for.
          each file should be preceded by -f separately
          (e.g. -f /var/log/vdsm/vdsm.log -f /tmp/my_log)
        * -r, --regex : option for regex (e.g. -r <REGULAR_EXPRESSION>)
        * -c, --command : followed by the command that should be executed in
          case of log event
          (e.g. -c 'ls -l') <- note that parameters with white space MUST be
          surrounds by " ' "
        * -M, --Machine : in case that the command should executes on
          different machine , this option followed
          by IP,username & password
          (e.g. -M 10.0.0.0 root P@SSW0RD)
        * -t, --timeout : limited time for watching
          (e.g. -t 3)

    """
    usage = "Usage: %prog [options] arg1 arg2"
    parser = argparse.ArgumentParser(
        description="this function can be used "
        "to watch log file for "
        "specific event ,"
        "and executes commands."
    )

    parser.add_argument(
        "-m",
        "--machine",
        action="store",
        dest="ip",
        nargs=3,
        help="if the file is on remote machine then '-m' "
        "followed by ip,username & password",
        default=(None, None, None),
    )

    parser.add_argument(
        "-f",
        "--file",
        action="append",
        dest="files_to_watch",
        help="option that followed by "
        "the absolute path of the "
        "file that need to watch for, each file should "
        "be preceded by -f separately",
        required=True,
        default=[],
    )

    parser.add_argument(
        "-r",
        "--regex",
        action="store",
        type=re.compile,
        dest="regex",
        required=True,
        help="option for regex (e.g. -r <REGULAR_EXPRESSION>)",
    )

    parser.add_argument(
        "-c",
        "--command",
        action="store",
        dest="command_to_exec",
        required=True,
        help="followed by the command that should be executed " "in case of log event",
    )

    parser.add_argument(
        "-M",
        "--Machine",
        action="store",
        dest="ip_for_execute_command",
        nargs=3,
        help="in case that the command should executes on "
        "different machine , "
        "this option followed by IP,username & password",
        default=(None, None, None),
    )

    parser.add_argument(
        "-t",
        "--timeout",
        action="store",
        type=int,
        dest="time_out",
        help="limited time for watching",
    )

    options = parser.parse_args()

    # TODO: Here we join files into a str, while docstring of watch_logs says it expects list
    # TODO: Check that provided files actually exist in order to catch this problem early
    files_to_watch = " ".join(options.files_to_watch)
    regex = options.regex
    command_to_exec = options.command_to_exec

    time_out = options.time_out

    ip_for_execute_command = None
    ip = None

    if options.ip:
        ip, username, password = options.ip

    if options.ip_for_execute_command:
        ip_for_execute_command, remote_username, remote_password = options.ip_for_execute_command

    logger.info("start watching...")
    watch_logs(
        files_to_watch,
        regex.pattern,
        command_to_exec,
        time_out=time_out,
        ip_for_files=ip,
        username=username,
        password=password,
        ip_for_execute_command=ip_for_execute_command,
        remote_username=remote_username,
        remote_password=remote_password,
    )

    logger.info("Done !!!")


if __name__ == "__main__":
    main()

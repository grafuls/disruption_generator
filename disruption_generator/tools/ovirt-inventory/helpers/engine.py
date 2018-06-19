"""
Class that gets information about engine via SSH
"""

import re

from rrmngmnt import Host, User

from helpers.config import engine as engine_conf


class Engine:
    """
    Class that gets informations and runs ssh commands on engine
    """
    config = None
    host = None

    def __init__(self, config, server):
        self.config = config
        self.host = Host(server)
        self.host.users.append(User(config["ssh"]["USER"], config["ssh"]["PASSWORD"]))

    def run(self, command):
        """
        Run command via ssh on the server

        Arguments:
            command (list): command to run, parsed with shlex
        Returns: (list) lines of command output
        Raises: (EngineException) In case running command failed
        """
        result, out, err = self.host.executor().run_cmd(command)
        if result == 0 and out:
            return out.split("\n")
        else:
            if not err and not out:
                err = "No output"
            raise EngineException(
                "command `{cmd}`: {err}".format(cmd=" ".join(command), err=err)
            )

    def get_hostname(self):
        """
        Get engine's fqdn
        """
        for hostname in self.host.network.hostname.split("\n"):
            if "localhost" not in hostname:
                return hostname

    def get_release_info(self):
        """
        Get engine's OS info
        """
        return self.host.os.release_info


class EngineData:
    """
    Class that processes engine's data via SSH
    """
    engine = None
    config = None

    def __init__(self, config, server):
        self.config = config
        self.engine = Engine(config, server)

    def get_data(self):
        """
        Get informations from the engine server

        Returns: (dict) engine informations (e.g. db user/password, fqdn, os
            version, ...)
        """
        data = {}
        release_info = self.engine.get_release_info()
        data["os"] = "{os}-{version}".format(
            os=release_info["ID"], version=release_info["VERSION_ID"]
        )
        data["arch"] = self.engine.run(["uname", "-i"])[0]
        data["fqdn"] = self.engine.get_hostname()

        r = re.compile(
            "({})".format("|".join(engine_conf.DATABASE_SETUP_FILES_KEYS)),
            re.IGNORECASE,
        )
        for conf_item in engine_conf.DATABASE_SETUP_FILES:
            out = self.engine.run(
                [
                    "grep",
                    conf_item["regex"],
                    "{etc_dir}/{conf_file}".format(
                        etc_dir=self.config["other"]["ENGINE_ETC_DIR"],
                        conf_file=conf_item["file"],
                    ),
                ]
            )
            for line in filter(r.search, out):
                key, value = line.strip().split("=")
                data_key = key.replace(conf_item["regex"], "").lower()
                data[conf_item["key_prefix"] + data_key] = value.strip()[1:-1]

        return data


class EngineException(Exception):
    """
    Class for Engine exceptions
    """

    def __str__(self):
        return "[Engine] {}".format(self.message)

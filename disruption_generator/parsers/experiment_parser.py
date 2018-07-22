import attr
import logging
import yaml
import zope.interface

from . import config
from .utils import Action, Listener, Disruption
from zope.interface import implementer

logger = logging.getLogger(__name__)


class ParserException(Exception):
    pass


class IParser(zope.interface.Interface):
    """
    Parser for experiments with disruptive actions definitions.
    """

    yaml_path = zope.interface.Attribute("The path to the scenario yaml")

    def parse(self):
        """
        Parse `self._path`, yield a :class:`Disruption` for each entry found.
        """


@implementer(IParser)
@attr.s(hash=True)
class ExperimentParser(object):

    yaml_path = attr.ib()

    def parse(self):
        def _init_listener(element_listener):
            """
            Returns listener info

            Args:
                element_listener (dict): yaml info of listener
            Returns:
                Listener: object with listener info
            """

            try:
                regex = element_listener[config.REGEX_KEY]
                log_file = element_listener[config.LOG_KEY]
                host = element_listener[config.HOST_KEY]
                username = element_listener[config.USERNAME_KEY]
                password = element_listener[config.PASSWORD_KEY]
            except KeyError as ex:
                raise ParserException(
                    "Missing {} definition from listener section".format(ex)
                )
            _listener = Listener(
                regex=regex,
                log=log_file,
                target=host,
                username=username,
                password=password,
            )
            return _listener

        def _init_actions(element_trigger):
            """
            Returns a list of actions info from trigger element

            Args:
                element_trigger (dict): yaml info of trigger
            Returns:
                List(Action): dictionary with trigger info
            """

            _actions = []
            for trigger in element_trigger:
                try:
                    key = config.ACTION_KEY
                    _name = trigger[key][config.NAME_KEY]
                    params = trigger[key][config.PARAMS_KEY]
                    target_host = trigger[key][config.TARGET_HOST_KEY]
                    username = trigger[key][config.USERNAME_KEY]
                    password = trigger[key][config.PASSWORD_KEY]
                    wait = trigger[key][config.WAIT_KEY]
                    timeout = trigger[key][config.TIMEOUT_KEY]

                    action = Action(
                        name=_name,
                        params=params,
                        target_host=target_host,
                        username=username,
                        password=password,
                        wait=wait,
                        timeout=timeout,
                    )
                    _actions.append(action)
                except KeyError as ex:
                    raise ParserException(
                        "Missing %s definition from action section", ex
                    )
            return _actions

        doc = None
        try:
            with open(self.yaml_path, "r") as f:
                data = f.read()
                doc = yaml.safe_load(data)
        except IOError as e:
            logging.error(
                "Failed to open file {file_name}, Why: {err}".format(
                    file_name=self.yaml_path, err=e
                )
            )

        _scenarios = []
        for disrupt_action in doc:
            name = disrupt_action[config.DISRUPT_ACTION_KEY][0][
                config.NAME_KEY
            ]
            listener = _init_listener(
                disrupt_action[config.DISRUPT_ACTION_KEY][0][
                    config.LISTENER_KEY
                ]
            )
            actions = _init_actions(
                disrupt_action[config.DISRUPT_ACTION_KEY][0][
                    config.TRIGGER_KEY
                ]
            )

            disruption = Disruption(
                name=name, listener=listener, actions=actions
            )

            _scenarios.append(disruption)

        return _scenarios

import attr
import logging
import yaml
import zope.interface

from . import config
from .utils import Action, Listener, Disruption
from zope.interface import implementer

logger = logging.getLogger(__name__)


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

            re = element_listener["re"]
            log_file = element_listener["log"]
            host = element_listener["host"]
            _listener = Listener(re=re, log=log_file, target=host)
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
                key = "action"
                _name = trigger[key][config.NAME_STR]
                params = trigger[key]["params"]
                target_host = trigger[key]["target_host"]
                wait = trigger[key]["wait"]
                timeout = trigger[key]["timeout"]

                trigger = Action(
                    name=_name,
                    params=params,
                    target_host=target_host,
                    wait=wait,
                    timeout=timeout,
                )
                _actions.append(trigger)
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

        _disruptions = []
        for disrupt_action in doc:
            name = disrupt_action[config.DISRUPT_ACTION_STR][0][config.NAME_STR]
            listener = _init_listener(
                disrupt_action[config.DISRUPT_ACTION_STR][0][config.LISTENER_STR]
            )
            actions = _init_actions(
                disrupt_action[config.DISRUPT_ACTION_STR][0][config.TRIGGER_STR]
            )

            disruption = Disruption(name=name, listener=listener, actions=actions)

            _disruptions.append(disruption)

        return _disruptions

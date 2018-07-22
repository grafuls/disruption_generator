import attr
import six


@attr.s(hash=True)
class Action(object):
    """
    A trigger object with the requested disruptive action.
    """

    name = attr.ib(validator=attr.validators.instance_of(six.text_type))
    params = attr.ib(validator=attr.validators.instance_of(six.text_type))
    target_host = attr.ib(validator=attr.validators.instance_of(six.text_type))
    username = attr.ib(validator=attr.validators.instance_of(str))
    password = attr.ib(validator=attr.validators.instance_of(str))
    wait = attr.ib(validator=attr.validators.instance_of(int))
    timeout = attr.ib(validator=attr.validators.instance_of(int))


@attr.s(hash=True)
class Listener(object):
    """
    A listener object which holds necessary data for logs and triggers.
    """

    regex = attr.ib(validator=attr.validators.instance_of(six.text_type))
    log = attr.ib(validator=attr.validators.instance_of(six.text_type))
    target = attr.ib(validator=attr.validators.instance_of(six.text_type))
    username = attr.ib(validator=attr.validators.instance_of(str))
    password = attr.ib(validator=attr.validators.instance_of(str))


@attr.s(hash=True)
class Disruption(object):
    """
    A disruptive action with all necessary information for causing trouble.
    """

    name = attr.ib(validator=attr.validators.instance_of(six.text_type))
    listener = attr.ib(validator=attr.validators.instance_of(Listener))
    actions = attr.ib(validator=attr.validators.instance_of(list))

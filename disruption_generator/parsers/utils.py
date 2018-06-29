import attr


@attr.s(hash=True)
class Action(object):
    """
    A trigger object with the requested disruptive action.
    """

    name = attr.ib(validator=attr.validators.instance_of(str))
    params = attr.ib(validator=attr.validators.instance_of(str))
    target_host = attr.ib(validator=attr.validators.instance_of(str))
    wait = attr.ib(validator=attr.validators.instance_of(int))
    timeout = attr.ib(validator=attr.validators.instance_of(int))


@attr.s(hash=True)
class Listener(object):
    """
    A listener object which holds necessary data for logs and triggers.
    """

    re = attr.ib(validator=attr.validators.instance_of(str))
    log = attr.ib(validator=attr.validators.instance_of(str))
    target = attr.ib(validator=attr.validators.instance_of(str))
    repeat = attr.ib(validator=attr.validators.instance_of(int))


@attr.s(hash=True)
class Disruption(object):
    """
    A disruptive action with all necessary information for causing trouble.
    """

    name = attr.ib(validator=attr.validators.instance_of(str))
    listener = attr.ib(validator=attr.validators.instance_of(Listener))
    actions = attr.ib(validator=attr.validators.instance_of(list))

#!/usr/bin/env python

"""
scenario yaml parser
"""

import logging
import yaml
import config as conf

logger = logging.getLogger(__name__)


def parse(scenario_file=conf.FILE_LOCATION):
    """
    Parse the scenario yaml, and return dictionary representation
    
    Args:
        scenario_file (str): File name and path
    Return:
        dict: dictionary representation of the yaml
    """
    
    def _init_listener(element_listener):
        """
        Returns listener info
        
        Args:
            element_listener (dict): yaml info of listener
        Returns:
            dict: dictionary with listener info
        """
        
        re = element_listener['re']
        log_file = element_listener['log']
        host = element_listener['host']
        return {'re': re, 'log_file': log_file, 'host': host}
    
    def _init_trigger(element_trigger):
        """
        Returns trigger info

        Args:
            element_trigger (dict): yaml info of trigger
        Returns:
            dict: dictionary with trigger info
        """
        
        actions = {}
        for action in element_trigger:
            key = action.keys()[0]
            name = '{key}_{name}'.format(key=key, name=action[key]['name'])
            actions[name] = {
                'action': key,
                'name': action[key][conf.NAME_STR],
                'target_host': action[key]['target_host'],
                'wait': action[key]['wait'],
                'timeout': action[key]['timeout']
            }
        return actions
    
    doc = None
    disrupt_action_dict = {}
    try:
        with open(scenario_file, 'r') as f:
            data = f.read()
            doc = yaml.safe_load(data)
    except IOError as e:
        logging.error('Failed to open file {file_name}, Why: {err}'.format(
            file_name=scenario_file, err=e
        ))
    
    for disrupt_action in doc:
        name = disrupt_action[conf.DISRUPT_ACTION_STR][0][conf.NAME_STR]
        disrupt_action_dict[name] = {
            'listener': _init_listener(
                disrupt_action[conf.DISRUPT_ACTION_STR][0][conf.LISTENER_STR]
            ),
            'trigger': _init_trigger(
                disrupt_action[conf.DISRUPT_ACTION_STR][0][conf.TRIGGER_STR]
            )
        }
    logging.info('disrupt action:{dict}'.format(dict=disrupt_action_dict))

    return disrupt_action_dict

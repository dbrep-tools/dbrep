"""
This module provides simple way to handle configs.
Key concept is having ability to override or generalize any given config.

So typical config structure should be as follows:
0. secret.key -- file containinig Fernet key
1. credentials.yaml.crypto -- encrypted credentials (or you may leave it unencrypted with credentials.yaml)
2. connections.yaml -- list of connections that can reference credentials {{level0.level1.level2}}
3. templates.yaml -- list of templates that are accessible for jobs
4. jobs.yaml -- list of jobs or pure job description
5. STDIN -- in form of level0.level1.level2=value, e.g. src.connection=ConName, src.table='asd'

So there must be a way to combine these multiple configs into single one. This could be done in two steps:
1. Unite all configs into single big config file: going from general to override/specific values
2. Use templating to update values of this final config
"""
import string
import functools
import copy
from typing import Any, Dict, List, Tuple, Union


def make_config(list_of_pairs : List[Tuple[str, Any]]) -> dict:
    """
    Convert list of pairs into structured config/dictionary.
    E.g. convert (a.b.c, 3) into {'a': {'b': {'c': 3}}}
    """
    if not list_of_pairs: #None, empty list and other should evaluate to empty dict
        return {}
    res = {}
    for k,v in list_of_pairs:
        keys = k.split('.')
        cur = res
        for x in keys[:-1]:
            if x not in cur:
                cur[x] = {}
            cur = cur[x]
        cur[keys[-1]] = v
    return res

def merge_handler_override(a, b):
    return b or a

def merge_handler_expand_or_override(a, b):
    if isinstance(a, list) and isinstance(b, list):
        return a + b
    return b or a

def merge_config(*args : dict, merge_handler=merge_handler_override) -> dict:
    """
    Merge several configs into single one. Later argument overrides the former.
    """
    def merge_dict(d1, d2, merge_handler):
        if isinstance(d1, dict) and isinstance(d2, dict):
            return {k: merge_dict(d1.get(k), d2.get(k), merge_handler) for k in set.union(set(d1), set(d2))}
        return merge_handler(d1, d2) #override with later        
    return functools.reduce(functools.partial(merge_dict, merge_handler=merge_handler), args, {})


def unflatten_config(config: Union[dict, list]) -> Union[dict, list]:
    if isinstance(config, list):
        return [unflatten_config(x) for x in config]
    elif isinstance(config, dict):
        cfg0 = {k:unflatten_config(v) for k,v in config.items() if '.' not in k}
        cfg1 = make_config([(k, unflatten_config(v)) for k,v in config.items() if '.' in k])
        return merge_config(cfg0, cfg1)
    else:
        return config


def flatten_config(config : dict, prefix : str = '') -> dict:
    """
    Convert config into flat map like a.b.c -> 1, a.b.d ->2, etc.
    """
    if not config: #None, empty dict and other should evaluate to empty dict
        return {}
    if not prefix:
        formatter = '{}'
    else:
        formatter = prefix + '.{}'
    res = {formatter.format(k): v for k,v in config.items()
                    if type(v) is not dict}
    res.update({k2: v2 for k, v in config.items()
                    if type(v) is dict
                    for k2, v2 in flatten_config(v, formatter.format(k)).items()})
    return res

def instantiate_templates(config: Union[dict, list], templates: dict, keywords = ['template', 'templates'], merge_handler = merge_handler_expand_or_override) -> Union[dict, list]:
    """
    Insert template values for `templates` dictionary into config, e.g.
    {
        "templates": ["a", "b"],
        "val": 3
    }
    {
        "a": {"va": 4, "vb": 5},
        "b": {"vb": 7, "vc": 8}
    }
    Should return
    {
        "templates": ["a", "b"],
        "va": 4,
        "vb": 7,
        "vc": 8,
        "val": 3
    }
    """
    if not config:
        return config
    if not templates:
        return config
    if isinstance(config, list):
        return [instantiate_templates(x, templates, keywords=keywords) for x in config]
    if not isinstance(config, dict):
        return config
    templates_to_use = []
    for k in keywords:
        if k in config:
            if isinstance(config[k], str):
                templates_to_use.append(config[k])
            elif isinstance(config[k], list) or isinstance(config[k], tuple):
                if not all(isinstance(x, str) for x in config[k]):
                    raise TypeError('Template value should be list of strings or single string, but got list with inconsistent types')
                templates_to_use += list(config[k])
            else:
                raise TypeError('Template value should be list of strings or single string, but got {}'.format(type(config[k])))
    if not templates_to_use: #exit early
        return config
    for t in templates_to_use:
        if t not in templates:
            raise ValueError('Template `{}` not present in templates dictionary'.format(t))
    
    result = merge_config(copy.deepcopy(config), *[templates[t] for t in templates_to_use], merge_handler=merge_handler)
    return {k: instantiate_templates(v, templates, keywords=keywords) for k,v in result.items()}
        
def expand_config(config: dict, field_from: str, field_to: str, merge_handler = merge_handler_expand_or_override) -> List[dict]:
    """
    Expand config into multiple items. E.g.
    {
        "values": [7, 10]
    }
    Will get expanded into
    [
        {
            "value": 7
        },
        {
            "value": 8
        }
    ]
    """
    tmp = config
    for p in field_from.split('.'):
        if p not in tmp:
            return [config]
        tmp = tmp[p]

    if not isinstance(tmp, list):
        raise TypeError('Config expansion can be made only on lists, but got {}'.format(type(tmp)))
    return [merge_config(copy.deepcopy(config), unflatten_config({field_to: v}), merge_handler=merge_handler) for v in tmp]

class TemplateDotted(string.Template):
    braceidpattern = r'[_a-z][_a-z0-9\.@\-]*'

def substitute_config(config : dict) -> dict:
    """
    Replace values like ${a.b.c} with value of a.b.c from this config
    """
    def replace_template(val, mapping):
        if isinstance(val, dict):
            return {k: replace_template(v, mapping) for k,v in val.items()}
        if isinstance(val, str):
            return TemplateDotted(val).substitute(mapping)
        return val
        
    if not config: #None, empty dict and other should evaluate to empty dict
        return {}
    flat_conf = flatten_config(config)
    while True:
        new_conf = replace_template(flat_conf, copy.deepcopy(flat_conf))
        if new_conf == flat_conf:
            break
        flat_conf = new_conf
    return replace_template(config, flat_conf)

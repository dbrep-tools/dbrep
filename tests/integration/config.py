import os
import yaml

from errors import InvalidTestConfigError
import dbrep.config

def read_multi_configs(prefix, postfix, names):
    files = [x for x in os.listdir('./')
                if x.startswith(prefix or '') and x.endswith(postfix or '')]
    res = {}
    for fn in files:
        with open(fn, 'rb') as f:
            tmp = yaml.safe_load(f.read().decode('utf8'))
        res.update(tmp[names] if names in tmp else tmp)
    return res

def override_as_list(config, names):
    if isinstance(config, dict):
        for n in names:
            if n in config:
                if not isinstance(config[n], list):
                    config[n] = [config[n]]
        return {k: override_as_list(v, names) for k,v in config.items()}
    elif isinstance(config, list):
        return [override_as_list(v, names) for v in config]
    else:
        return config


def read_test_configs():
    with open('connections.yaml', 'rb') as f:
        connections = yaml.safe_load(f.read().decode('utf8'))

    tests = read_multi_configs('test_', '.yaml', 'tests')
    templates = read_multi_configs('template_', '.yaml', 'templates')
    res = dbrep.config.unflatten_config({
        'connections': connections,
        'templates': templates,
        'tests': tests
    })
    override_as_list(res, ['setup', 'cleanup', 'steps'])
    return res

def is_explicit_test(config):
    return 'test' in config and 'config' in config and 'template' not in config \
        and 'tests' not in config and 'configs' not in config

def make_explicit_tests(config):
    def expand_test_config(cfg):
        res = dbrep.config.expand_config(cfg, 'configs', 'config')
        res = [v for x in res for v in dbrep.config.expand_config(x, 'config.src.conns', 'config.src.conn')]
        res = [v for x in res for v in dbrep.config.expand_config(x, 'config.dst.conns', 'config.dst.conn')]
        res = [v for x in res for v in dbrep.config.expand_config(x, 'tests', 'test')]
        res = [v for x in res for v in dbrep.config.expand_config(x, 'config.modes', 'config.mode')]
        for x in res:
            for k in ['tests', 'configs', 'template', 'templates']:
                if k in x:
                    del x[k]
            if 'modes' in x['config']:
                del x['config']['modes']
            if 'conns' in x['config']['src']:
                del x['config']['src']['conns']
            if 'conns' in x['config']['dst']:
                del x['config']['dst']['conns']
            if 'name' in x['test'] and 'name' in x:
                x['name'] = '_'.join([x['name'], x['test']['name']])
                del x['test']['name']
        return res
    templates = config.get('templates', [])
    res = [dbrep.config.instantiate_templates(dict(**v, name=k), templates) for k,v in config['tests'].items()]
    return [v for x in res for v in expand_test_config(x)]
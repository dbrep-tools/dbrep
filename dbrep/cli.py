import argparse
import logging
import sys
from typing import Dict, Optional, Union

from cryptography.fernet import Fernet
import yaml

from .config import make_config, merge_config, substitute_config
from .replication import full_refresh, incremental_update
from . import create_engine, add_engine_factory, init_factory

logFormatter = logging.Formatter("%(asctime)s [%(levelname)-5.5s]  %(message)s")
logger = logging.getLogger()
consoleHandler = logging.StreamHandler(stream=sys.stdout)
consoleHandler.setFormatter(logFormatter)
logger.addHandler(consoleHandler)
logger.setLevel(logging.DEBUG)

class StoreDictKeyPair(argparse.Action):
    def __init__(self, option_strings, dest, nargs=None, **kwargs):
        self._nargs = nargs
        super(StoreDictKeyPair, self).__init__(option_strings, dest, nargs=nargs, **kwargs)
        
    def __call__(self, parser, namespace, values, option_string=None):
        my_dict = {}
        for kv in values:
            k,v = kv.split("=")
            my_dict[k] = v
        setattr(namespace, self.dest, my_dict)

def make_dbrep_argparser():
    parser = argparse.ArgumentParser(description='DataBase REPlication tool')
    subparsers = parser.add_subparsers(dest='cmd_main')
    parser_run = subparsers.add_parser('run', help='run replication between databases (and other entities)')
    parser_config = subparsers.add_parser('config', help='configure connections and templates (TBD), i.e. manage public data')
    parser_secret = subparsers.add_parser('secret', help='configure credentials and secrets, i.e. manage private data')

    parser_run.add_argument('-f', '--local', default='dbrep.yaml', help='Location of local configuration yaml (may reference global and credentials)')
    parser_run.add_argument('-g', '--globals', default=None, help='Location of global configuration yaml (may reference credentials)')
    parser_run.add_argument('-c', '--credential', default='dbrep.cred', help='Location of dbrep credentials file')
    parser_run.add_argument('-s', '--secret', default=None, help='Location of file with crypto-key')
    parser_run.add_argument('-r', '--run', default=None, help='Specify name of replication to run')
    parser_run.add_argument('-o', '--options', default=None, action=StoreDictKeyPair, nargs="*", metavar="KEY=VAL", help='Override options')

    parser_secret.add_argument('cmd', choices=['new', 'ls', 'rm', 'set'])
    parser_secret.add_argument('-s', '--secret', default=None, help='Location of file with crypto-key')
    parser_secret.add_argument('-c', '--credential', default='dbrep.cred', help='Location of dbrep credentials file')
    parser_secret.add_argument('-n', '--namespace', default=None, help='Location of file with crypto-key')
    parser_secret.add_argument('-o', '--options', default=None, action=StoreDictKeyPair, nargs="*", metavar="KEY=VAL", help='Configure values')

    return parser


def cli_dbrep():
    parser = make_dbrep_argparser()
    args = parser.parse_args()
    if args.cmd_main == 'run':
        secret = load_secret(args.secret)
        local_config = load_config(args.local, secret) or {}
        global_config = load_config(args.globals, secret)
        cred_config = load_config(args.credential, secret) or {}        
        options = make_config((args.options or {}).items())
        config = substitute_config(merge_config(global_config, cred_config, local_config, options))
        return run(config)
    elif args.cmd_main == 'secret':
        return manage_secrets(args)
    elif args.cmd_main == 'config':
        return manage_configs(args)
    else:
        raise NotImplementedError('Unexpected command in dbrep')

def load_secret(fname: Optional[str]) -> Optional[bytes]:
    if fname is None:
        return None
    with open(fname, 'r') as f: #propagate exception if invalid file
        return f.read().encode('utf-8')

def load_config(fname: Optional[str], secret: Optional[bytes] = None) -> Optional[Dict]:
    if fname is None:
        return None
    with open(fname, 'rb') as f:
        data = f.read()
    if secret is not None:
        frn = Fernet(secret)
        data = frn.decrypt(data)
    return yaml.safe_load(data.decode('utf-8'))

def manage_secrets(args):
    print('Invoke secrets with args: {}'.format(args))

def manage_configs(args):
    print('Invoke configs with args: {}'.format(args))


def make_engine(conn_config: Union[Dict, str], full_config: Dict):
    if isinstance(conn_config, str):
        if 'connections' not in full_config or conn_config not in full_config['connections']:
            raise KeyError('When specifying name of connection ({}), it should exist in `connections` section of config'.format(conn_config))
        config = full_config['connections'][conn_config]
    elif isinstance(conn_config, dict):
        config = conn_config
    else:
        raise TypeError('conn_config should be dict or str, but got {}'.format(conn_config))

    if not isinstance(config, dict):
        raise TypeError('Connection config should be dict with at least `engine` field, but got {}'.format(type(config)))
    if 'engine' not in config:
        raise ValueError('Connection config should contain at least `engine` field')

    return create_engine(config['engine'], config)

def run(config : Dict):
    init_factory()
    if 'run' not in config:
        raise ValueError("Must specify `run` parameter: either name of replication from config, or dictionary specifying replication!")

    if isinstance(config['run'], str):
        run_config = config['replications'][config['run']] #Propagate exceptions
    elif isinstance(config['run'], dict):
        run_config = config['run']
    else:
        raise TypeError('Inapproapriate type of `run`: {}, while expected either dict or str'.format(type(config['run'])))
    
    if not isinstance(run_config, dict):
        raise TypeError('Run should be dict, but got {}!'.format(type(run_config)))
    if 'src' not in run_config or 'dst' not in run_config or 'mode' not in run_config:
        raise ValueError('Run should contain mode, src and dst')

    src_engine = make_engine(run_config['src']['conn'], config)
    dst_engine = make_engine(run_config['dst']['conn'], config)

    if run_config['mode'] == 'full-refresh':
        return full_refresh(src_engine, dst_engine, run_config)
    elif run_config['mode'] == 'incremental':
        return incremental_update(src_engine, dst_engine, run_config)
    else:
        raise ValueError("Unsupported mode: {}. Should be full-refresh or incremental".format(run_config['mode']))
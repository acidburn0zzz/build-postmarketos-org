import logging
import sys

host = "0.0.0.0"
port = 5000
database = "bpo.db"
gitlab_secret = None
job_service = "local"

local_pmaports = "pmaports"
local_pmbootstrap = "pmbootstrap"
local_tempdir = "temp"


def init():
    import argparse
    import configparser

    self = sys.modules[__name__]

    # Save type info
    ints = []
    floats = []
    for key in self.__dict__:
        if not '__' in key and not key == 'init':
            if isinstance(getattr(self, key), int):
                ints.append(key)
            elif isinstance(getattr(self, key), float):
                floats.append(key)

    # Create argparser
    parser = argparse.ArgumentParser(description="postmarketOS build coordinator")

    parser.add_argument('config', help='Config file')
    parser.add_argument('--verbose', '-v', help='Show more debug info', action='store_true')

    for key in self.__dict__:
        if not '__' in key and not key == 'init':
            parser.add_argument('--{}'.format(key.replace('_', '-')))
    args = parser.parse_args()

    # Read base config from configfile
    configfile = configparser.ConfigParser()
    configfile.read(args.config)
    for section in configfile.sections():
        prefix = ''
        if section != 'config':
            prefix = '{}_'.format(section)

        for key, value in configfile.items(section):
            real_key = prefix + key.replace('-', '_')
            if hasattr(self, real_key):
                setattr(self, real_key, value)
            else:
                logging.warning('Unknown key in config file: {}.{}'.format(section, key))

    # Apply overrides from argparse
    for key in self.__dict__:
        if not '__' in key and not key == 'init':
            ap_value = getattr(args, key.replace('-', '_'))
            if ap_value is not None:
                setattr(self, key, ap_value)

    # Correct types
    for key in self.__dict__:
        if key in ints:
            setattr(self, key, int(getattr(self, key)))
        if key in floats:
            setattr(self, key, float(getattr(self, key)))

    if args.verbose:
        print('Loaded config:')
        for key in self.__dict__:
            if not '__' in key and not key == 'init':
                print('  {} = {}'.format(key, self.__dict__[key]))

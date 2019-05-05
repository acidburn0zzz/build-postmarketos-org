import sys

host = "0.0.0.0"
port = 1338
database = "database.sql"
gitlab_secret = None
job_service = "local"

local_pmaports = a
local_pmbootstrap = b
local_tempdir = a


def init():
    import argparse
    import configparser

    # Create argparser
    parser = argparse.ArgumentParser(description="postmarketOS build coordinator")
    parser.add_argument('config', help='Config file')
    self = sys.modules[__name__]
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
            real_key = prefix + key
            setattr(self, real_key, value)

    # Apply overrides from argparse
    for key in self.__dict__:
        if not '__' in key and not key == 'init':
            ap_value = getattr(args, key)
            if ap_value is not None:
                setattr(self, key, ap_value)

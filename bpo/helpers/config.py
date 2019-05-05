import sys

host = "0.0.0.0"
port = 1338
database = "database.sql"
gitlab_secret = None


def init():
    import argparse
    import configparser

    parser = argparse.ArgumentParser(description="postmarketOS build coordinator")
    self = sys.modules[__name__]
    for key in self.__dict__:
        if not '__' in key and not key == 'init':
            parser.add_argument('--{}'.format(key.replace('_', '-')), default=globals()[key])
    args = parser.parse_args()
    for key in self.__dict__:
        if not '__' in key and not key == 'init':
            setattr(self, key, getattr(args, key))

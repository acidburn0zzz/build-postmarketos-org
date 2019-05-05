# Copyright 2019 Oliver Smith
# SPDX-License-Identifier: GPL-3.0-or-later
import logging
import sys
from .helpers import args as helpers_args
from .helpers import httpd as helpers_httpd


def logging_init():
    logging.basicConfig(level=logging.DEBUG, stream=sys.stdout,
                        format="[%(asctime)s] %(message)s", datefmt="%H:%M:%S")


def main():
    # Initialize logging, args, database
    logging_init()
    args = helpers_args.init()

    # Run the webserver
    helpers_httpd.run(args)


if __name__ == "__main__":
    sys.exit(main())

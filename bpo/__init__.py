# Copyright 2019 Oliver Smith
# SPDX-License-Identifier: GPL-3.0-or-later
import logging
import sys

from flask import Flask
from bpo.component.gitlab import gitlab


def logging_init():
    logging.basicConfig(level=logging.DEBUG, stream=sys.stdout,
                        format="[%(asctime)s] %(message)s", datefmt="%H:%M:%S")


def main():
    # Initialize logging, args, database
    logging_init()
    app = Flask(__name__)
    app.register_blueprint(gitlab)


if __name__ == "__main__":
    sys.exit(main())

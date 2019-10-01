# Copyright 2019 Oliver Smith
# SPDX-License-Identifier: AGPL-3.0-or-later

import configparser
import hashlib
import logging
import os
import string
import sys

import bpo.config.const
import bpo.config.args


# Hashes of generated tokens will be stored here
push_hook_gitlab = None
job_callback = None


def load():
    """ Load existing token file into ConfigParser() or prepare new one. """
    ret = configparser.ConfigParser()
    path = bpo.config.args.tokens
    if os.path.isfile(path):
        ret.read(path)

    if "bpo" not in ret:
        ret["bpo"] = {}

    return ret


def hash_generate(token):
    """ Generate a token and save the sha512 hash to the token file.
        :param token: name of the token, e.g. "push_hook_gitlab"
        :returns: hash of the generated token """
    # Generate
    chars = string.ascii_letters + string.digits
    token_plain = os.urandom(50).hex()
    token_hash = hashlib.sha512(token_plain.encode()).hexdigest()

    # Show the generated token to the user once
    path = bpo.config.args.tokens
    print("=== Token generated! ===")
    print("name:  " + token)
    print("value: " + token_plain)
    print("This token will not be shown again, a hash is saved in your config")
    print("file (remove to generate a new token): " + path)
    print("========================")

    # Save the hash
    cfg = load()
    cfg["bpo"][token] = token_hash
    with open(path, "w") as handle:
        cfg.write(handle)
    os.chmod(path, 0o600)
    return token_hash


def init():
    """ Load/generate all tokens. """
    tokens = ["push_hook_gitlab", "job_callback"]
    self = sys.modules[__name__]
    cfg = load()

    for token in tokens:
        if token in cfg["bpo"]:
            setattr(self, token, cfg["bpo"][token])
        else:
            setattr(self, token, hash_generate(token))

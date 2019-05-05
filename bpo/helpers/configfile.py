# Copyright 2019 Oliver Smith
# SPDX-License-Identifier: GPL-3.0-or-later
import configparser
import hashlib
import logging
import os
import secrets
import string

import bpo.helpers.config

def load(args):
    """ Load existing config file into ConfigParser() or prepare new one. """
    ret = configparser.ConfigParser()
    if os.path.isfile(args.config):
        ret.read(args.config)

    if "bpo" not in ret:
        ret["bpo"] = {}

    return ret


def token_hash_generate(args, config_key):
    """ Generate a token and save the sha512 hash to the config file.
        :param config_key: where to store it, e.g. "token_push_hook_gitlab"
        :returns: hash of the generated token """
    # Generate
    chars = string.ascii_letters + string.digits
    token = "".join([secrets.choice(chars) for _ in range(50)])
    ret = hashlib.sha512(token.encode()).hexdigest()

    # Show the generated token to the user once
    print("=== Token generated! ===")
    print("name:  " + config_key.replace("token_hash_","",1))
    print("value: " + token)
    print("This token will not be shown again, a hash is saved in your config")
    print("file (remove to generate a new token): " + args.config)
    print("========================")

    # Save the hash
    cfg = load(args)
    cfg["bpo"][config_key] = ret
    with open(args.config, "w") as handle:
        cfg.write(handle)
    os.chmod(args.config, 0o600)
    return ret


def init(args):
    """ Load config file, and extend args. """
    cfg = load(args)
    for key in bpo.helpers.config.configfile_keys:
        # Try to load from config file
        value = None
        if key in cfg["bpo"]:
            value = cfg["bpo"][key]

        # Generate missing tokens
        elif key.startswith("token_hash_"):
            value = token_hash_generate(args, key)

        # Extend args
        setattr(args, key, value)

# Copyright 2020 Oliver Smith
# SPDX-License-Identifier: AGPL-3.0-or-later

import configparser
import hashlib
import os
import sys

import bpo.config.const
import bpo.config.args


# Hashes of generated tokens will be stored here
push_hook_gitlab = None
job_callback = None
job_callback_secret = None  # sourcehut secret ID for the job_callback token
sourcehut = None  # personal access oauth token
final_sign_secret = None  # sourcehut secret ID for the final signing rsa key


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
    self = sys.modules[__name__]
    cfg = load()

    # Load or generate
    for token in ["push_hook_gitlab", "job_callback"]:
        if token in cfg["bpo"]:
            setattr(self, token, cfg["bpo"][token])
        else:
            setattr(self, token, hash_generate(token))

    # Just load
    for token in ["sourcehut", "job_callback_secret", "final_sign_secret"]:
        if token in cfg["bpo"]:
            setattr(self, token, cfg["bpo"][token])


def require(token):
    """ :param token: name of the required token (e.g. "sourcehut") """
    self = sys.modules[__name__]
    if getattr(self, token):
        return

    print("=== Token missing! ===")
    print("name: " + token)
    print("Please obtain this token (see README.md for details) and put it in")
    print("the [bpo] section of this file: " + bpo.config.args.tokens)
    print("Then restart the bpo server and try again.")
    print("========================")
    sys.exit(1)

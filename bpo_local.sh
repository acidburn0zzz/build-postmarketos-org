#!/bin/sh -ex
rm -rf bpo.db _repo_wip* || true
./bpo.py -t test/test_tokens.cfg local

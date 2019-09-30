#!/bin/sh -ex
rm -rf bpo.db _repo* || true

# Use old binary repository URL for testing locally, because otherwise it would
# try to build *all* packages.
./bpo.py -t test/test_tokens.cfg -m "http://postmarketos.brixit.nl" local

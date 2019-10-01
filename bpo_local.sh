#!/bin/sh -ex
rm -rf bpo.db _repo* _temp _html_out || true

# Use old binary repository URL for testing locally, because otherwise it would
# try to build *all* packages.
./bpo.py -t test/test_tokens.cfg -m "http://postmarketos.brixit.nl" local

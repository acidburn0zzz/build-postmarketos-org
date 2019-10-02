#!/bin/sh -ex
rm -rf bpo.db _repo* _temp _html_out || true

./bpo.py -a -t test/test_tokens.cfg local

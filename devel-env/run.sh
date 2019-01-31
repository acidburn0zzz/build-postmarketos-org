#!/bin/sh -e
# TODO: check if installed: docker, docker-compose
# TODO: shellcheck this!

scriptdir="$(cd $(dirname "$0"); pwd)"
gitdir="$(realpath $scriptdir/..)"

# Use default config
cd "$gitdir"
if [ -e .env ]; then
	if ! diff -s .env .env.dist; then
		echo "ERROR: .env is different from .env.dist!"
		echo "Make a backup of the file if you had modified it:"
		echo "  $gitdir/.env"
		echo "Then remove it and try again."
		exit 1
	fi
else
	cp -a .env.dist .env
fi

# Build custom docker containers
docker build -t bpo:latest "$scriptdir/bpo"

# use docker-compose to run everything
cd "$scriptdir"
docker-compose up

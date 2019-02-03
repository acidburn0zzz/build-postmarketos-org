#!/bin/sh -e
# TODO: check if installed: docker, docker-compose
# TODO: shellcheck this!

scriptdir="$(cd $(dirname "$0"); pwd)"
gitdir="$(realpath $scriptdir/..)"

# Use default config
cd "$gitdir"
if [ -e .env ]; then
	if ! diff -q .env .env.dist; then
		echo "ERROR: .env is different from .env.dist!"
		echo "Make a backup of the file if you have modified it:"
		echo "  $gitdir/.env"
		echo "Then remove it and try again."
		exit 1
	fi
else
	cp -a .env.dist .env
fi

# Build custom docker containers
docker build -t bpo:latest "$scriptdir/bpo"
docker build -t builds.sr.ht:latest "$scriptdir/builds.sr.ht"

# use docker-compose to run everything
cd "$scriptdir"
docker-compose rm -f builds.sr.ht postgres redis
docker-compose up

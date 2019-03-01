#!/bin/sh -e
scriptdir="$(cd $(dirname "$0"); pwd)"
gitdir="$(realpath $scriptdir/..)"
database_line="DATABASE_URL=mysql://root:devsetup@db:3306/bpo"

# Check required commands
for cmd in docker docker-compose; do
	if ! command -v "$cmd" >/dev/null 2>&1; then
		echo "ERROR: missing command: $cmd"
		exit 1
	fi
done

# Copy default config
cd "$gitdir"
if ! [ -e .env ]; then
	cp -v .env.dist .env
fi

# Check database line
if ! grep -q "^$database_line\$" .env; then
	echo "ERROR: please change your DATABASE_URL line in $PWD/.env to:"
	echo "$database_line"
	exit 1
fi

# Check sr.ht token
if grep -q "^SRHT_TOKEN=a$" .env; then
	echo "ERROR: please register a personal access token at"
	echo "       https://meta.sr.ht/oauth/register and put it into"
	echo "       SRHT_TOKEN in $PWD/.env."
	exit 1
fi

# Build custom docker container
docker build -t bpo:latest "$scriptdir/bpo"

# Use docker-compose to run everything
cd "$scriptdir"
docker-compose up

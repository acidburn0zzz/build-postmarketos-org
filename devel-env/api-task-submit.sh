#!/bin/sh -e

# Generate secret
scriptdir="$(cd $(dirname "$0"); pwd)"
. "$scriptdir/../.env"
secret="$(printf "$APP_SECRET" | sha1sum | cut -d' ' -f 1)"
commit="e8a7926eb6004ba57ae8b9a7250ce563188dd808"
arch="x86_64"

# Submit hello-world task
curl -H "Content-Type: application/json" \
	-H "X-Secret: $secret" \
	-H "X-Commit: $commit" \
	-H "X-Arch: $arch" \
	--data '[{"pkgname": "hello-world",
		"version": "1-r4",
		"repo": "master",
		"branch": "master",
		"depends": []}]' \
	http://localhost/api/task-submit

#!/bin/sh -ex

echo "Waiting for redis, postgres, docker in docker..."
sleep 2

#
# *** Install build.sr.ht ***
#
# https://man.sr.ht/builds.sr.ht/installation.md
#
# When these commands run for the first time, they take a long time to
# complete (otherwise they are cached). Prefix each line with sed, so it
# is easy to see what's happening.
#

# Build qemu docker image
cd /var/lib/images
docker build -t qemu -f qemu/Dockerfile . | sed "s/^/[docker build qemu] /"

# Bootstrap "alpine/edge" image
cd /var/lib/images/alpine
export release=edge
./genimg  | sed "s/^/[genimg alpine:$release] /"

#
# *** Configure and run ***
#

# Start nginx
echo "Starting nginx..."
mkdir -p /run/nginx
nginx -t
nginx
tail -qF /var/log/nginx/access.log | sed "s/^/[nginx acc] /" &
tail -qF /var/log/nginx/error.log | sed "s/^/[nginx err] /" &

# Configure database
echo "Configuring meta.sr.ht database..."
export PGPASSWORD="devsetup"
createdb -h postgres -p 5432 -U postgres builds.sr.ht || true
python3 -c "from metasrht.app import db; db.create()"


# Start meta.sr.ht
echo "Starting meta.sr.ht..."
gunicorn metasrht.app:app_dispatch -b 127.0.0.1:5000


# Configure build.sr.ht (requires meta.sr.ht running?)
# python3 -c "from buildsrht.app import db; db.create()"

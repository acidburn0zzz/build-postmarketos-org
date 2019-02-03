#!/bin/sh -e
# Reference: https://man.sr.ht/builds.sr.ht/installation.md
# All these '| sed "s/^/[prefix] /"' statements add a '[prefix] '.

#
# *** Helper functions ***
#

# Run curl with a cookiejar and pretty output.
# Writes the first lines of the downloaded website to stdout and the
# whole thing to /tmp/curl_out.
pretty_curl () {
	(
		echo "*** $@ ***"
		curl -s -c /tmp/cookiejar -b /tmp/cookiejar "$@" \
			| tee /tmp/curl_out | head -n 8
		echo # Add missing \n
	) | sed "s/^/[curl] /"
}

# Wait for a TCP server $1 and port $2
wait_for() {
	echo "[wait] Waiting for: $1 $2"
	while ! nc -z $1 $2; do
		sleep 0.1
	done
}

# Extract oauth token of length $1 from /tmp/curl_out
oauth_token() {
	grep -E -o "<dd>[a-f0-9]{$1}<\/d" /tmp/curl_out \
		| cut -d'>' -f 2 | cut -d '<' -f 1
}

#
# *** Apply patches ***
#
cd ./usr/lib/python3.6/site-packages/
for patch in /patches/*; do
	patch -p1 < "$patch"  2>&1 | sed "s~^~[patch $patch] ~"
done

#
# *** Start nginx ***
#
mkdir -p /run/nginx
nginx -t 2>&1 | sed "s/^/[nginx config check] /"
nginx
tail -qF /var/log/nginx/access.log | sed "s/^/[nginx access] /" &
tail -qF /var/log/nginx/error.log | sed "s/^/[nginx error] /" &

#
# *** Install build.sr.ht ***
#

# Wait for other docker containers
wait_for redis 6379
wait_for postgres 5432
wait_for docker 2375

# Build qemu docker image (takes a long time, but gets cached)
cd /var/lib/images
docker build -t qemu -f qemu/Dockerfile . 2>&1 \
	| sed "s/^/[docker build qemu] /"

# Bootstrap "alpine/edge" image (FIXME: not working yet)
cd /var/lib/images/alpine
export release=edge
./genimg 2>&1 | sed "s/^/[genimg alpine:$release] /"

#
# *** Configure and run ***
#

# Configure database
echo "Configuring meta.sr.ht database..."
export PGPASSWORD="devsetup"
dropdb -h postgres -p 5432 -U postgres builds.sr.ht || true
createdb -h postgres -p 5432 -U postgres builds.sr.ht
python3 -c "from metasrht.app import db; db.create()" 2>&1 | \
	sed "s/^/[meta.sr.ht db create] /"

# Start meta.sr.ht
echo "Starting meta.sr.ht..."
gunicorn metasrht.app:app_dispatch -b 127.0.0.1:5000 2>&1 \
	| sed "s/^/[meta.sr.ht] /" &
wait_for localhost 5000

# Register account
pretty_curl "http://localhost:8000/register" \
	-d "username=devsetup" \
	-d "password=devsetup" \
	-d "email=devsetup@localhost"

# Give admin access
python3 -c "from metasrht.app import db, User, UserType
u = User.query.filter_by(username='devsetup').one()
u.user_type = UserType.admin
User.query.session.commit()" 2>&1 | sed "s/^/[give admin access] /"

# Register builds.sr.ht oauth token
pretty_curl "http://localhost:8000/login" \
	-d "username=devsetup" \
	-d "password=devsetup"
pretty_curl "http://localhost:8000/oauth/register" \
	-d "client-name=builds.sr.ht" \
	-d "redirect-uri=http://localhost:8002/oauth/callback"
pretty_curl "http://localhost:8000/oauth/registered"

# Put oauth token in config
client_id="$(oauth_token 16)"
client_secret="$(oauth_token 32)"
echo "[oauth] client id: $client_id"
echo "[oauth] client secret: $client_secret"
sed "s/^oauth-client-id=/oauth-client-id=$client_id/" \
	-i /etc/sr.ht/config.ini
sed "s/^oauth-client-secret=/oauth-client-secret=$client_secret/" \
	-i /etc/sr.ht/config.ini

# Mark build.sr.ht as first-party
psql -h postgres -p 5432 -U postgres builds.sr.ht -c \
	"UPDATE oauthclient
	 SET preauthorized = true
	 WHERE client_id = '$client_id';" \
	2>&1 | sed "s/^/[psql update oauthclient] /"

# Configure build.sr.ht
echo "Configuring builds.sr.ht database..."
python3 -c "from buildsrht.app import db; db.create()"

gunicorn buildsrht.app:app -b 127.0.0.1:5002 2>&1 \
	| sed "s/^/[builds.sr.ht] /" &
wait_for localhost 5002


# Start build.sr.ht
# builds.sr.ht-worker 2>&1 | sed "s/^/[worker] /"

sleep 999

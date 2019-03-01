#!/bin/sh

# Delete all persistent data from the docker containers (mariadb database!)
docker-compose rm -f -v

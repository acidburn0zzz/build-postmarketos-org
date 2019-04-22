#!/bin/sh -e
# Execute /bin/sh in the running BPO container

# Get the container's ID
id="$(docker container ls | grep develenv_bpo_1 | cut -f 1 -d' ')"
if [ -z "$id" ]; then
	echo "ERROR: could not get container ID of BPO container. Did you do ./run.sh?"
	exit 1
fi

# Run /bin/sh
set -x
docker exec -it "$id" sh

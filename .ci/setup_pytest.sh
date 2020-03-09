#!/bin/sh -e
pmb_url="https://gitlab.com/postmarketOS/pmbootstrap/-/archive/master/pmbootstrap-master.tar.bz2"

# Sanity check
if [ -z "$CI" ]; then
	echo "ERROR: This script is only supposed to run in CI!"
	exit 1
fi
set -x

# Install depends
apt-get update > /dev/null
apt-get -y install git procps python3-pip sudo wget > /dev/null
pip3 -q --disable-pip-version-check install -r requirements.txt \
	pytest pytest-cov pytest-timeout

# Create pmos user
useradd pmos -m -s /bin/bash
chown -R pmos:pmos .
echo 'pmos ALL=(ALL) NOPASSWD: ALL' >> /etc/sudoers

# Install pmbootstrap
mount -t binfmt_misc none /proc/sys/fs/binfmt_misc
wget -q "$pmb_url"
tar -xf pmbootstrap-master.tar.bz2
mv pmbootstrap-master ../pmbootstrap
chown -R pmos:pmos ../pmbootstrap
su pmos -c 'yes "" | ../pmbootstrap/pmbootstrap.py -q init'

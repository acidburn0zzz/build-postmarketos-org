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

# Install python 3.6
py3_url="https://github.com/chriskuehl/python3.6-debian-stretch/releases/download/v3.6.3-1-deb9u1"
wget -q "$py3_url/python3.6_3.6.3-1.deb9u1_amd64.deb" \
	"$py3_url/python3.6-minimal_3.6.3-1.deb9u1_amd64.deb" \
	"$py3_url/python3.6-dev_3.6.3-1.deb9u1_amd64.deb" \
	"$py3_url/libpython3.6_3.6.3-1.deb9u1_amd64.deb" \
	"$py3_url/libpython3.6-minimal_3.6.3-1.deb9u1_amd64.deb" \
	"$py3_url/libpython3.6-stdlib_3.6.3-1.deb9u1_amd64.deb" \
	"$py3_url/libpython3.6-dev_3.6.3-1.deb9u1_amd64.deb"
dpkg -i *.deb > /dev/null

# Make pmbootstrap use python 3.6. This hack can be removed once our production
# environment for bpo has python >= 3.6 available.
cd ../pmbootstrap
(echo "#!/usr/bin/python3.6"; cat pmbootstrap.py) > _
chmod +x _
mv _ pmbootstrap.py
cat pmbootstrap.py
python3 -V
python3.6 -V

# pmbootstrap init (echo: fix missing \n)
su pmos -c 'yes "" | ./pmbootstrap.py -q init'
echo

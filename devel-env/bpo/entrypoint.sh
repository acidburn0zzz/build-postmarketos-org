#!/bin/sh -ex

# Install depends
cd ~/bpo
composer install

# Create/migrate database
bin/console doctrine:database:create --if-not-exists --no-interaction
bin/console doctrine:migrations:migrate --no-interaction

# Run web server
sudo /usr/local/bin/apache-start.sh

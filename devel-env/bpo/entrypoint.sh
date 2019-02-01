#!/bin/sh -ex

# Install depends
cd ~/bpo
composer install

# Wait for MySQL server to show up
sleep 3

# Create/migrate database
bin/console doctrine:database:create --if-not-exists --no-interaction
bin/console doctrine:migrations:migrate --no-interaction

# Run web server
bin/console server:run 0.0.0.0

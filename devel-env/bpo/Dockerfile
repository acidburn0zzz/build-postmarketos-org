FROM alpine:latest

# Install depends
RUN apk add \
	apache2 \
	composer \
	php7-ctype \
	php7-dom \
	php7-pdo_mysql \
	php7-simplexml \
	php7-tokenizer \
	php7-xml \
	php7-xmlrpc \
	sudo

# Allow starting apache2 as user (used in entrypoint.sh)
ARG script=/usr/local/bin/apache-start.sh
RUN echo 'whoami; echo "FIXME: start apache here"; exit 1' > $script
RUN chmod +x $script
RUN echo "user ALL=(root) NOPASSWD: $script" > /etc/sudoers
RUN visudo -c

# Create user
RUN adduser -D -s /bin/sh user users
USER user:users
RUN mkdir -p ~/bpo
WORKDIR /home/user/bpo
ENTRYPOINT ~/bpo/devel-env/bpo/entrypoint.sh

FROM alpine:latest

# Install depends
RUN apk --no-cache add \
	composer \
	php7-ctype \
	php7-dom \
	php7-pdo_mysql \
	php7-simplexml \
	php7-session \
	php7-tokenizer \
	php7-xml \
	php7-xmlrpc \
	php7-xmlwriter

# Create user
RUN adduser -D -s /bin/sh user users
USER user:users
RUN mkdir -p ~/bpo
WORKDIR /home/user/bpo
COPY entrypoint.sh /home/user/entrypoint.sh
ENTRYPOINT ~/entrypoint.sh

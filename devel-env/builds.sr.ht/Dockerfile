FROM alpine:edge

# Upgrade TLS certificates (so we can connect to mirror.sr.ht)
RUN apk --no-cache upgrade

# Install builds.sr.ht
COPY alpine@sr.ht.rsa.pub /etc/apk/keys/
RUN echo "https://mirror.sr.ht/alpine/sr.ht" >> /etc/apk/repositories
RUN apk --no-cache add builds.sr.ht

# FIXME: switch user and run it

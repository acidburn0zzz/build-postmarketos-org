FROM alpine:edge

# Upgrade TLS certificates (so we can connect to mirror.sr.ht)
RUN apk --no-cache upgrade

# Install builds.sr.ht
COPY alpine@sr.ht.rsa.pub /etc/apk/keys/
RUN echo "http://dl-cdn.alpinelinux.org/alpine/edge/testing" >> /etc/apk/repositories && \
	echo "https://mirror.sr.ht/alpine/sr.ht" >> /etc/apk/repositories
RUN apk --no-cache add \
	builds.sr.ht \
	builds.sr.ht-images \
	builds.sr.ht-worker \
	docker \
	meta.sr.ht \
	py3-psycopg2 \
	qemu-img

# FIXME: these should be depends of meta.sr.ht
RUN apk --no-cache add \
	py3-stripe \
	py3-weasyprint \
	py3-cssselect2 \
	py3-tinycss2 \
	py3-cairocffi \
	py3-pyphen \
	pango \
	py3-cairosvg \
	py3-defusedxml \
	py3-pdfrw

# FIXME: merge with first one
RUN apk --no-cache add \
	postgresql-client \
	nginx

COPY config.ini /etc/sr.ht/config.ini
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Create user
# RUN adduser -D -s /bin/sh user users
# USER user:users
# WORKDIR /home/user/
COPY entrypoint.sh /entrypoint.sh
ENTRYPOINT /entrypoint.sh

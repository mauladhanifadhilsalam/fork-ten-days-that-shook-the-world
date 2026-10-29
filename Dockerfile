# Ten Days That Shook the World on Cloud Run: build the page from source, serve it with nginx.
# Adapted from Raskolnikov Wandering. Base images come through mirror.gcr.io, Google's cache of
# Docker Hub, so Cloud Build does not hit Docker Hub's anonymous rate limit.

# Stage 1: pack the page (standard-library Python only) and pre-compress it.
FROM mirror.gcr.io/library/python:3.12-slim AS build
WORKDIR /src
COPY tools/bundle.py tools/bundle.py
COPY src/ src/
COPY build/map.json build/story.json build/
COPY deploy/nginx.conf.template deploy/nginx.conf.template
RUN python3 -I tools/bundle.py build/map.json build/story.json src/app.html /out \
 && gzip -9 -k /out/index.html \
 && sed "s|__CSP__|$(cat /out/csp.txt)|" deploy/nginx.conf.template > /out/default.conf.template

# Stage 2: unprivileged nginx on the stable 1.30 branch (runs as UID 101).
# Cloud Run sets PORT; 8080 is the local default.
FROM mirror.gcr.io/nginxinc/nginx-unprivileged:1.30-alpine
ENV PORT=8080
COPY --from=build /out/default.conf.template /etc/nginx/templates/default.conf.template
COPY --from=build /out/index.html /out/index.html.gz /usr/share/nginx/html/
EXPOSE 8080

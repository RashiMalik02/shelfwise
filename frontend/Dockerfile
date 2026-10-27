# ---- build stage: Node is only needed to produce the static bundle ----
FROM node:24-alpine AS build
WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund

COPY . .
# Shown in the header so you can see which commit is actually deployed.
ARG APP_BUILD=dev
ENV VITE_APP_BUILD=$APP_BUILD
RUN npm run build


# ---- runtime stage: unprivileged nginx (uid 101, listens on 8080) ----
FROM nginxinc/nginx-unprivileged:1.30-alpine AS runtime

LABEL org.opencontainers.image.title="shelfwise-frontend" \
      org.opencontainers.image.description="Shelfwise inventory dashboard (React + nginx)"

# Pull in alpine security fixes released after the base image was built,
# so the Trivy gate in CI doesn't fail on already-fixed CVEs.
USER root
RUN apk upgrade --no-cache

# The nginx image runs envsubst on /etc/nginx/templates/*.template at start-up,
# so BACKEND_URL can differ between docker compose and Kubernetes.
ENV BACKEND_URL=http://backend:8000
COPY nginx/default.conf.template /etc/nginx/templates/default.conf.template
COPY --from=build /app/dist /usr/share/nginx/html

USER 101
EXPOSE 8080

HEALTHCHECK --interval=15s --timeout=3s --retries=3 CMD wget -qO- http://127.0.0.1:8080/healthz >/dev/null || exit 1

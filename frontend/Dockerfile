# ==========================================================
# SmartCivicAI frontend image — multi-stage build
# ==========================================================

FROM node:20-alpine AS build
WORKDIR /app

COPY package.json ./
RUN npm install

COPY . .

# Baked in at BUILD time (Vite convention) — this must be the URL the
# user's BROWSER can reach, not the Docker-internal service name. With the
# default docker-compose.yml port mapping (backend published on host
# port 8000), http://localhost:8000/api/v1 is correct for local use.
ARG VITE_API_BASE_URL=http://localhost:8000/api/v1
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=5 \
    CMD wget -q -O - http://localhost:80 > /dev/null || exit 1

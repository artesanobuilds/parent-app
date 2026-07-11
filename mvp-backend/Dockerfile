# Stage 1: Build CMS frontend
FROM node:20-slim AS cms-build
WORKDIR /cms
COPY cms/package.json cms/package-lock.json ./
RUN npm install --legacy-peer-deps
COPY cms/ .
RUN npm run build

# Stage 1b: Build parent dashboard frontend (Vite SPA, base=/dashboard/)
FROM node:20-slim AS dashboard-build
# PostHog analytics is baked at build time (Vite inlines VITE_*). The project
# key is public-by-design (write-only, "safe to use in public apps") — same key
# shipped in the iOS Info.plist — so a committed default here is fine and makes
# prod deterministic without relying on build-arg plumbing. Override via a
# Railway build variable if the key ever rotates.
ARG VITE_POSTHOG_KEY=phc_xdDZCBbTyJQ6RpD4CkSoemGqjmFGtFzfYiCSecRt4abz
ARG VITE_POSTHOG_HOST=https://us.i.posthog.com
ENV VITE_POSTHOG_KEY=$VITE_POSTHOG_KEY
ENV VITE_POSTHOG_HOST=$VITE_POSTHOG_HOST
WORKDIR /dashboard
COPY parent-dashboard/package.json parent-dashboard/package-lock.json ./
RUN npm install --legacy-peer-deps
COPY parent-dashboard/ .
RUN npm run build

# Stage 2: Python backend
FROM python:3.13-slim
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Store seed parquet files separately — the volume mounts over /app/data at runtime
RUN mkdir -p /app/seed-data && cp /app/data/*.parquet /app/seed-data/ 2>/dev/null || true
RUN rm -f /app/data/*.duckdb /app/data/*.duckdb.wal

# Copy built CMS into the expected location
COPY --from=cms-build /cms/dist /app/cms/dist
# Copy built parent dashboard (served at /dashboard by app.server)
COPY --from=dashboard-build /dashboard/dist /app/parent-dashboard/dist

COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

ENV PORT=8080
EXPOSE 8080
ENTRYPOINT ["/app/entrypoint.sh"]

# Stage 1: Build CMS frontend
FROM node:20-slim AS cms-build
WORKDIR /cms
COPY cms/package.json cms/package-lock.json ./
RUN npm install --legacy-peer-deps
COPY cms/ .
RUN npm run build

# Stage 1b: Build parent dashboard frontend (Vite SPA, base=/dashboard/)
FROM node:20-slim AS dashboard-build
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

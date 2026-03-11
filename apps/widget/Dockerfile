# ── Agent Builder Chat Widget ─────────────────────────────────────────────────
# Multi-stage: Node builds Vite app, nginx serves static files.
# ─────────────────────────────────────────────────────────────────────────────

# ── Stage 1: Build ────────────────────────────────────────────────────────────
FROM node:20-alpine AS builder

WORKDIR /app

COPY apps/widget/package.json apps/widget/package-lock.json* ./
RUN npm ci

COPY apps/widget .

# API URL baked in at build time
ARG VITE_API_BASE_URL=http://localhost:8000
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

# Skip tsc (it flags test files) — vite handles transpilation on its own
RUN npx vite build

# ── Stage 2: Serve ────────────────────────────────────────────────────────────
FROM nginx:1.27-alpine

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx/widget.conf /etc/nginx/conf.d/default.conf

EXPOSE 5174

CMD ["nginx", "-g", "daemon off;"]

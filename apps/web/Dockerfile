# syntax=docker/dockerfile:1
FROM node:22-bookworm-slim AS deps
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci

FROM node:22-bookworm-slim AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build

FROM node:22-bookworm-slim AS runner
WORKDIR /app
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
RUN useradd --create-home --uid 10001 dolphin
COPY --from=builder /app/public ./public
COPY --from=builder --chown=dolphin:dolphin /app/.next/standalone ./
COPY --from=builder --chown=dolphin:dolphin /app/.next/static ./.next/static
USER dolphin
EXPOSE 3000
CMD ["node", "server.js"]

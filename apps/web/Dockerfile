FROM node:22-alpine AS dependencies
WORKDIR /app
COPY package.json package-lock.json ./
COPY apps/web/package.json ./apps/web/package.json
RUN npm ci
FROM node:22-alpine AS builder
WORKDIR /app
ENV NEXT_TELEMETRY_DISABLED=1
COPY --from=dependencies /app/ ./
COPY apps/web/ ./apps/web/
RUN npm run build -w @magribi/web
FROM node:22-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production NEXT_TELEMETRY_DISABLED=1 HOSTNAME=0.0.0.0 PORT=3000
RUN addgroup -S magribi && adduser -S magribi -G magribi
COPY --from=builder --chown=magribi:magribi /app/apps/web/.next/standalone ./
COPY --from=builder --chown=magribi:magribi /app/apps/web/.next/static ./apps/web/.next/static
COPY --from=builder --chown=magribi:magribi /app/apps/web/public ./apps/web/public
USER magribi
EXPOSE 3000
CMD ["node", "apps/web/server.js"]

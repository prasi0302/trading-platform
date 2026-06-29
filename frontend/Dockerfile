FROM node:20-alpine AS build

WORKDIR /app
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install
COPY frontend/ .
RUN npm run build

FROM nginx:alpine

# Install curl for healthcheck and create a non-root user.
RUN apk add --no-cache curl \
    && addgroup -S appgroup \
    && adduser -S -G appgroup appuser

# Copy built assets and the non-root nginx config (listens on 8080).
COPY --from=build /app/dist /usr/share/nginx/html
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf

# Make nginx writable directories owned by the non-root user.
RUN chown -R appuser:appgroup /var/cache/nginx /var/log/nginx /etc/nginx/conf.d /usr/share/nginx/html \
    && touch /var/run/nginx.pid \
    && chown appuser:appgroup /var/run/nginx.pid

USER appuser

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD ["curl", "-fsS", "http://127.0.0.1:8080/"]

CMD ["nginx", "-g", "daemon off;"]

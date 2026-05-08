FROM node:20-alpine AS builder

WORKDIR /app
COPY react/package.json react/package-lock.json ./
RUN npm ci
COPY react/ .
RUN npm run build

FROM nginx:1.27-alpine

COPY react/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

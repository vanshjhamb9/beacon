FROM node:22-alpine AS deps
WORKDIR /app
COPY package.json ./
COPY apps/dashboard/package.json ./apps/dashboard/package.json
RUN npm install

FROM node:22-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY --from=deps /app/apps/dashboard/node_modules ./apps/dashboard/node_modules
COPY . .
RUN npm --workspace apps/dashboard run build

FROM node:22-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
COPY --from=builder /app/package.json ./package.json
COPY --from=builder /app/apps/dashboard ./apps/dashboard
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/apps/dashboard/node_modules ./apps/dashboard/node_modules
WORKDIR /app/apps/dashboard
EXPOSE 3000
CMD ["npm", "run", "start"]

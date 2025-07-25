# --- Stage 1: Base Image ---
FROM node:18-alpine AS base
WORKDIR /app

# --- Stage 2: Dependencies (This gets cached) ---
FROM base AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm install

# --- Stage 3: Development Image (This is the target) ---
FROM base AS development
WORKDIR /app
# Copy the installed dependencies from the 'deps' stage
COPY --from=deps /app/node_modules ./node_modules
# Copy the rest of your app code
COPY . .

EXPOSE 3000

# The command to run is specified in docker-compose.yml for development
CMD ["npm", "run", "dev"]
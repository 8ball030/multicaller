# Stage 1: Build TypeScript source code
FROM node:16 AS builder

WORKDIR /app

COPY package*.json ./

RUN npm install

COPY . .

RUN npm run build

# Stage 2: Create a lightweight image for production
FROM node:16-alpine

WORKDIR /app

COPY package*.json ./

RUN npm install --only=production

# Copy only necessary files from the build stage
COPY --from=builder /app/server.js /app/server.js

# Expose the port your app will run on
EXPOSE 3000

# Start the application
CMD ["npm", "start"]

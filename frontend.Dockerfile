# Build stage
FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY frontend/package*.json ./

# Install dependencies
RUN npm install

# Copy project files
COPY frontend/ .

# Expose Vite development port
EXPOSE 5173

# Start development server
CMD ["npm", "run", "dev", "--", "--host"]

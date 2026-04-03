FROM node:20-alpine AS frontend-build
RUN apk add --no-cache python3 make g++
WORKDIR /app/frontend
COPY frontend/ ./
RUN npm install --legacy-peer-deps && npm install ajv@6.12.6
ENV CI=false
ENV GENERATE_SOURCEMAP=false
ENV NODE_OPTIONS=--max_old_space_size=4096
ENV ENABLE_HEALTH_CHECK=false
RUN npm rebuild
RUN REACT_APP_BACKEND_URL="/" npm run build

FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends gcc && rm -rf /var/lib/apt/lists/*
COPY backend/requirements.txt ./backend/
RUN pip install --no-cache-dir --extra-index-url https://d33sy5i8bnduwe.cloudfront.net/simple/ -r backend/requirements.txt
COPY backend/ ./backend/
COPY --from=frontend-build /app/frontend/build ./frontend/build
WORKDIR /app/backend
EXPOSE 8001
CMD ["sh", "-c", "uvicorn server:app --host 0.0.0.0 --port ${PORT:-8001}"]

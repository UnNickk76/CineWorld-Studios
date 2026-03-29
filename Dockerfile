# ===== BUILD =====
FROM node:18-alpine as build

WORKDIR /app

# Copia TUTTO il progetto
COPY . .

# Vai nel frontend
WORKDIR /app/frontend

RUN npm install
RUN npm run build

# ===== PRODUCTION =====
FROM node:18-alpine

WORKDIR /app

RUN npm install -g serve

COPY --from=build /app/frontend/build ./build

EXPOSE 3000

CMD ["serve", "-s", "build", "-l", "3000"]

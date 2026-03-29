# build stage
FROM node:18 AS build

WORKDIR /app

COPY frontend ./frontend

WORKDIR /app/frontend

RUN npm install
RUN npm run build

# production stage
FROM node:18

WORKDIR /app

COPY --from=build /app/frontend/build ./build
COPY frontend/server.js ./server.js
COPY frontend/package.json ./package.json

RUN npm install --omit=dev

EXPOSE 3000

CMD ["node", "server.js"]

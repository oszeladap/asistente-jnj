FROM node:24-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build -- --configuration production

FROM node:24-alpine
WORKDIR /app
RUN npm install -g serve@14
COPY --from=build /app/dist/frontend/browser ./browser
EXPOSE 3000
CMD ["sh", "-c", "serve -s browser -l ${PORT:-3000}"]

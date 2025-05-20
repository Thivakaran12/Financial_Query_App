################ 1. Build React ################
FROM node:18-slim AS builder
WORKDIR /usr/src/app

# copy lock-files and install deps
COPY package*.json ./
RUN npm ci

# copy the rest of the React app
COPY . .

ARG REACT_APP_API_URL=http://localhost:8000
ENV REACT_APP_API_URL=${REACT_APP_API_URL}

RUN npm run build

################ 2. Nginx stage ###############
FROM nginx:1.25-alpine

# Copy our custom conf into the container
COPY nginx/default.conf /etc/nginx/conf.d/default.conf

# Copy the built React app
COPY --from=builder /usr/src/app/build /usr/share/nginx/html

EXPOSE 80
CMD ["nginx","-g","daemon off;"]


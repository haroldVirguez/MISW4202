# Usar imagen de Node.js para construir la aplicación
FROM node:20.19-alpine AS builder

WORKDIR /app

# Copiar archivos de configuración
COPY package*.json ./
COPY angular.json ./
COPY tsconfig*.json ./

# Instalar dependencias
RUN npm ci

# Copiar código fuente
COPY src/ ./src/
COPY public/ ./public/

# Construir la aplicación para producción
RUN npm run build

# Usar nginx para servir la aplicación
FROM nginx:alpine

# Copiar archivos construidos al directorio de nginx
COPY --from=builder /app/dist/frontend /usr/share/nginx/html

# Copiar configuración personalizada de nginx
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Exponer puerto 80
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]

FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements
COPY requirements.txt .

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar todo el código de la aplicación
COPY . .

# Crear directorio para la base de datos
RUN mkdir -p /data

COPY docker-entrypoint-security.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint-security.sh

# Hacer los entry points ejecutables
RUN chmod +x entrypoints/entrypoint_*.py

# El comando será definido en docker-compose para cada servicio
# Por defecto, mostrar mensaje de ayuda
CMD ["echo", "Use docker-compose to run specific microservices"]

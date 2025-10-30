# Imagen base con Python y herramientas necesarias
FROM python:3.11-slim

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    curl \
    gcc \
    g++ \
    gnupg \
    pkg-config \
    libmariadb-dev \
    libffi-dev \
    libnss3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libx11-xcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libxkbcommon0 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libcairo2 \
    libasound2 \
    fonts-liberation \
    xdg-utils \
    && rm -rf /var/lib/apt/lists/*

# Crear directorio de trabajo
WORKDIR /app

# Copiar dependencias de Python
COPY requirements.txt .

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Instalar navegadores de Playwright (Chromium)
RUN playwright install --with-deps chromium

# Copiar el resto del proyecto
COPY . .

# Variables de entorno recomendadas
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=web_scraping.settings

# Exponer el puerto del servidor web
EXPOSE 8000

# Comando por defecto: usar gunicorn en producción
CMD ["gunicorn", "web_scraping.wsgi:application", "--bind", "0.0.0.0:8000"]
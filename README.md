# 📰 Web Scraping Django - Portal de Noticias El Comercio

Un sistema completo de **web scraping** desarrollado en Django para extraer, almacenar y mostrar noticias del periódico **El Comercio** (Perú) de manera automatizada. El proyecto incluye una interfaz web moderna para visualizar noticias por categorías con filtros avanzados y funcionalidades de búsqueda.

## 🎯 ¿De qué trata el proyecto?

Este proyecto es un **agregador de noticias inteligente** que:

- **Extrae automáticamente** noticias de El Comercio usando web scraping
- **Categoriza las noticias** en: Política, Economía, Mundo, Tecnología
- **Almacena** títulos, autores, fechas, imágenes y enlaces en base de datos
- **Presenta** las noticias en una interfaz web moderna y responsive
- **Ejecuta scraping** manual o programado por categorías específicas

## 🛠️ Tecnologías Utilizadas

### Backend
- **Django 5.2.6** - Framework web principal
- **Python 3.13** - Lenguaje de programación
- **MySQL** - Base de datos (mysqlclient)
- **Playwright** - Automatización de navegadores para scraping
- **BeautifulSoup4** - Parsing y extracción de datos HTML
- **Celery** - Tareas asíncronas (opcional)

### Frontend
- **HTML5/CSS3** - Interfaz de usuario
- **JavaScript** - Interactividad
- **Font Awesome** - Iconografía
- **CSS Grid/Flexbox** - Layout responsive

### Herramientas de Desarrollo
- **Git** - Control de versiones
- **Virtual Environment** - Aislamiento de dependencias
- **Django Management Commands** - Comandos personalizados

## 📋 Requisitos del Sistema

- **Python 3.13** o superior
- **pip** (gestor de paquetes de Python)
- **Git** (para clonar el repositorio)
- **MySQL** (base de datos)
- **Navegador web** (Chrome/Firefox para Playwright)

## 🚀 Guía de Instalación Completa

### Paso 1: Clonar el Repositorio
`ash
git clone <URL_DEL_REPOSITORIO>
cd web_Scraping
`

### Paso 2: Crear Entorno Virtual
`ash
# Windows (PowerShell)
python -m venv env
.\env\Scripts\Activate.ps1

# Windows (CMD)
python -m venv env
.\env\Scripts\activate.bat

# Linux/Mac
python -m venv env
source env/bin/activate
`

### Paso 3: Instalar Dependencias
`ash
pip install -r requirements.txt
`

### Paso 4: Instalar Navegadores de Playwright
`ash
playwright install
`

### Paso 5: Configurar Base de Datos

1. **Crear base de datos MySQL:**
   `sql
   CREATE DATABASE web_scraping_db;
   `

2. **Configurar settings.py** (si es necesario):
   `python
   DATABASES = {
       'default': {
           'ENGINE': 'django.db.backends.mysql',
           'NAME': 'web_scraping_db',
           'USER': 'tu_usuario',
           'PASSWORD': 'tu_contraseña',
           'HOST': 'localhost',
           'PORT': '3306',
       }
   }
   `

### Paso 6: Ejecutar Migraciones
`ash
python manage.py migrate
`

### Paso 7: Crear Superusuario (Opcional)
`ash
python manage.py createsuperuser
`

### Paso 8: Iniciar Servidor
`ash
python manage.py runserver
`

### Paso 9: Acceder a la Aplicación
Abre tu navegador y ve a: **http://127.0.0.1:8000/**

## 📖 Cómo Usar el Sistema

### 1. Visualizar Noticias
- **Página principal**: Todas las noticias
- **Categorías específicas**: /politica, /economia, /mundo, /tecnologia

### 2. Filtrar Contenido
- **Por fecha**: Hoy, última semana, último mes
- **Por imágenes**: Solo noticias con imágenes
- **Búsqueda**: Buscar por título o autor

### 3. Ejecutar Scraping
- **Botón "Scraping"** en cada página para extraer noticias
- **Comandos manuales**:
   `ash
   python manage.py scrape_elcomercio        # Todas las noticias
   python manage.py scrape_elcomercio_pol    # Solo política
   python manage.py scrape_economia          # Solo economía
   python manage.py scrape_mundo             # Solo mundo
   python manage.py scrape_tecnologia        # Solo tecnología
   `

## �� Estructura del Proyecto

`
web_Scraping/
├── �� scraping/                    # App principal
│   ├── 📄 models.py               # Modelo de datos (Noticia)
│   ├── 📄 views.py                # Vistas para cada categoría
│   ├── 📄 urls.py                 # Rutas de la aplicación
│   ├── 📁 management/commands/    # Comandos de scraping
│   │   ├── scrape_elcomercio.py
│   │   ├── scrape_elcomercio_pol.py
│   │   ├── scrape_economia.py
│   │   ├── scrape_mundo.py
│   │   └── scrape_tecnologia.py
│   ├── 📁 templates/noticias/     # Plantillas HTML
│   │   ├── lista.html
│   │   ├── politica.html
│   │   ├── economia.html
│   │   ├── mundo.html
│   │   └── tecnologia.html
│   └── 📁 static/css/            # Estilos CSS
│       └── noticias.css
├── 📁 web_scraping/              # Configuración Django
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── 📄 manage.py                  # Script de gestión Django
├── 📄 requirements.txt           # Dependencias Python
└── 📄 README.md                  # Este archivo
`

## 🔧 Comandos Útiles

### Desarrollo
`ash
# Iniciar servidor de desarrollo
python manage.py runserver

# Crear migraciones
python manage.py makemigrations

# Aplicar migraciones
python manage.py migrate

# Acceder al shell de Django
python manage.py shell
`

### Scraping
`ash
# Scraping completo
python manage.py scrape_elcomercio

# Scraping por categoría
python manage.py scrape_elcomercio_pol
python manage.py scrape_economia
python manage.py scrape_mundo
python manage.py scrape_tecnologia
`

### Base de Datos
`ash
# Ver estado de migraciones
python manage.py showmigrations

# Resetear base de datos (¡CUIDADO!)
python manage.py flush
`

## ⚙️ Configuración Avanzada

### Variables de Entorno (Opcional)
Crea un archivo .env en la raíz del proyecto:
`nv
SECRET_KEY=tu_clave_secreta_aqui
DEBUG=True
DATABASE_URL=mysql://usuario:password@localhost:3306/web_scraping_db
`

### Celery para Tareas Asíncronas
`ash
# Instalar Redis (requerido para Celery)
# Windows: Descargar de https://redis.io/download
# Linux: sudo apt-get install redis-server

# Ejecutar worker de Celery
celery -A web_scraping worker --loglevel=info
`

## 🐛 Solución de Problemas

### Error de Playwright
`ash
# Reinstalar navegadores
playwright install --force
`

### Error de Base de Datos
`ash
# Verificar conexión MySQL
python manage.py dbshell
`

### Error de Dependencias
`ash
# Reinstalar dependencias
pip install -r requirements.txt --force-reinstall
`

## 📊 Características del Sistema

- ✅ **Scraping inteligente** con detección automática de imágenes
- ✅ **Interfaz responsive** con diseño moderno
- ✅ **Filtros avanzados** por fecha, categoría y contenido
- ✅ **Búsqueda en tiempo real** por título y autor
- ✅ **Estadísticas automáticas** de noticias
- ✅ **Manejo de errores** robusto
- ✅ **Optimización de imágenes** automática
- ✅ **Navegación por categorías** intuitiva

## 🤝 Contribuir

1. Fork el proyecto
2. Crea una rama para tu feature (git checkout -b feature/AmazingFeature)
3. Commit tus cambios (git commit -m "Add some AmazingFeature")
4. Push a la rama (git push origin feature/AmazingFeature)
5. Abre un Pull Request

## 📝 Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para detalles.

## 👨‍💻 Autor

- **Tu Nombre** - [@tuusuario](https://github.com/tuusuario)

## 📞 Soporte

Si tienes problemas o preguntas:
- Abre un [Issue](https://github.com/tuusuario/web_Scraping/issues)
- Contacta: tu.email@ejemplo.com

---

**¡Disfruta scrapeando noticias! 📰✨**

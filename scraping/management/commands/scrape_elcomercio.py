from django.core.management.base import BaseCommand
from django.db import transaction
from scraping.models import Noticia
from playwright.sync_api import sync_playwright
from datetime import datetime
import re
from django.utils import timezone

class Command(BaseCommand):
    help = 'Scrapea noticias de El Comercio (versión arreglada para imágenes específicas)'
    
    def obtener_imagen_elcomercio(self, noticia_element):
        """Obtiene imágenes específicamente de El Comercio basado en el HTML proporcionado"""
        try:
            # Selectores específicos para El Comercio
            img_selectors = [
                "img.fs-wi__img",  # Clase específica de El Comercio
                "img[src*='elcomercio.pe/resizer']",  # URLs del resizer de El Comercio
                "img[data-src*='elcomercio.pe/resizer']",  # data-src con resizer
                ".fs-wi__img-link img",  # Imágenes dentro de enlaces
                "img.lazy",  # Imágenes con lazy loading
                "img[src]",  # Cualquier imagen con src
                "img[data-src]"  # Cualquier imagen con data-src
            ]
            
            mejor_imagen = None
            mejor_resolucion = 0
            
            for selector in img_selectors:
                try:
                    imgs = noticia_element.locator(selector).all()
                    
                    for img in imgs:
                        # Obtener diferentes fuentes de imagen
                        img_sources = [
                            img.get_attribute("src"),
                            img.get_attribute("data-src")
                        ]
                        
                        for src in img_sources:
                            if not src:
                                continue
                                
                            # Limpiar URL (manejar &amp;)
                            src = src.replace('&amp;', '&')
                            
                            # Validar que es una imagen válida
                            if not self.es_imagen_valida(src):
                                continue
                                
                            # Obtener resolución de la URL
                            resolucion = self.obtener_resolucion_url(src)
                            
                            # Si es de El Comercio y tiene mejor resolución
                            if 'elcomercio.pe' in src and resolucion > mejor_resolucion:
                                mejor_resolucion = resolucion
                                mejor_imagen = src
                                self.stdout.write(f"  🖼️ Imagen encontrada: {resolucion}p - {src[:80]}...")
                                
                except Exception as e:
                    continue
                    
            # Si no encontramos imagen de alta calidad, intentar mejorar una existente
            if not mejor_imagen or mejor_resolucion < 300:
                mejor_imagen = self.intentar_mejorar_imagen(noticia_element)
                
            return mejor_imagen
            
        except Exception as e:
            self.stdout.write(f"⚠️ Error obteniendo imagen: {e}")
            return None
    
    def es_imagen_valida(self, url):
        """Valida si es una URL de imagen válida"""
        if not url:
            return False
            
        # Filtrar URLs inválidas
        filtros_invalidos = [
            'data:image',
            'placeholder',
            'loading.gif',
            'spinner.gif',
            'blank.png',
            'default.jpg',
            '.svg'
        ]
        
        url_lower = url.lower()
        for filtro in filtros_invalidos:
            if filtro in url_lower:
                return False
                
        # Debe ser HTTP/HTTPS
        return url.startswith('http')
    
    def obtener_resolucion_url(self, url):
        """Extrae la resolución de la URL del resizer de El Comercio"""
        try:
            # Buscar parámetros width y height en URLs de El Comercio
            width_match = re.search(r'width=(\d+)', url)
            height_match = re.search(r'height=(\d+)', url)
            
            if width_match and height_match:
                width = int(width_match.group(1))
                height = int(height_match.group(1))
                return max(width, height)  # Retornar la dimensión mayor
                
            # Si solo hay width
            elif width_match:
                return int(width_match.group(1))
                
            # Patrones alternativos
            resolution_patterns = re.findall(r'(\d+)x(\d+)', url)
            if resolution_patterns:
                width, height = map(int, resolution_patterns[-1])
                return max(width, height)
                
            # Valores por defecto según patrones conocidos
            if 'thumb' in url.lower():
                return 100
            elif 'small' in url.lower():
                return 200  
            elif 'medium' in url.lower():
                return 400
            elif 'large' in url.lower():
                return 800
                
            return 300  # Valor por defecto
            
        except Exception:
            return 0
    
    def intentar_mejorar_imagen(self, noticia_element):
        """Intenta mejorar la calidad de imagen modificando parámetros de URL"""
        try:
            # Buscar cualquier imagen de El Comercio
            img = noticia_element.locator("img[src*='elcomercio.pe'], img[data-src*='elcomercio.pe']").first
            
            if img:
                src = img.get_attribute("src") or img.get_attribute("data-src")
                if src:
                    # Limpiar &amp;
                    src = src.replace('&amp;', '&')
                    
                    # Mejorar calidad modificando parámetros
                    src_mejorada = self.mejorar_url_imagen(src)
                    self.stdout.write(f"  📈 Mejorando imagen: {src_mejorada[:80]}...")
                    return src_mejorada
                    
        except Exception:
            pass
            
        return None
    
    def mejorar_url_imagen(self, url):
        """Mejora la calidad de imagen modificando parámetros de URL"""
        try:
            # Para URLs del resizer de El Comercio
            if 'elcomercio.pe/resizer' in url:
                # Aumentar width y height
                url = re.sub(r'width=\d+', 'width=800', url)
                url = re.sub(r'height=\d+', 'height=600', url)
                # Mejorar calidad
                url = re.sub(r'quality=\d+', 'quality=85', url)
                return url
                
        except Exception:
            pass
            
        return url
    
    def obtener_enlace_noticia(self, noticia_element):
        """Obtiene el enlace a la noticia completa"""
        try:
            # Selectores específicos para enlaces de El Comercio
            link_selectors = [
                ".fs-wi__img-link",  # Enlaces de imagen
                ".fs-wi__title a",   # Enlaces en títulos
                "a[href*='/noticia/']",  # Enlaces que contienen /noticia/
                "a[data-mrf-link]",  # Enlaces con data-mrf-link
                "a[href]"  # Cualquier enlace
            ]
            
            for selector in link_selectors:
                try:
                    link = noticia_element.locator(selector).first
                    href = link.get_attribute("href") or link.get_attribute("data-mrf-link")
                    
                    if href:
                        # Convertir a URL absoluta si es necesario
                        if href.startswith('/'):
                            href = 'https://elcomercio.pe' + href
                        elif not href.startswith('http'):
                            href = 'https://elcomercio.pe/' + href
                            
                        # Validar que es un enlace de noticia válido
                        if 'elcomercio.pe' in href:
                            return href
                            
                except Exception:
                    continue
                    
            return None
            
        except Exception:
            return None

    def handle(self, *args, **kwargs):
        noticias_para_guardar = []
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0 Safari/537.36"
            )
            page = context.new_page()
            
            try:
                self.stdout.write("🌐 Navegando a El Comercio...")
                page.goto("https://elcomercio.pe", timeout=60000, wait_until="domcontentloaded")
                
                # Esperar a que carguen las noticias
                page.wait_for_selector(".fs-wi", timeout=15000)
                
                # Scroll para cargar más imágenes lazy
                self.stdout.write("📜 Haciendo scroll para cargar imágenes...")
                for _ in range(3):
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    page.wait_for_timeout(2000)
                
                noticias = page.locator(".fs-wi").all()
                self.stdout.write(f"📰 Se encontraron {len(noticias)} noticias.")
                
                for i, noticia in enumerate(noticias):
                    try:
                        self.stdout.write(f"📄 Procesando noticia {i+1}/{len(noticias)}")
                        
                        # Título
                        try:
                            titulo = noticia.locator(".fs-wi__title, .story-item__content-title.overflow-hidden").inner_text(timeout=5000).strip()
                        except:
                            titulo = "Sin título"
                        
                        # Autor
                        try:
                            autor = noticia.locator(".fs-wi__authors a").inner_text(timeout=5000).strip()
                        except:
                            autor = "Redacción El Comercio"
                        
                        # Fecha
                        try:
                            fecha_str = noticia.locator("time").get_attribute("datetime", timeout=5000)
                            if fecha_str:
                                fecha = datetime.fromisoformat(fecha_str.replace("Z", "+00:00"))
                            else:
                                fecha = timezone.localtime(timezone.now())  # fecha actual en Lima
                        except:
                            fecha = timezone.localtime(timezone.now())  # fallback
                        
                        # Imagen mejorada específica para El Comercio
                        imagen = self.obtener_imagen_elcomercio(noticia)
                        
                        # Enlace a la noticia
                        enlace = self.obtener_enlace_noticia(noticia)
                        
                        noticia_data = {
                            'titulo': titulo,
                            'autor': autor,
                            'fecha': fecha,
                            'imagen': imagen,
                            'enlace': enlace
                        }
                        
                        noticias_para_guardar.append(noticia_data)
                        
                        # Debug info
                        if imagen:
                            resolucion = self.obtener_resolucion_url(imagen)
                            self.stdout.write(f"  ✅ Imagen: {resolucion}p - {titulo[:30]}...")
                        else:
                            self.stdout.write(f"  ⚠️ Sin imagen: {titulo[:30]}...")
                            
                    except Exception as e:
                        self.stdout.write(f"❌ Error procesando noticia {i+1}: {e}")
                        continue
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Error durante el scraping: {e}"))
            finally:
                browser.close()
        
        # Guardar en base de datos con manejo de errores
        if noticias_para_guardar:
            self.stdout.write(f"💾 Guardando {len(noticias_para_guardar)} noticias...")
            
            noticias_nuevas = 0
            noticias_actualizadas = 0
            errores = 0
            
            with transaction.atomic():
                for data in noticias_para_guardar:
                    try:
                        # Truncar campos si son muy largos
                        titulo = data['titulo'][:250] if data['titulo'] else "Sin título"
                        autor = data['autor'][:250] if data['autor'] else "Redacción"
                        
                        noticia, created = Noticia.objects.get_or_create(
                            titulo=titulo,
                            origen='elcomercio',
                            defaults={
                                'autor': autor,
                                'fecha': data['fecha'],
                                'imagen': data['imagen'],
                                'enlace': data['enlace']
                            }
                        )
                        
                        if created:
                            noticias_nuevas += 1
                            self.stdout.write(f"  ✅ Nueva: {titulo[:40]}...")
                        else:
                            # Actualizar imagen si la nueva es mejor
                            if data['imagen'] and (not noticia.imagen or 
                                self.obtener_resolucion_url(data['imagen']) > self.obtener_resolucion_url(noticia.imagen or "")):
                                noticia.imagen = data['imagen']
                                noticia.save()
                                noticias_actualizadas += 1
                                self.stdout.write(f"  🔄 Actualizada: {titulo[:40]}...")
                            else:
                                self.stdout.write(f"  ⚪ Existente: {titulo[:40]}...")
                                
                    except Exception as e:
                        errores += 1
                        self.stdout.write(f"  ❌ Error guardando: {e}")
                        continue
                
                self.stdout.write(f"📊 Resumen:")
                self.stdout.write(f"  ✅ Noticias nuevas: {noticias_nuevas}")
                self.stdout.write(f"  🔄 Noticias actualizadas: {noticias_actualizadas}")
                self.stdout.write(f"  ❌ Errores: {errores}")
        
        self.stdout.write(self.style.SUCCESS("✅ Scraping finalizado!"))
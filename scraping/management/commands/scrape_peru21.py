from django.core.management.base import BaseCommand
from django.db import transaction
from scraping.models import Noticia
from playwright.sync_api import sync_playwright
from datetime import datetime
import re
from django.utils import timezone


class Command(BaseCommand):
    help = 'Scrapea noticias de Perú21'

    def obtener_imagen_peru21(self, noticia_element):
        """Obtiene la imagen principal de cada noticia"""
        try:
            img = noticia_element.locator("img.image-style-teaser-liquido").first
            src = img.get_attribute("src")
            if src:
                if src.startswith('/'):
                    src = "https://peru21.pe" + src
                return src.replace("&amp;", "&")
        except Exception as e:
            self.stdout.write(f"⚠️ Error obteniendo imagen: {e}")
        return None

    def obtener_enlace_noticia(self, noticia_element):
        """Obtiene el enlace de la noticia"""
        try:
            link = noticia_element.locator(".col-teaser-liquido-media a").first
            href = link.get_attribute("href")
            if href:
                if href.startswith('/'):
                    href = "https://peru21.pe" + href
                return href
        except Exception:
            pass
        return None

    def obtener_resolucion_url(self, url):
        """Devuelve resolución aproximada de la URL de imagen"""
        if not url:
            return 0
        try:
            width_match = re.search(r'width=(\d+)', url)
            height_match = re.search(r'height=(\d+)', url)
            if width_match and height_match:
                return max(int(width_match.group(1)), int(height_match.group(1)))
        except Exception:
            pass
        return 300  # valor por defecto

    def handle(self, *args, **kwargs):
        noticias_para_guardar = []
        noticias_saltadas = 0

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0 Safari/537.36"
            )
            page = context.new_page()

            try:
                self.stdout.write("🌐 Navegando a Perú21...")
                page.goto("https://peru21.pe", timeout=60000, wait_until="domcontentloaded")
                page.wait_for_selector("article.node--type-article", timeout=15000)

                total = page.locator("article.node--type-article").count()
                self.stdout.write(f"📰 Se encontraron {total} artículos.")

                for i in range(total):
                    try:
                        art = page.locator("article.node--type-article").nth(i)

                        # Título
                        titulo_el = art.locator(".titulo-teaser-liquido a")
                        if not titulo_el.count():
                            noticias_saltadas += 1
                            continue
                        titulo = titulo_el.inner_text(timeout=2000).strip()

                        # Autor
                        autor = (
                            art.locator(".firma-teaser-liquido a").inner_text(timeout=2000).strip()
                            if art.locator(".firma-teaser-liquido a").count()
                            else "Redacción Perú21"
                        )

                        # Fecha
                        fecha_str = art.locator("time").get_attribute("datetime") if art.locator("time").count() else None
                        fecha = (
                            datetime.fromisoformat(fecha_str.replace("Z", "+00:00"))
                            if fecha_str
                            else timezone.localtime(timezone.now())
                        )

                        # Imagen y enlace
                        imagen = self.obtener_imagen_peru21(art)
                        enlace = self.obtener_enlace_noticia(art)

                        if not enlace:  # si no hay enlace, descartar
                            noticias_saltadas += 1
                            continue

                        noticias_para_guardar.append({
                            'titulo': titulo,
                            'autor': autor,
                            'fecha': fecha,
                            'imagen': imagen,
                            'enlace': enlace
                        })
                        self.stdout.write(f"  ✅ {titulo[:60]}...")

                    except Exception:
                        noticias_saltadas += 1
                        continue

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Error durante el scraping: {e}"))
            finally:
                browser.close()

        # Guardar en base de datos
        if noticias_para_guardar:
            self.stdout.write(f"💾 Guardando {len(noticias_para_guardar)} noticias...")
            noticias_nuevas = 0
            noticias_actualizadas = 0
            errores = 0

            with transaction.atomic():
                for data in noticias_para_guardar:
                    try:
                        titulo = data['titulo'][:250]
                        autor = data['autor'][:250]

                        # 🔑 Usar enlace como clave principal
                        noticia, created = Noticia.objects.get_or_create(
                            enlace=data['enlace'],
                            origen='peru21',
                            defaults={
                                'titulo': titulo,
                                'autor': autor,
                                'fecha': data['fecha'],
                                'imagen': data['imagen']
                            }
                        )

                        if created:
                            noticias_nuevas += 1
                            self.stdout.write(f"  ✅ Nueva: {titulo[:50]}...")
                        else:
                            actualizado = False

                            # Actualizar título si cambió
                            if noticia.titulo != titulo:
                                noticia.titulo = titulo
                                actualizado = True

                            # Actualizar autor si cambió
                            if noticia.autor != autor:
                                noticia.autor = autor
                                actualizado = True

                            # Actualizar fecha si es más reciente
                            if data['fecha'] and data['fecha'] > noticia.fecha:
                                noticia.fecha = data['fecha']
                                actualizado = True

                            # Actualizar imagen si es mejor
                            nueva_res = self.obtener_resolucion_url(data['imagen'] or "")
                            vieja_res = self.obtener_resolucion_url(noticia.imagen or "")
                            if data['imagen'] and (not noticia.imagen or nueva_res > vieja_res):
                                noticia.imagen = data['imagen']
                                actualizado = True

                            if actualizado:
                                noticia.save()
                                noticias_actualizadas += 1
                                self.stdout.write(f"  🔄 Actualizada: {titulo[:50]}...")
                            else:
                                self.stdout.write(f"  ⚪ Existente: {titulo[:50]}...")

                    except Exception as e:
                        errores += 1
                        self.stdout.write(f"  ❌ Error guardando: {e}")
                        continue

                # 📊 Resumen final
                self.stdout.write(self.style.SUCCESS("📊 Resumen final:"))
                self.stdout.write(f"  ✅ Noticias nuevas: {noticias_nuevas}")
                self.stdout.write(f"  🔄 Noticias actualizadas: {noticias_actualizadas}")
                self.stdout.write(f"  ⚪ Saltadas / sin título: {noticias_saltadas}")
                self.stdout.write(f"  ❌ Errores al guardar: {errores}")

        self.stdout.write(self.style.SUCCESS("✅ Scraping finalizado!"))

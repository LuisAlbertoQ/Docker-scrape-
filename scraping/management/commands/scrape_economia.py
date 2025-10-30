from django.core.management.base import BaseCommand
from django.db import transaction
from scraping.models import Noticia
from playwright.sync_api import sync_playwright
from datetime import datetime
from urllib.parse import urljoin
import re
from django.utils import timezone

BASE_URL = "https://elcomercio.pe/economia"


class Command(BaseCommand):
    help = 'Scrapea noticias de la sección Economia de El Comercio'

    def obtener_imagen_elcomercio(self, noticia_element):
        """Obtiene imágenes de mejor calidad posible"""
        try:
            img_selectors = [
                "img.fs-wi__img",
                "img[src*='elcomercio.pe/resizer']",
                "img[data-src*='elcomercio.pe/resizer']",
                ".fs-wi__img-link img",
                "img.lazy",
                "img[src]",
                "img[data-src]"
            ]

            mejor_imagen = None
            mejor_resolucion = 0

            for selector in img_selectors:
                try:
                    imgs = noticia_element.locator(selector).all()
                    for img in imgs:
                        img_sources = [
                            img.get_attribute("src"),
                            img.get_attribute("data-src")
                        ]

                        for src in img_sources:
                            if not src:
                                continue
                            src = src.replace("&amp;", "&")

                            if not self.es_imagen_valida(src):
                                continue

                            resolucion = self.obtener_resolucion_url(src)
                            if "elcomercio.pe" in src and resolucion > mejor_resolucion:
                                mejor_resolucion = resolucion
                                mejor_imagen = src
                except Exception:
                    continue

            if not mejor_imagen or mejor_resolucion < 300:
                mejor_imagen = self.intentar_mejorar_imagen(noticia_element)

            return mejor_imagen

        except Exception:
            return None

    def es_imagen_valida(self, url):
        if not url:
            return False

        filtros_invalidos = [
            "data:image", "placeholder", "loading.gif",
            "spinner.gif", "blank.png", "default.jpg", ".svg"
        ]
        url_lower = url.lower()
        for f in filtros_invalidos:
            if f in url_lower:
                return False

        return url.startswith("http")

    def obtener_resolucion_url(self, url):
        try:
            width_match = re.search(r"width=(\d+)", url)
            height_match = re.search(r"height=(\d+)", url)

            if width_match and height_match:
                return max(int(width_match.group(1)), int(height_match.group(1)))
            elif width_match:
                return int(width_match.group(1))

            resolution_patterns = re.findall(r"(\d+)x(\d+)", url)
            if resolution_patterns:
                w, h = map(int, resolution_patterns[-1])
                return max(w, h)

            if "thumb" in url.lower():
                return 100
            elif "small" in url.lower():
                return 200
            elif "medium" in url.lower():
                return 400
            elif "large" in url.lower():
                return 800

            return 300
        except Exception:
            return 0

    def intentar_mejorar_imagen(self, noticia_element):
        try:
            img = noticia_element.locator(
                "img[src*='elcomercio.pe'], img[data-src*='elcomercio.pe']"
            ).first
            if img:
                src = img.get_attribute("src") or img.get_attribute("data-src")
                if src:
                    src = src.replace("&amp;", "&")
                    return self.mejorar_url_imagen(src)
        except Exception:
            return None

    def mejorar_url_imagen(self, url):
        try:
            if "elcomercio.pe/resizer" in url:
                url = re.sub(r"width=\d+", "width=800", url)
                url = re.sub(r"height=\d+", "height=600", url)
                url = re.sub(r"quality=\d+", "quality=85", url)
                return url
        except Exception:
            pass
        return url

    def obtener_enlace_noticia(self, noticia_element):
        """Obtiene el enlace de la noticia con urljoin para evitar duplicados"""
        try:
            link_selectors = [
                ".fs-wi__img-link",
                ".fs-wi__title a",
                "a[href*='/noticia/']",
                "a[data-mrf-link]",
                "a[href]"
            ]

            for selector in link_selectors:
                try:
                    link = noticia_element.locator(selector).first
                    href = link.get_attribute("href") or link.get_attribute("data-mrf-link")
                    if href:
                        href = urljoin(BASE_URL, href)  # ✅ corrige duplicados
                        if "elcomercio.pe" in href:
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
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                           "(KHTML, like Gecko) Chrome/115.0 Safari/537.36"
            )
            page = context.new_page()

            try:
                self.stdout.write("🌐 Navegando a El Comercio - Economia...")
                page.goto(BASE_URL, timeout=60000, wait_until="domcontentloaded")

                page.wait_for_selector(".fs-wi", timeout=15000)

                self.stdout.write("📜 Haciendo scroll para cargar imágenes...")
                for _ in range(3):
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    page.wait_for_timeout(2000)

                noticias = page.locator(".fs-wi").all()
                self.stdout.write(f"📰 Se encontraron {len(noticias)} noticias.")

                for i, noticia in enumerate(noticias):
                    try:
                        self.stdout.write(f"📄 Procesando noticia {i+1}/{len(noticias)}")

                        try:
                            titulo = noticia.locator(".fs-wi__title, .story-item__content-title overflow-hidden").inner_text(timeout=5000).strip()
                        except:
                            titulo = "Sin título"

                        try:
                            autor = noticia.locator(".fs-wi__authors a").inner_text(timeout=5000).strip()
                        except:
                            autor = "Redacción El Comercio"

                        try:
                            fecha_str = noticia.locator("time").get_attribute("datetime", timeout=5000)
                            if fecha_str:
                                fecha = datetime.fromisoformat(fecha_str.replace("Z", "+00:00"))
                            else:
                                fecha = timezone.localtime(timezone.now())  # fecha actual en Lima
                        except:
                            fecha = timezone.localtime(timezone.now())  # fallback

                        imagen = self.obtener_imagen_elcomercio(noticia)
                        enlace = self.obtener_enlace_noticia(noticia)

                        noticia_data = {
                            "titulo": titulo,
                            "autor": autor,
                            "fecha": fecha,
                            "imagen": imagen,
                            "enlace": enlace
                        }
                        noticias_para_guardar.append(noticia_data)

                    except Exception as e:
                        self.stdout.write(f"❌ Error procesando noticia {i+1}: {e}")
                        continue

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Error durante el scraping: {e}"))
            finally:
                browser.close()

        if noticias_para_guardar:
            self.stdout.write(f"💾 Guardando {len(noticias_para_guardar)} noticias...")
            noticias_nuevas, noticias_actualizadas, errores = 0, 0, 0

            with transaction.atomic():
                for data in noticias_para_guardar:
                    try:
                        titulo = data["titulo"][:250] if data["titulo"] else "Sin título"
                        autor = data["autor"][:250] if data["autor"] else "Redacción"

                        noticia, created = Noticia.objects.get_or_create(
                            titulo=titulo,
                            origen='elcomercio',
                            defaults={
                                "autor": autor,
                                "fecha": data["fecha"],
                                "imagen": data["imagen"],
                                "enlace": data["enlace"]
                            }
                        )

                        if created:
                            noticias_nuevas += 1
                        else:
                            if data["imagen"] and (
                                not noticia.imagen or
                                self.obtener_resolucion_url(data["imagen"]) > self.obtener_resolucion_url(noticia.imagen or "")
                            ):
                                noticia.imagen = data["imagen"]
                                noticia.save()
                                noticias_actualizadas += 1
                    except Exception as e:
                        errores += 1
                        self.stdout.write(f"  ❌ Error guardando: {e}")
                        continue

            self.stdout.write(f"📊 Resumen:")
            self.stdout.write(f"  ✅ Noticias nuevas: {noticias_nuevas}")
            self.stdout.write(f"  🔄 Noticias actualizadas: {noticias_actualizadas}")
            self.stdout.write(f"  ❌ Errores: {errores}")

        self.stdout.write(self.style.SUCCESS("✅ Scraping de economia finalizado!"))
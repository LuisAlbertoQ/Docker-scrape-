from django.core.management.base import BaseCommand
from django.db import transaction
from scraping.models import Noticia
from playwright.sync_api import sync_playwright
from datetime import datetime
from urllib.parse import urljoin
from django.utils import timezone
import re

BASE_URL = "https://peru21.pe/gastronomia"


class Command(BaseCommand):
    help = 'Scrapea noticias de la sección Deportes de Perú21'

    def obtener_imagen_peru21(self, noticia_element):
        try:
            img = noticia_element.locator("img.img-fluid").first
            if img:
                src = img.get_attribute("src")
                if src and src.startswith("/"):
                    src = urljoin(BASE_URL, src)
                return src
        except Exception:
            return None
        return None

    def obtener_enlace_noticia(self, noticia_element):
        try:
            link = noticia_element.locator("a[href*='/gastronomia/']").first
            if link:
                href = link.get_attribute("href")
                if href:
                    return urljoin(BASE_URL, href)
        except Exception:
            return None
        return None

    def handle(self, *args, **kwargs):
        noticias_para_guardar = []

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                           "AppleWebKit/537.36 (KHTML, like Gecko) "
                           "Chrome/115.0 Safari/537.36"
            )
            page = context.new_page()

            try:
                self.stdout.write("🌐 Navegando a Perú21 - Gastronomia...")
                page.goto(BASE_URL, timeout=60000, wait_until="domcontentloaded")

                page.wait_for_selector("article.node--type-article", timeout=15000)

                self.stdout.write("📜 Haciendo scroll para cargar más noticias...")
                for _ in range(3):
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    page.wait_for_timeout(2000)

                noticias = page.locator("article.node--type-article").all()
                self.stdout.write(f"📰 Se encontraron {len(noticias)} noticias.")

                for i, noticia in enumerate(noticias):
                    try:
                        self.stdout.write(f"📄 Procesando noticia {i+1}/{len(noticias)}")

                        # título
                        try:
                            titulo = noticia.locator(
                                ".titulo-teaser-liquido a, .titulo-teaser-2col a, h2 a"
                            ).inner_text(timeout=5000).strip()
                        except:
                            titulo = "Sin título"

                        # autor
                        try:
                            autor = noticia.locator(
                                ".firma-teaser-liquido a, .firma-teaser-2col a"
                            ).inner_text(timeout=5000).strip()
                        except:
                            autor = "Redacción Perú21"

                        # fecha
                        try:
                            fecha_str = (
                                noticia.locator("time")
                                .get_attribute("datetime")
                            )
                            if not fecha_str:
                                fecha_str = noticia.locator(
                                    ".field--name-field-fecha-actualizacion"
                                ).inner_text()
                            fecha = (
                                datetime.fromisoformat(fecha_str.replace("Z", "+00:00"))
                                if fecha_str else timezone.localtime(timezone.now())
                            )
                        except:
                            fecha = timezone.localtime(timezone.now())

                        # imagen y enlace
                        imagen = self.obtener_imagen_peru21(noticia)
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

        # Guardado en DB
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
                            origen='peru21',
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
                            if data["imagen"] and not noticia.imagen:
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

        self.stdout.write(self.style.SUCCESS("✅ Scraping de Gastronomia Perú21 finalizado!"))
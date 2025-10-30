from django.core.management.base import BaseCommand
from scraping.utils.beat_cleaner import clean_if_schedule_changed
import subprocess
import sys

class Command(BaseCommand):
    help = "Arranca Celery Beat limpiando schedule si cambió la config."

    def handle(self, *args, **options):
        clean_if_schedule_changed()
        try:
            subprocess.run(
                [sys.executable, "-m", "celery", "-A", "web_scraping", "beat", "--loglevel=info"],
                check=True
            )
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING("Beat detenido por el usuario."))
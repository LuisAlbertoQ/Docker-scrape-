from celery import shared_task
from django.core.management import call_command

@shared_task
def scrape_all_sections():
    call_command('scrape_elcomercio')
    call_command('scrape_economia')
    call_command('scrape_elcomercio_pol')
    call_command('scrape_mundo')
    call_command('scrape_tecnologia')
    call_command('scrape_peru21')
    call_command('scrape_peru21D')
    call_command('scrape_peru21G')
    call_command('scrape_peru21I')
    call_command('scrape_peru21L')
from django.urls import path
from . import views

urlpatterns = [
    path('', views.lista_noticias, name='lista_noticias'),
    path('scraping/lista', views.ejecutar_scraping_lista_noticias, name='scraping_lista_noticias'),
    path('politica', views.politica, name='politica'),
    path('scraping/politica', views.ejecutar_scraping_politica, name='scraping_politica'),
    path('economia', views.economia, name='economia'),
    path('scraping/economia', views.ejecutar_scraping_economia, name='scraping_economia'),
    path('mundo', views.mundo, name='mundo'),
    path('scraping/mundo', views.ejecutar_scraping_mundo, name='scraping_mundo'),
    path('tecnologia', views.tecnologia, name='tecnologia'),
    path('scraping/tecnologia', views.ejecutar_scraping_tecnologia, name='scraping_tecnologia'),
    #Peru21
    path('peru21', views.peru21, name='peru21'),
    path('scraping/peru21', views.ejecutar_scraping_peru21, name='scraping_peru21'),
    path('peru21/deportes', views.peru21d, name='peru21d'),
    path('scraping/peru21/deportes', views.ejecutar_scraping_peru21_deportes, name='scraping_peru21_deportes'),
    path('peru21/gastronomia', views.peru21g, name='peru21g'),
    path('scraping/peru21/gastronomia', views.ejecutar_scraping_peru21_gastronomia, name='scraping_peru21_gastronomia'),
    path('peru21/investigacion', views.peru21i, name='peru21i'),
    path('scraping/peru21/investigacion', views.ejecutar_scraping_peru21_investigacion, name='scraping_peru21_investigacion'),
    path('peru21/lima', views.peru21l, name='peru21l'),
    path('scraping/peru21/lima', views.ejecutar_scraping_peru21_lima, name='scraping_peru21_lima'),
]
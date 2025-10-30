import io
from django.shortcuts import render
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta, datetime
from .models import Noticia
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import JsonResponse
from django.core.management import call_command

# Función helper mejorada para manejar lógica común de listas de noticias
def lista_noticias_helper(request, queryset_base, template_name, nav_type='comercio'):
    # Obtener filtros desde GET
    filtro_imagen = request.GET.get('con_imagen', '')
    filtro_fecha = request.GET.get('fecha', 'todas')
    fecha_desde = request.GET.get('fecha_desde', '')
    fecha_hasta = request.GET.get('fecha_hasta', '')
    busqueda = request.GET.get('q', '')
    
    noticias = queryset_base
    
    # ===== FILTRO POR BÚSQUEDA =====
    if busqueda:
        noticias = noticias.filter(
            Q(titulo__icontains=busqueda) | 
            Q(autor__icontains=busqueda)
        )
    
    # ===== FILTRO POR IMAGEN =====
    if filtro_imagen == '1':
        noticias = noticias.exclude(imagen__isnull=True).exclude(imagen='')
    
    # ===== FILTRO POR FECHA =====
    now = timezone.now()
    
    if filtro_fecha == 'hoy':
        # Noticias de hoy
        inicio_dia = now.replace(hour=0, minute=0, second=0, microsecond=0)
        noticias = noticias.filter(fecha__gte=inicio_dia)
        
    elif filtro_fecha == 'ayer':
        # Noticias de ayer
        ayer = now - timedelta(days=1)
        inicio_ayer = ayer.replace(hour=0, minute=0, second=0, microsecond=0)
        fin_ayer = ayer.replace(hour=23, minute=59, second=59, microsecond=999999)
        noticias = noticias.filter(fecha__gte=inicio_ayer, fecha__lte=fin_ayer)
        
    elif filtro_fecha == 'semana':
        # Últimos 7 días
        hace_una_semana = now - timedelta(days=7)
        noticias = noticias.filter(fecha__gte=hace_una_semana)
        
    elif filtro_fecha == 'mes':
        # Últimos 30 días
        hace_un_mes = now - timedelta(days=30)
        noticias = noticias.filter(fecha__gte=hace_un_mes)
        
    elif filtro_fecha == 'rango' and fecha_desde and fecha_hasta:
        # Rango personalizado
        try:
            fecha_inicio = datetime.strptime(fecha_desde, '%Y-%m-%d')
            fecha_fin = datetime.strptime(fecha_hasta, '%Y-%m-%d')
            
            # Hacer timezone aware
            fecha_inicio = timezone.make_aware(fecha_inicio.replace(hour=0, minute=0, second=0))
            fecha_fin = timezone.make_aware(fecha_fin.replace(hour=23, minute=59, second=59))
            
            noticias = noticias.filter(fecha__gte=fecha_inicio, fecha__lte=fecha_fin)
        except ValueError:
            # Si hay error en las fechas, ignorar el filtro
            pass
    
    # ===== ORDENAMIENTO =====
    noticias = noticias.order_by('-fecha', '-fecha_scraping')
    
    # ===== PAGINACIÓN =====
    page = request.GET.get('page', 1)
    per_page = request.GET.get('per_page', 10)
    
    try:
        per_page = int(per_page)
        if per_page not in [10, 20, 50]:
            per_page = 10
    except (ValueError, TypeError):
        per_page = 10
    
    paginator = Paginator(noticias, per_page)
    
    try:
        noticias_paginadas = paginator.page(page)
    except PageNotAnInteger:
        noticias_paginadas = paginator.page(1)
    except EmptyPage:
        noticias_paginadas = paginator.page(paginator.num_pages)
    
    # ===== ESTADÍSTICAS =====
    total_noticias = noticias.count()
    noticias_con_imagen = noticias.exclude(imagen__isnull=True).exclude(imagen='').count()
    
    # ===== CONTEXTO =====
    context = {
        'noticias': noticias_paginadas,
        'total_noticias': total_noticias,
        'noticias_con_imagen': noticias_con_imagen,
        'nav_type': nav_type,
        'filtro_actual': {
            'imagen': filtro_imagen == '1',
            'fecha': filtro_fecha,
            'busqueda': busqueda,
            'fecha_desde': fecha_desde,
            'fecha_hasta': fecha_hasta,
        },
        'today': timezone.now().date(),
        'paginator': paginator
    }
    
    return render(request, template_name, context)

# ===== VISTAS PARA EL COMERCIO =====
def lista_noticias(request):
    queryset = Noticia.objects.filter(Q(origen="elcomercio") | Q(origen="desconocido"))
    return lista_noticias_helper(request, queryset, 'noticias/lista.html', nav_type='comercio')

def politica(request):
    queryset = Noticia.objects.filter(
        Q(origen="elcomercio") | Q(origen="desconocido"), 
        enlace__icontains="/politica/"
    )
    return lista_noticias_helper(request, queryset, 'noticias/politica.html', nav_type='comercio')

def economia(request):
    queryset = Noticia.objects.filter(
        Q(origen="elcomercio") | Q(origen="desconocido"), 
        enlace__icontains="/economia/"
    )
    return lista_noticias_helper(request, queryset, 'noticias/economia.html', nav_type='comercio')

def mundo(request):
    queryset = Noticia.objects.filter(
        Q(origen="elcomercio") | Q(origen="desconocido"), 
        enlace__icontains="/mundo/"
    )
    return lista_noticias_helper(request, queryset, 'noticias/mundo.html', nav_type='comercio')

def tecnologia(request):
    queryset = Noticia.objects.filter(
        Q(origen="elcomercio") | Q(origen="desconocido"), 
        enlace__icontains="/tecnologia/"
    )
    return lista_noticias_helper(request, queryset, 'noticias/tecnologia.html', nav_type='comercio')

# ===== VISTAS PARA PERU21 =====
def peru21(request):
    queryset = Noticia.objects.filter(origen='peru21')
    return lista_noticias_helper(request, queryset, 'peru21/peru21.html', nav_type='peru21')

def peru21d(request):
    queryset = Noticia.objects.filter(origen='peru21', enlace__icontains="/deportes/")
    return lista_noticias_helper(request, queryset, 'peru21/peru21d.html', nav_type='peru21')

def peru21g(request):
    queryset = Noticia.objects.filter(origen='peru21', enlace__icontains="/gastronomia/")
    return lista_noticias_helper(request, queryset, 'peru21/peru21g.html', nav_type='peru21')

def peru21i(request):
    queryset = Noticia.objects.filter(origen='peru21', enlace__icontains="/investigacion/")
    return lista_noticias_helper(request, queryset, 'peru21/peru21i.html', nav_type='peru21')

def peru21l(request):
    queryset = Noticia.objects.filter(origen='peru21', enlace__icontains="/lima/")
    return lista_noticias_helper(request, queryset, 'peru21/peru21l.html', nav_type='peru21')

# ===== VISTAS DE SCRAPING =====
def ejecutar_scraping_generico(request, command_name):
    """Vista genérica para ejecutar comandos de scraping"""
    if request.method == "POST":
        buffer = io.StringIO()
        try:
            call_command(command_name, stdout=buffer)
            output = buffer.getvalue()
            return JsonResponse({
                "status": "ok", 
                "log": output,
                "message": "Scraping completado exitosamente"
            })
        except Exception as e:
            return JsonResponse({
                "status": "error", 
                "error": str(e),
                "message": f"Error al ejecutar scraping: {str(e)}"
            }, status=500)
    return JsonResponse({
        "status": "error", 
        "error": "Método no permitido",
        "message": "Solo se permiten peticiones POST"
    }, status=405)

# ===== VISTAS DE SCRAPING ESPECÍFICAS =====
def ejecutar_scraping_lista_noticias(request):
    return ejecutar_scraping_generico(request, "scrape_elcomercio")

def ejecutar_scraping_politica(request):
    return ejecutar_scraping_generico(request, "scrape_elcomercio_pol")

def ejecutar_scraping_economia(request):
    return ejecutar_scraping_generico(request, "scrape_economia")

def ejecutar_scraping_mundo(request):
    return ejecutar_scraping_generico(request, "scrape_mundo")

def ejecutar_scraping_tecnologia(request):
    return ejecutar_scraping_generico(request, "scrape_tecnologia")

def ejecutar_scraping_peru21(request):
    return ejecutar_scraping_generico(request, "scrape_peru21")

def ejecutar_scraping_peru21_deportes(request):
    return ejecutar_scraping_generico(request, "scrape_peru21D")

def ejecutar_scraping_peru21_gastronomia(request):
    return ejecutar_scraping_generico(request, "scrape_peru21G")

def ejecutar_scraping_peru21_investigacion(request):
    return ejecutar_scraping_generico(request, "scrape_peru21I")

def ejecutar_scraping_peru21_lima(request):
    return ejecutar_scraping_generico(request, "scrape_peru21L")

# ===== VISTA API PARA ESTADÍSTICAS (OPCIONAL) =====
def estadisticas_noticias(request):
    """Vista opcional para obtener estadísticas de noticias vía API"""
    origen = request.GET.get('origen', 'all')
    
    if origen == 'all':
        queryset = Noticia.objects.all()
    else:
        queryset = Noticia.objects.filter(origen=origen)
    
    total = queryset.count()
    con_imagen = queryset.exclude(imagen__isnull=True).exclude(imagen='').count()
    
    # Estadísticas por período
    now = timezone.now()
    hoy = queryset.filter(fecha__date=now.date()).count()
    semana = queryset.filter(fecha__gte=now - timedelta(days=7)).count()
    mes = queryset.filter(fecha__gte=now - timedelta(days=30)).count()
    
    return JsonResponse({
        'total': total,
        'con_imagen': con_imagen,
        'sin_imagen': total - con_imagen,
        'hoy': hoy,
        'ultima_semana': semana,
        'ultimo_mes': mes,
        'origen': origen
    })
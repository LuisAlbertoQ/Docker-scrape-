from django.contrib import admin
from django.utils.html import format_html
from .models import Noticia

@admin.register(Noticia)
class NoticiaAdmin(admin.ModelAdmin):
    list_display = ('titulo_corto', 'autor', 'fecha', 'tiene_imagen', 'tiene_enlace', 'fecha_scraping')
    list_filter = ('autor', 'fecha', 'fecha_scraping')
    search_fields = ('titulo', 'autor')
    readonly_fields = ('fecha_scraping', 'preview_imagen')
    date_hierarchy = 'fecha'
    list_per_page = 20
    
    def titulo_corto(self, obj):
        return obj.titulo[:50] + '...' if len(obj.titulo) > 50 else obj.titulo
    titulo_corto.short_description = 'Título'
    
    def tiene_imagen(self, obj):
        if obj.imagen:
            return format_html('<span style="color: green;">✓ Sí</span>')
        return format_html('<span style="color: red;">✗ No</span>')
    tiene_imagen.short_description = 'Imagen'
    tiene_imagen.admin_order_field = 'imagen'
    
    def tiene_enlace(self, obj):
        if obj.enlace:
            return format_html('<a href="{}" target="_blank">🔗 Ver</a>', obj.enlace)
        return format_html('<span style="color: red;">✗ No</span>')
    tiene_enlace.short_description = 'Enlace'
    
    def preview_imagen(self, obj):
        if obj.imagen:
            return format_html(
                '<img src="{}" width="200" style="border-radius: 8px;" />',
                obj.imagen
            )
        return "Sin imagen"
    preview_imagen.short_description = 'Vista previa'
    
    fieldsets = (
        ('Información Principal', {
            'fields': ('titulo', 'autor', 'fecha')
        }),
        ('Multimedia', {
            'fields': ('imagen', 'preview_imagen', 'enlace')
        }),
        ('Metadatos', {
            'fields': ('fecha_scraping',),
            'classes': ('collapse',)
        }),
    )
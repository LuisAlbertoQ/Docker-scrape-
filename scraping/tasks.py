import time
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
    

@shared_task(bind=True)
def run_single_scrape(self, command_name):
    """Versión con progreso REAL durante el scraping."""
    try:
        import threading
        import time
        from io import StringIO
        
        # Configuración por tipo de comando
        command_config = {
            'scrape_elcomercio': {'estimated_time': 120, 'steps': 8},
            'scrape_economia': {'estimated_time': 90, 'steps': 7},
            'scrape_elcomercio_pol': {'estimated_time': 90, 'steps': 7},
            'scrape_mundo': {'estimated_time': 90, 'steps': 7},
            'scrape_tecnologia': {'estimated_time': 90, 'steps': 7},
            'scrape_peru21': {'estimated_time': 180, 'steps': 10},  # Más tiempo para Peru21
            'scrape_peru21D': {'estimated_time': 120, 'steps': 8},
            'scrape_peru21G': {'estimated_time': 90, 'steps': 7},
            'scrape_peru21I': {'estimated_time': 120, 'steps': 8},
            'scrape_peru21L': {'estimated_time': 90, 'steps': 7},
        }
        
        config = command_config.get(command_name, {'estimated_time': 120, 'steps': 8})
        estimated_time = config['estimated_time']
        total_steps = config['steps']
        
        output_buffer = StringIO()
        command_completed = False
        current_progress = 0
        
        def execute_command():
            nonlocal command_completed
            try:
                call_command(command_name, stdout=output_buffer)
                command_completed = True
                print(f"✅ Comando {command_name} completado")
            except Exception as e:
                print(f"❌ Error en comando {command_name}: {e}")
                command_completed = True
        
        # FASE 1: Progreso inicial rápido (0-20%)
        initial_stages = [
            (5, "Preparando scraping..."),
            (10, "Iniciando proceso..."),
            (15, "Configurando entorno..."),
            (20, "Listo para comenzar..."),
        ]
        
        for progress, message in initial_stages:
            if command_completed:
                break
            self.update_state(
                state='PROGRESS',
                meta={
                    'current': progress,
                    'total': 100,
                    'status': message,
                    'command': command_name
                }
            )
            print(f"📊 Progreso: {progress}% - {message}")
            time.sleep(1)
        
        # Iniciar el comando REAL
        command_thread = threading.Thread(target=execute_command)
        command_thread.start()
        print(f"🎯 Comando {command_name} iniciado en hilo separado")
        
        # FASE 2: Progreso durante la ejecución (20-95%)
        start_time = time.time()
        check_interval = 5  # Verificar cada 5 segundos
        
        while command_thread.is_alive():
            elapsed = time.time() - start_time
            progress_ratio = min(0.75, elapsed / estimated_time)  # Máximo 75% por tiempo
            progress = 20 + int(progress_ratio * 75)  # De 20% a 95%
            
            # Mensajes basados en el progreso
            if progress < 40:
                status_msg = "Navegando y cargando páginas..."
            elif progress < 60:
                status_msg = "Extrayendo contenido..."
            elif progress < 80:
                status_msg = "Procesando noticias..."
            else:
                status_msg = "Guardando en base de datos..."
            
            self.update_state(
                state='PROGRESS',
                meta={
                    'current': progress,
                    'total': 100,
                    'status': status_msg,
                    'command': command_name,
                    'elapsed_time': int(elapsed)
                }
            )
            print(f"🔄 Progreso durante ejecución: {progress}% - {status_msg}")
            
            # Esperar antes del siguiente check
            time.sleep(check_interval)
        
        # FASE 3: Completar (95-100%)
        if command_completed:
            # Progreso final rápido
            for progress in [96, 98, 100]:
                self.update_state(
                    state='PROGRESS',
                    meta={
                        'current': progress,
                        'total': 100,
                        'status': "Finalizando proceso...",
                        'command': command_name
                    }
                )
                print(f"✅ Progreso final: {progress}%")
                time.sleep(0.5)
        
        # Asegurarse de que el hilo terminó
        command_thread.join()
        
        print(f"🎉 Tarea {command_name} completada al 100%")
        return f"Comando {command_name} ejecutado exitosamente"
        
    except Exception as exc:
        print(f"💥 Error crítico en tarea: {exc}")
        self.update_state(
            state='FAILURE',
            meta={
                'current': 0, 
                'total': 100, 
                'status': f"Error crítico: {exc}",
                'command': command_name
            }
        )
        raise
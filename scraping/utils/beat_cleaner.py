import os, json, hashlib
from django.conf import settings

SCHEDULE_PATH = "celerybeat-schedule"
CHECK_FILE = "celerybeat-schedule-hash"


def current_schedule_hash() -> str:
    """Devuelve un hash de la configuración actual de CELERY_BEAT_SCHEDULE."""
    schedule_str = json.dumps(settings.CELERY_BEAT_SCHEDULE, sort_keys=True)
    return hashlib.md5(schedule_str.encode()).hexdigest()


def clean_if_schedule_changed():
    """Borra archivos viejos si la config cambió."""
    old_hash = None
    if os.path.exists(CHECK_FILE):
        with open(CHECK_FILE) as f:
            old_hash = f.read().strip()

    new_hash = current_schedule_hash()

    if old_hash != new_hash:
        # Borra todos los archivos de schedule
        for fname in [SCHEDULE_PATH, SCHEDULE_PATH + "-shm", SCHEDULE_PATH + "-wal", CHECK_FILE]:
            if os.path.exists(fname):
                os.remove(fname)
        # Guarda el nuevo hash
        with open(CHECK_FILE, "w") as f:
            f.write(new_hash)
        print("[Beat-Cleaner] Detectó cambio de intervalo → schedule limpiado.")
    else:
        print("[Beat-Cleaner] Sin cambios → arranca con schedule anterior.")
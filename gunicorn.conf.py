import multiprocessing
import os

# Adresse et port d'écoute (Render fournit le port via la variable PORT)
bind = f"0.0.0.0:{os.environ.get('PORT', '8000')}"

# Nombre de workers (formule standard : 2 x CPU + 1)
workers = int(os.environ.get("WEB_CONCURRENCY", multiprocessing.cpu_count() * 2 + 1))

# Type de worker
worker_class = "sync"

# Timeout des requêtes (en secondes)
timeout = 60

# Logs vers stdout/stderr (visibles dans les logs Render)
accesslog = "-"
errorlog = "-"
loglevel = "info"

# Redémarre les workers après un certain nombre de requêtes (évite les fuites mémoire)
max_requests = 1000
max_requests_jitter = 50

"""this is gunicorn config file"""
import multiprocessing
import os

# server socket
bind = "0.0.0.0:8000"

# workers
workers = multiprocessing.cpu_count()*2+1
worker_class = "sync"
worker_connections = 1000
timeout = 30
threads = 2

# logging
accesslog = "-"
errorlog = "-"
loglevel = "info"

# processing name
proc_name = "fleet_logger_api"

# server mechanics
deamon = False
pidfile = None
mask = 0
user = None
group = None
tmp_upload_dir = None

# ssl well add later
# keyfile = None
# certfile = None

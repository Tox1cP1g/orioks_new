import multiprocessing

bind = "0.0.0.0:8006"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
timeout = 120
keepalive = 5
max_requests = 500
max_requests_jitter = 50
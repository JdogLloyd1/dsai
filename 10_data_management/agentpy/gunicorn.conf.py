# gunicorn.conf.py
# Tell Posit Connect's gunicorn to use ASGI workers for FastAPI
# (Without this, gunicorn defaults to sync/WSGI workers which crash FastAPI.)

worker_class = "uvicorn.workers.UvicornWorker"

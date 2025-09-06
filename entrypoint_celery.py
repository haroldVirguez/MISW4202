#!/usr/bin/env python3

import os
import sys

# Agregar el directorio raíz al PYTHONPATH
sys.path.insert(0, '/app')

if __name__ == '__main__':
    from celery_config import celery
    
    print("Starting Celery worker...")
    celery.start()

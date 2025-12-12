# ------------------------------------------------------------------
# service_engine/router.py
"""
Thread qui écoute la pipe de registre et gère l'enregistrement des services.
"""

import os
import time
import json
import threading
import logging

REGISTRY_PIPE = '/tmp/service_registry'

logger = logging.getLogger('serviceEngine.router')

services = {}  # service_name -> {'pipe_name':..., 'login_required':..., 'last_seen':...}
services_lock = threading.Lock()


def ensure_registry_pipe():
    if not os.path.exists(REGISTRY_PIPE):
        try:
            os.mkfifo(REGISTRY_PIPE)
            logger.info('Pipe de registre créé: %s', REGISTRY_PIPE)
        except Exception as e:
            logger.error('Impossible de créer la pipe de registre: %s', e)


def registry_listener():
    ensure_registry_pipe()
    logger.info('Démarrage du listener de registre sur %s', REGISTRY_PIPE)
    while True:
        try:
            with open(REGISTRY_PIPE, 'r') as fifo:
                for line in fifo:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        msg = json.loads(line)
                    except Exception as e:
                        logger.error('Message registre invalide: %s', e)
                        continue
                    action = msg.get('action')
                    if action == 'register':
                        service_name = msg.get('service_name')
                        pipe_name = msg.get('pipe_name')
                        login_required = bool(msg.get('login_required'))
                        if not service_name or not pipe_name:
                            logger.warning('Enregistrement incomplet: %s', msg)
                            continue
                        with services_lock:
                            services[service_name] = {'pipe_name': pipe_name, 'login_required': login_required, 'last_seen': time.time()}
                        logger.info('Service enregistré: %s -> %s', service_name, pipe_name)
                    elif action == 'unregister':
                        service_name = msg.get('service_name')
                        if not service_name:
                            continue
                        with services_lock:
                            if service_name in services:
                                del services[service_name]
                                logger.info('Service désinscrit: %s', service_name)
                    else:
                        logger.warning('Action registre inconnue: %s', action)
        except Exception as e:
            logger.error('Erreur du listener registre: %s', e)
            time.sleep(1)


def start_registry_thread():
    t = threading.Thread(target=registry_listener, daemon=True)
    t.start()

# service_engine/pipes.py
"""
Helpers pour la communication avec les services via FIFO (named pipes).
"""

import os
import json
import uuid
import errno
import logging
from select import select

logger = logging.getLogger('serviceEngine.pipes')

RESPONSE_DIR = '/tmp/service_ui_responses'
READ_TIMEOUT = 5.0


def ensure_dir(path):
    try:
        os.makedirs(path, exist_ok=True)
    except Exception as e:
        logger.error('Impossible de créer le répertoire %s: %s', path, e)


def make_fifo(path):
    try:
        if not os.path.exists(path):
            os.mkfifo(path)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise


def write_json_to_fifo(fifo_path, obj):
    payload = json.dumps(obj)
    logger.info('Envoi commande au service via %s', fifo_path)
    try:
        fd = os.open(fifo_path, os.O_WRONLY | os.O_NONBLOCK)
        with os.fdopen(fd, 'w') as f:
            f.write(payload + '\n')
        return True
    except OSError as e:
        logger.error('Erreur en ecrivant dans la pipe %s : %s', fifo_path, e)
        return False


def read_json_from_fifo(fifo_path, timeout=READ_TIMEOUT):
    try:
        fd = os.open(fifo_path, os.O_RDONLY | os.O_NONBLOCK)
    except OSError as e:
        logger.error("Impossible d'ouvrir la pipe de réponse %s: %s", fifo_path, e)
        return None

    try:
        with os.fdopen(fd, 'r') as f:
            ready, _, _ = select([f], [], [], timeout)
            if not ready:
                logger.warning('Timeout en attente de la réponse sur %s', fifo_path)
                return None
            data = ''
            while True:
                chunk = f.readline()
                if not chunk:
                    break
                data += chunk
            if not data:
                return None
            return json.loads(data)
    except Exception as e:
        logger.error('Impossible de parser la réponse JSON: %s', e)
        return None
    finally:
        try:
            os.remove(fifo_path)
        except Exception:
            pass



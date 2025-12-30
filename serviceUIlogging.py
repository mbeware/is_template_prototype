import logging

if ('__serviceUIlogging__' not in dir()):
    __serviceUIlogging__ = True
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    webUIlogger = logging.getLogger('serviceWebUI')
    

    

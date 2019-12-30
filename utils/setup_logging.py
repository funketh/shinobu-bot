import logging
import logging.handlers


def setup_logging():
    file_handler = logging.handlers.RotatingFileHandler('logs/debug.log', maxBytes=500000, backupCount=7)
    file_handler.setLevel(logging.DEBUG)
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.INFO)
    logging.basicConfig(
        format='%(asctime)s %(levelname)-8s'
               '[%(filename)s:%(funcName)s:%(lineno)d] %(message)s',
        datefmt='%Y-%m-%d:%H:%M:%S',
        level=logging.DEBUG,
        handlers=(file_handler, stream_handler)
    )

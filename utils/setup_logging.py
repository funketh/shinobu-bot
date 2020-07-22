import logging
import logging.handlers


def setup_logging():
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.INFO)

    info_file_handler = logging.handlers.RotatingFileHandler('logs/info.log', maxBytes=500000, backupCount=20)
    info_file_handler.setLevel(logging.INFO)

    debug_file_handler = logging.handlers.RotatingFileHandler('logs/debug.log', maxBytes=500000, backupCount=20)
    debug_file_handler.setLevel(logging.DEBUG)

    logging.basicConfig(
        format='%(asctime)s %(levelname)-8s'
               '[%(filename)s:%(funcName)s:%(lineno)d] %(message)s',
        datefmt='%Y-%m-%d:%H:%M:%S',
        level=logging.DEBUG,
        handlers=(debug_file_handler, info_file_handler, stream_handler)
    )

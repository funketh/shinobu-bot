from data.CONSTANTS import MAX_MESSAGE_LENGTH


def paginate(text: str, prefix: str = '', suffix: str = ''):
    max_content_len = MAX_MESSAGE_LENGTH - len(prefix) - len(suffix)
    text_length = len(text)
    i = 0
    while i < text_length:
        max_j = i + max_content_len
        if max_j > text_length:
            j = text_length
        else:
            j = i + text[i:max_j].rfind('\n') + 1
        yield prefix + text[i:j] + suffix
        i = j

MAX_MESSAGE_LENGTH = 2000


def paginate(text: str, prefix: str = '', suffix: str = ''):
    max_content_len = MAX_MESSAGE_LENGTH - len(prefix) - len(suffix)
    i = 0
    while i < len(text):
        max_j = i + max_content_len
        j = len(text) if max_j > len(text) else i + text[i:max_j].rfind('\n') + 1
        yield prefix + text[i:j] + suffix
        i = j

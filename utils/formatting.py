MAX_MESSAGE_LENGTH = 2000


def paginate(text: str, prefix: str = '', suffix: str = ''):
    max_content_len = MAX_MESSAGE_LENGTH - (len(prefix) + len(suffix))
    i = 0
    while i < len(text):
        old_i = i
        max_next_i = old_i + max_content_len
        if max_next_i > len(text):
            i = len(text)
        else:
            after_newline = text[i:max_next_i].rfind('\n')
            i = max_next_i if after_newline < old_i else after_newline
        yield prefix + text[old_i:i] + suffix

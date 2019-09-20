def paginate(text: str, prefix: str = '', suffix: str = ''):
    i = 0
    while i < len(text):
        old_i = i
        max_next_i = max(old_i + 1024, len(text))
        after_newline = text[i:max_next_i].rfind('\n')
        i = max_next_i if after_newline < old_i else after_newline
        yield prefix + text[old_i:i] + suffix

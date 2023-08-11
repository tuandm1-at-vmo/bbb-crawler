

def escape_special_characters(content):
    if content is None: return ''
    return str(content) \
        .replace('<', '&#60;') \
        .replace('>', '&#62;') \
        .replace('&', '&#38;')

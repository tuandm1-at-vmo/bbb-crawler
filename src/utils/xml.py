

def escape_special_characters(content):
    return str(content) \
        .replace('<', '&#60;') \
        .replace('>', '&#62;') \
        .replace('&', '&#38;')

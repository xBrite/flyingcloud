import six

def hexdump(src, length=8):
    """Generate ASCII hexdump of bytes or unicode data."""
    result = []
    is_unicode = isinstance(src, six.text_type)
    digits = 4 if is_unicode else 2

    if six.PY3:
        def code(x):
            return ord(x) if is_unicode else x

        def char(x):
            return x if is_unicode else chr(x)
    else:
        code = ord

        def char(x):
            return x

    for i in range(0, len(src), length):
        s = src[i:i+length]
        hexa = ' '.join(["%0*X" % (digits, code(x)) for x in s])
        text = ''.join([char(x) if 0x20 <= code(x) < 0x7F else '.' for x in s])
        result.append( "%04X   %-*s   %s" % (i, length*(digits + 1), hexa, text) )
    return '\n'.join(result)

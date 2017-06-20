
import six
from builtins import range

def hexdump(src, length=8):
    """Generate ASCII hexdump of bytes or unicode data."""
    result = []
    digits = 4 if isinstance(six.text_type) else 2
    for i in range(0, len(src), length):
        s = src[i:i+length]
        hexa = b' '.join(["%0*X" % (digits, ord(x))  for x in s])
        text = b''.join([x if 0x20 <= ord(x) < 0x7F else b'.'  for x in s])
        result.append( b"%04X   %-*s   %s" % (i, length*(digits + 1), hexa, text) )
    return b'\n'.join(result)

# -*- coding: utf-8 -*-
import os
import six

import pytest

from flyingcloud.utils.misc import hexdump


class TestHexDump:
    Payload = b"""\
(hub-fc) $ (feature/python3_fixes) python
Python 2.7.13 (default, Dec 18 2016, 07:03:39)
[GCC 4.2.1 Compatible Apple LLVM 8.0.0 (clang-800.0.42.1)] on darwin
Type "help", "copyright", "credits" or "license" for more information."""

    BytesExpected = u"""\
0000   28 68 75 62 2D 66 63 29    (hub-fc)
0008   20 24 20 28 66 65 61 74     $ (feat
0010   75 72 65 2F 70 79 74 68    ure/pyth
0018   6F 6E 33 5F 66 69 78 65    on3_fixe
0020   73 29 20 70 79 74 68 6F    s) pytho
0028   6E 0A 50 79 74 68 6F 6E    n.Python
0030   20 32 2E 37 2E 31 33 20     2.7.13 
0038   28 64 65 66 61 75 6C 74    (default
0040   2C 20 44 65 63 20 31 38    , Dec 18
0048   20 32 30 31 36 2C 20 30     2016, 0
0050   37 3A 30 33 3A 33 39 29    7:03:39)
0058   0A 5B 47 43 43 20 34 2E    .[GCC 4.
0060   32 2E 31 20 43 6F 6D 70    2.1 Comp
0068   61 74 69 62 6C 65 20 41    atible A
0070   70 70 6C 65 20 4C 4C 56    pple LLV
0078   4D 20 38 2E 30 2E 30 20    M 8.0.0 
0080   28 63 6C 61 6E 67 2D 38    (clang-8
0088   30 30 2E 30 2E 34 32 2E    00.0.42.
0090   31 29 5D 20 6F 6E 20 64    1)] on d
0098   61 72 77 69 6E 0A 54 79    arwin.Ty
00A0   70 65 20 22 68 65 6C 70    pe "help
00A8   22 2C 20 22 63 6F 70 79    ", "copy
00B0   72 69 67 68 74 22 2C 20    right", 
00B8   22 63 72 65 64 69 74 73    "credits
00C0   22 20 6F 72 20 22 6C 69    " or "li
00C8   63 65 6E 73 65 22 20 66    cense" f
00D0   6F 72 20 6D 6F 72 65 20    or more 
00D8   69 6E 66 6F 72 6D 61 74    informat
00E0   69 6F 6E 2E                ion."""

    UnicodeExpected = u"""\
0000   0028 0068 0075 0062 002D 0066 0063 0029    (hub-fc)
0008   0020 0024 0020 0028 0066 0065 0061 0074     $ (feat
0010   0075 0072 0065 002F 0070 0079 0074 0068    ure/pyth
0018   006F 006E 0033 005F 0066 0069 0078 0065    on3_fixe
0020   0073 0029 0020 0070 0079 0074 0068 006F    s) pytho
0028   006E 000A 0050 0079 0074 0068 006F 006E    n.Python
0030   0020 0032 002E 0037 002E 0031 0033 0020     2.7.13 
0038   0028 0064 0065 0066 0061 0075 006C 0074    (default
0040   002C 0020 0044 0065 0063 0020 0031 0038    , Dec 18
0048   0020 0032 0030 0031 0036 002C 0020 0030     2016, 0
0050   0037 003A 0030 0033 003A 0033 0039 0029    7:03:39)
0058   000A 005B 0047 0043 0043 0020 0034 002E    .[GCC 4.
0060   0032 002E 0031 0020 0043 006F 006D 0070    2.1 Comp
0068   0061 0074 0069 0062 006C 0065 0020 0041    atible A
0070   0070 0070 006C 0065 0020 004C 004C 0056    pple LLV
0078   004D 0020 0038 002E 0030 002E 0030 0020    M 8.0.0 
0080   0028 0063 006C 0061 006E 0067 002D 0038    (clang-8
0088   0030 0030 002E 0030 002E 0034 0032 002E    00.0.42.
0090   0031 0029 005D 0020 006F 006E 0020 0064    1)] on d
0098   0061 0072 0077 0069 006E 000A 0054 0079    arwin.Ty
00A0   0070 0065 0020 0022 0068 0065 006C 0070    pe "help
00A8   0022 002C 0020 0022 0063 006F 0070 0079    ", "copy
00B0   0072 0069 0067 0068 0074 0022 002C 0020    right", 
00B8   0022 0063 0072 0065 0064 0069 0074 0073    "credits
00C0   0022 0020 006F 0072 0020 0022 006C 0069    " or "li
00C8   0063 0065 006E 0073 0065 0022 0020 0066    cense" f
00D0   006F 0072 0020 006D 006F 0072 0065 0020    or more 
00D8   0069 006E 0066 006F 0072 006D 0061 0074    informat
00E0   0069 006F 006E 002E                        ion."""

    def test_bytes(self):
        h = hexdump(self.Payload)
        assert self.BytesExpected == h
        assert isinstance(h, str)

    def test_unicode(self):
        p = self.Payload.decode()
        assert isinstance(p, six.text_type)
        h = hexdump(p)
        assert self.UnicodeExpected == h
        assert isinstance(h, six.text_type)

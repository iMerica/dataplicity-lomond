from __future__ import print_function

import struct

from .errors import FrameBuildError
from .mask import make_masking_key, mask

class Opcode(object):
    continuation = 0
    text = 1
    binary = 2
    reserved1 = 3
    reserved2 = 4
    reserved3 = 5
    reserved4 = 6
    reserved5 = 7
    close = 8
    ping = 9
    pong = 0xA
    reserved6 = 0xB
    reserved7 = 0xC
    reserved8 = 0xD
    reserved9 = 0xE
    reserved10 = 0xF


class Frame(object):

    def __init__(self, opcode, payload=b'', masking_key=None, fin=0, rsv1=0, rsv2=0, rsv3=0):
        self.fin = fin
        self.rsv1 = rsv1
        self.rsv2 = rsv2
        self.rsv2 = rsv3
        self.opcode = opcode
        self.mask = 0
        self.payload_length = len(payload)
        self.masking_key = masking_key
        self.payload_data = payload

    # Use struct module to pack ws frame header
    _pack8 = struct.Struct('!BB4B').pack
    _pack16 = struct.Struct('!BBH4B').pack
    _pack64 = struct.Struct('!BBQ4B').pack

    @classmethod
    def build_header(cls, opcode, payload=b'', fin=0):
        """Build a WS frame header."""
        # https://tools.ietf.org/html/rfc6455#section-5.2
        masking_key = make_masking_key()
        mask_bit = mask << 7
        byte0 = (fin << 7) | opcode
        length = len(payload)
        if length < 126:
            header_bytes = cls._pack8(byte0, mask_bit | length, masking_key)
        elif length < (1 << 16):
            header_bytes = cls._pack16(byte0, mask_bit | 126, length, masking_key)
        elif length < (1 << 63):
            header_bytes = cls._pack64(byte0, mask_bit | 127, length, masking_key)
        else:
            # Can't send a payload > 2**63 bytes
            raise FrameBuildError(
                'payload is too large for a single frame'
            )
        return header_bytes

    @property
    def is_control(self):
        return self.opcode >= 8

    @property
    def is_binary(self):
        return self.opcode == Opcode.binary

    @property
    def is_text(self):
        return self.opcode == Opcode.text

    @property
    def is_continuation(self):
        return self.opcode == Opcode.continuation

    @property
    def is_ping(self):
        return self.opcode == Opcode.ping

    @property
    def is_pong(self):
        return self.opcode == Opcode.pong

    @property
    def is_close(self):
        return self.opcode == Opcode.close
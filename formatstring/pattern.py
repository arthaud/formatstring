#!/usr/bin/env python3
import struct


def make_pattern(buffer_size, start_offset=1):
    pattern = 'ABCDEFGH'
    offset = start_offset

    while True:
        fmt = '|%%%d$x' % offset
        if len(pattern) + len(fmt) > buffer_size:
            break

        pattern += fmt
        offset += 1

    return pattern


def compute_offset(buffer, start_offset=1, endianness='@'):
    memory = buffer.split('|')
    if memory[0] == 'ABCDEFGH':
        memory = memory[1:]

    memory = map(lambda x: struct.pack(endianness + 'I', int(x, 16)), memory)
    memory = b''.join(memory)

    for i in range(len(buffer)):
        if memory[i:i + 10] == b'ABCDEFGH|%':
            if i % 4 == 0:
                return (start_offset + i // 4, 0)
            else:
                return (start_offset + i // 4 + 1, 4 - i % 4)

    return False # not found

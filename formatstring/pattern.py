#!/usr/bin/env python3
import struct
from formatstring.architectures import local_arch


def make_pattern(buffer_size, start_offset=1):
    '''
    Generate a pattern to get the offset of your buffer

    Args:
        buffer_size (int): The maximum size of your buffer
        start_offset (int): The starting offset

    Returns:
        A pattern for the format string
    '''
    pattern = 'ABCDEFGH'
    offset = start_offset

    while True:
        fmt = '|%%%d$p' % offset
        if len(pattern) + len(fmt) > buffer_size:
            break

        pattern += fmt
        offset += 1

    return pattern


def compute_offset(buffer, start_offset=1, arch=None):
    '''
    Compute the offset of your buffer given the result of make_pattern

    Args:
        buffer (string): The result of make_pattern
        start_offset (int): The starting offset
        arch (Architecture): The architecture of your system

    Returns:
        False if the offset is not found
        Otherwise, returns the couple (offset, padding)
    '''
    arch = arch or local_arch()

    buffer = buffer.replace('(nil)', '0x0')
    memory = buffer.split('|')
    if memory[0] == 'ABCDEFGH':
        memory = memory[1:]

    memory = map(lambda x: struct.pack(arch.address_fmt, int(x, 16)),
                 memory)
    memory = b''.join(memory)

    for i in range(len(buffer)):
        if memory[i:i + 10] == b'ABCDEFGH|%':
            if i % arch.bytes == 0:
                return (start_offset + i // arch.bytes, 0)
            else:
                return (start_offset + i // arch.bytes + 1,
                        arch.bytes - i % arch.bytes)

    return False # not found

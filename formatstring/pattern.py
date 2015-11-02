#!/usr/bin/env python3
import struct


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
        fmt = '|%%%d$x' % offset
        if len(pattern) + len(fmt) > buffer_size:
            break

        pattern += fmt
        offset += 1

    return pattern


def compute_offset(buffer, start_offset=1, endianness='@'):
    '''
    Compute the offset of your buffer given the result of make_pattern

    Args:
        buffer (string): The result of make_pattern
        start_offset (int): The starting offset
        endianness ('@', '<' or '>'): The endianness of your system (see struct.pack)

    Returns:
        False if the offset is not found
        Otherwise, returns the couple (offset, padding)
    '''
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

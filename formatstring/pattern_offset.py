#!/usr/bin/env python3
from formatstring import pattern
import argparse

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Compute the offset of your buffer, given the result of pattern_create')
    parser.add_argument('buffer', metavar='BUFFER',
                        help='The result of pattern_create')
    parser.add_argument('-s', '--start-offset', metavar='OFFSET', type=int, default=1,
                        help='The starting offset')
    parser.add_argument('--little-endian', action='store_true')
    parser.add_argument('--big-endian', action='store_true')
    args = parser.parse_args()

    endianness = '@'
    if args.little_endian:
        endianness = '<'
    elif args.big_endian:
        endianness = '>'

    ret = pattern.compute_offset(args.buffer, args.start_offset, endianness)
    if ret:
        offset, padding = ret

        if padding == 0:
            print('Found buffer at offset %d' % offset)
        else:
            print('Found buffer, use offset %d with a padding of %d bytes' % (offset, padding))
    else:
        print('Buffer not found, look forward.')

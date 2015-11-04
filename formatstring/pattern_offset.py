#!/usr/bin/env python3
import argparse
import sys
from formatstring import architectures
from formatstring import pattern

def main(args=None):
    desc = 'Compute the offset of your buffer, given the result of pattern_create'
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument('buffer', metavar='BUFFER', nargs='?',
                        help='The result of pattern_create')
    parser.add_argument('-s', '--start-offset', metavar='OFFSET',
                        type=int, default=1,
                        help='The starting offset')
    parser.add_argument('-a', '--arch', metavar='ARCH',
                        help='The architecture '
                             '(x86_32, x86_64, arm, sparc, ...)')
    args = parser.parse_args(args)

    if not args.buffer:
        print('Enter the result of the format string on a pattern '
              'given by pattern_create:')
        args.buffer = sys.stdin.readline()

    if args.arch:
        if args.arch not in architectures.archs:
            print('error: unknown architecture: %s' % args.arch)
            exit(1)

        arch = architectures.archs[args.arch]
    else:
        arch = architectures.local_arch()

    ret = pattern.compute_offset(args.buffer, args.start_offset, arch)
    if ret:
        offset, padding = ret

        if padding == 0:
            print('Found buffer at offset %d' % offset)
        else:
            print('Found buffer at offset %d '
                  'with a padding of %d bytes' % (offset, padding))
    else:
        print('Buffer not found, look forward (or check the architecture).')


if __name__ == '__main__':
    main()

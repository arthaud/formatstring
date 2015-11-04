#!/usr/bin/env python3
from formatstring import pattern
import argparse


def main(args=None):
    desc = 'Generate a pattern to get the offset of your buffer'
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument('buffer_size', metavar='BUF_SIZE', type=int,
                        help='The size of your buffer')
    parser.add_argument('-s', '--start-offset', metavar='OFFSET',
                        type=int, default=1,
                        help='The starting offset')
    args = parser.parse_args(args)
    print(pattern.make_pattern(args.buffer_size, args.start_offset))

if __name__ == '__main__':
    main()

#!/usr/bin/env python3


def struct_fmt(size, signed=False):
    '''
    Helper that returns the format for struct.pack, given a size and
    a signedness

    >>> struct_fmt(4, False)
    'I'
    >>> struct_fmt(8, True)
    'q'
    '''
    formats = {1: 'b', 2: 'h', 4: 'i', 8: 'q'}
    assert size in formats, 'unknown size'

    if not signed:
        return formats[size].upper()
    else:
        return formats[size]


class Architecture:
    def __init__(self, name, bits, endian):
        assert bits >= 1
        assert endian in ('little', 'big')

        self.name = name
        self.bits = bits
        self.endian = endian

    @property
    def bytes(self):
        return self.bits // 8

    # format for struct

    @property
    def endian_fmt(self):
        return '<' if self.endian == 'little' else '>'

    @property
    def address_fmt(self):
        return self.endian_fmt + struct_fmt(self.bytes, False)

    def __repr__(self):
        return '<%s (%d bits, %s endian)>' % (self.name,
                                              self.bits,
                                              self.endian)


archs = {}
aarch64 = archs['aarch64'] = Architecture('aarch64', 64, 'little')
alpha = archs['alpha'] = Architecture('alpha', 64, 'little')
avr = archs['avr'] = Architecture('avr', 8, 'little')
amd64 = archs['amd64'] = Architecture('amd64', 64, 'little')
arm = archs['arm'] = Architecture('arm', 32, 'little')
cris = archs['cris'] = Architecture('cris', 32, 'little')
i386 = archs['i386'] = Architecture('i386', 32, 'little')
ia64 = archs['ia64'] = Architecture('ia64', 64, 'big')
m68k = archs['m68k'] = Architecture('m68k', 32, 'big')
mips = archs['mips'] = Architecture('mips', 32, 'little')
mips64 = archs['mips64'] = Architecture('mips64', 64, 'little')
msp430 = archs['msp430'] = Architecture('msp430', 16, 'little')
powerpc = archs['powerpc'] = Architecture('powerpc', 32, 'big')
powerpc64 = archs['powerpc64'] = Architecture('powerpc64', 64, 'big')
s390 = archs['s390'] = Architecture('s390', 32, 'big')
sparc = archs['sparc'] = Architecture('sparc', 32, 'big')
sparc64 = archs['sparc64'] = Architecture('sparc64', 64, 'big')
thumb = archs['thumb'] = Architecture('thumb', 32, 'little')
vax = archs['vax'] = Architecture('vax', 32, 'little')

# for convenience
x86_32 = archs['x86_32'] = Architecture('x86_32', 32, 'little')
x86_64 = archs['x86_64'] = Architecture('x86_64', 64, 'little')


def local_arch():
    import platform

    assert platform.machine() in archs, 'unknown architecture'
    return archs[platform.machine()]


def binary_arch(path):
    from elftools.elf.elffile import ELFFile

    with open(path, 'rb') as f:
        elf = ELFFile(f)

        name = {
            'EM_X86_64': 'amd64',
            'EM_386': 'i386',
            'EM_486': 'i386',
            'EM_ARM': 'arm',
            'EM_AARCH64': 'aarch64',
            'EM_MIPS': 'mips',
            'EM_PPC': 'powerpc',
            'EM_PPC64': 'powerpc64',
            'EM_SPARC32PLUS': 'sparc',
            'EM_SPARCV9': 'sparc64',
            'EM_IA_64': 'ia64'
        }.get(elf['e_machine'], elf['e_machine'])
        bits = elf.elfclass
        endian = {
            'ELFDATANONE': 'little',
            'ELFDATA2LSB': 'little',
            'ELFDATA2MSB': 'big'
        }[elf['e_ident']['EI_DATA']]

        return Architecture(name, bits, endian)

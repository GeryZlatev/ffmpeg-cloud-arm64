#!/usr/bin/env python3
"""Regression tests for rejecting unexpected static inputs and nonempty libdl."""
from pathlib import Path
import tempfile
import unittest

from static_link import inspect


class StaticLinkContract(unittest.TestCase):
    def test_approved_empty_archive(self):
        with tempfile.TemporaryDirectory() as directory:
            dl = Path(directory) / 'libdl.a'
            dl.write_bytes(b'!<arch>\n')
            content = 'LOAD /work/prefix/lib/libdav1d.a\nLOAD ' + str(dl) + '\nLOAD libavcodec/libavcodec.a\n'
            self.assertIn(str(dl), inspect(content, dl))
            for unexpected in ('libx265.a', 'libaom.a', 'libz.a', 'libunexpected.a'):
                with self.subTest(archive=unexpected), self.assertRaises(RuntimeError):
                    inspect(content + 'LOAD /usr/lib/' + unexpected, dl)
            with self.assertRaises(RuntimeError):
                inspect(content + str(dl) + '(injected.o)', dl)
            with self.assertRaises(RuntimeError):
                inspect(content + 'LOAD /different/provider/libdl.a', dl)
            dl.write_bytes(b'!<arch>\nnot-empty')
            with self.assertRaises(RuntimeError):
                inspect(content, dl)

    def test_missing_dav1d(self):
        with self.assertRaises(RuntimeError):
            inspect('LOAD libavcodec/libavcodec.a')


if __name__ == '__main__':
    unittest.main()

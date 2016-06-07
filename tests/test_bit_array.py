__author__ = "Stefan Hölzl"

import pytest

from canpy.bit_array import BitArray

class TestBitArray(object):
    def test_init(self):
        ba = BitArray(5)
        assert ba._list == [False, False, False, False, False]

    def test_setitem(self):
        ba = BitArray(5)
        ba[0] = 1
        ba[1] = True
        assert ba._list == [True, True, False, False, False]

    def test_getitem(self):
        ba = BitArray(5)
        ba[0] = 1
        ba[1] = 1
        assert ba[0] == True
        assert ba[1] == True
        assert ba[2] == False
        assert ba[3] == False
        assert ba[4] == False

    def test_len(self):
        ba = BitArray(5)
        assert len(ba) == 5

    def test_str(self):
        ba = BitArray(5)
        ba[0] = 1
        ba[1] = 1
        assert str(ba) == '11000'

    def test_set(self):
        ba = BitArray(5)
        ba.set(5)
        assert ba._list == [True, False, True, False, False]

    def test_set_signed(self):
        ba = BitArray(5, signed=True, little_endian=True)
        ba.set(-5)
        assert ba._list == [True, False, True, False, True]

    def test_set_big_endian(self):
        ba = BitArray(5, signed=False, little_endian=False)
        ba.set(5)
        assert ba._list == [False, False, True, False, True]

    def test_set_signed_big_endian(self):
        ba = BitArray(5, signed=True, little_endian=False)
        ba.set(-5)
        assert ba._list == [True, False, True, False, True]

    def test_int_little_endian(self):
        ba = BitArray(5, value=19, little_endian=True, signed=False)
        assert int(ba) == 19

    def test_int_big_endian(self):
        ba = BitArray(5, value=19, little_endian=False, signed=False)
        assert int(ba) == 19

    def test_int_little_endian_signed(self):
        ba = BitArray(5, value=-9, little_endian=True, signed=True)
        assert int(ba) == -9

    def test_int_big_endian_signed(self):
        ba = BitArray(5, value=-9, little_endian=False, signed=True)
        assert int(ba) == -9

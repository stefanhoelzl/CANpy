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

    @pytest.mark.parametrize('size, signed, little_endian, set, expected_list', [
        (5, False, True, 5, [True, False, True, False, False]),
        (5, True, True, 5, [True, False, True, False, False]),
        (5, False, False, 5, [False, False, True, False, True]),
        (5, True, False, -5, [True, False, True, False, True]),
        (2, False, True, 5, [False, True])
    ])
    def test_set(self, size, signed, little_endian, set, expected_list):
        ba = BitArray(size=size, signed=signed, little_endian=little_endian)
        ba.set(set)
        assert ba._list == expected_list

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

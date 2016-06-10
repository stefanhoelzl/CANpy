__author__ = "Stefan Hölzl"
__all__ = ['BitArray']


class BitArray(object):
    """Representation of a number as list of bits"""
    def __init__(self, size, value=0, little_endian=True, signed=False):
        """Initializes the BitArray

        Args:
            size:          Size of the bit array
            value:         Value which should be represented
            little_endian: If True the number is represented in little endian bit order else big endian
            signed:        If True the bit array can represent signed numbers
        """
        self.signed = signed
        self.little_endian = little_endian
        self._list = [False for _ in range(size)]
        self.set(value)

    def set(self, value):
        """Sets an integer value to the bit array

        Args:
            value: integer value to save
        """
        self._list = [False for _ in range(len(self))]
        value_str = bin(abs(value)).replace('0b', '')

        offset = max(0, len(self) - (len(value_str) if not self.signed else len(value_str)+1))
        for bit, val in enumerate(value_str):
            bit = bit if not self.signed else bit+1
            bit += offset
            if bit >= len(self):
                break
            self._list[bit] = True if val == '1' else False

        if value < 0 and self.signed:
            self._list[0] = True
        if self.little_endian:
            self._list.reverse()

    # Protocol definitions
    def __setitem__(self, key, value):
        self._list[key] = bool(value)

    def __getitem__(self, key):
        return self._list[key]

    def __len__(self):
        return len(self._list)

    def __str__(self):
        return ''.join(map(str, map(int, self._list)))

    def __int__(self):
        bits = self._list
        negative = False
        value = 0
        if not self.little_endian:
            bits = bits[::-1]
        if self.signed:
            negative = True if bits[-1] else False
            bits = bits[:-1]
        for bit, val in enumerate(bits):
            value += 2**bit if val else 0
        if negative:
            value *= -1
        return value
__author__ = "Stefan Hölzl"
__all__ = ['CANSignal']

from canpy.bit_array import BitArray
from canpy.can_objects.can_object import CANObject

class CANSignal(CANObject):
    """Represents a CAN-Signal"""
    def __init__(self, name, start_bit, length, little_endian=True, signed=False, factor=1.0, offset=0.0, value_min=0,
                 value_max=0, unit="", is_multiplexer=False, multiplexer_id=None):
        """Initializes the object

        Args:
            name:           Name of the signal
            start_bit:      Start bit of the signal
            length:         Length of the signal in bits
            little_endian:  True if data is in little-endian format (default: True)
            signed:         True if the value is signed (default: False)
            factor:         Factor to calculate the signal value (default: 1)
            offset:         Offset to calculate the signal value (default: 0)
            value_min:      Minimum value of the signal (default: 0)
            value_max:      Maximum value of the signal (default: 0)
            unit:           Unit of the signal value (default: "")
            is_multiplexer: True if message is a multiplexer (default: False)
            multiplexer_id: Multiplexer ID if this message is multiplexed (default: None)
        """
        super().__init__()
        self._receiver = []
        self._raw_value = 0

        self.name = name
        self.start_bit = start_bit
        self.length = length
        self.little_endian = little_endian
        self.signed = signed
        self.factor = factor
        self.offset = offset
        self.value_min = value_min
        self.value_max = value_max
        self.unit = unit
        self.is_multiplexer = is_multiplexer
        self.multiplexer_id = multiplexer_id

        self.message = None
        self.value_dict = None

    # Property definitions
    @property
    def last_bit(self):
        return self.start_bit + self.length - 1

    @property
    def receiver(self):
        return self._receiver

    @property
    def raw_value(self):
        return self._raw_value

    @raw_value.setter
    def raw_value(self, value):
        """Sets the raw value and checks for length, sign and type

        Args:
            value: New raw value
        Raises:
            AttributeError: If value cant be converted to an int
            AttributeError: If value is signed, but signal is unsigned
            AttributeError: If value exceeds signal length
        """
        try:
            value = int(value)
        except:
            raise AttributeError('Cant convert to int')
        if not self.signed and value < 0:
            raise AttributeError('Signed value not allowed')

        usable_length = self.length if not self.signed else self.length-1
        if 2**usable_length <= abs(value):
            raise AttributeError('Value exceeds signal length')
        self._raw_value = value

    @property
    def value(self):
        """Converts the raw value to the actual value

        Returns:
            converted raw value
        """
        if self.value_dict and self.raw_value in self.value_dict.keys():
            return self.value_dict[self.raw_value]
        return self.raw_value*self.factor + self.offset

    @value.setter
    def value(self, value):
        """Sets the raw_value by converting the given value and limits the value to min/max of the signal

        Args:
            value: value to convert and save as raw_value
        """
        if self.value_min != 0 and self.value_max != 0:
            value = max(value, self.value_min)
            value = min(value, self.value_max)
        self.raw_value = int((value-self.offset)/self.factor)

    @property
    def bits(self):
        """Converts the raw_value to a bit array

        Returns:
            Bit array representing the raw value
        """
        return BitArray(self.length, value=self.raw_value, little_endian=self.little_endian, signed=self.signed)

    @bits.setter
    def bits(self, value):
        """Sets the raw_value with value coresponding the given value
        Args:
            value: bit array
        """
        self.raw_value = int(value)

    # Method definitions
    def add_receiver(self, node):
        """Adds a new receiver to the signal

        Args:
            node: Node which receives this message
        """
        self._receiver.append(node)

    # Protocol definitions
    def __int__(self):
        return self.raw_value

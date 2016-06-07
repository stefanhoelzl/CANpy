__author__ = "Stefan Hölzl"

from canpy.bit_array import BitArray

class CANBus(object):
    """Representation of a CAN-Bus"""
    def __init__(self):
        """Initializes the object"""
        self._nodes = {}

        self.version = ""
        self.description = ""
        self.speed = 100

    # Property definitions
    @property
    def nodes(self):
        return self._nodes

    # Method definitions
    def add_node(self, node):
        """Adds a new Node to the CANDB

        Args:
            node: Node to add.
        """
        self._nodes[node.name] = node

    def get_message(self, can_id):
        """Returns message by can_id

        Args:
            can_id: Message CAN-ID
        Returns:
            message with the given can-id or None
        """
        messages = [msg for node in self.nodes.values() for msg in node.messages.values() if msg.can_id == can_id]
        if len(messages) == 0:
            return None
        return messages[0]

    def get_signal(self, can_id, name):
        """Returns signal by name and can_id

        Args:
            can_id: CAN-ID of the message which contains the signal
            name:   Signal name
        Returns:
            signal with the given name and CAN-ID or None
        """
        message = self.get_message(can_id)
        if not message:
            return None
        signals = [sig for sig in message.signals.values() if sig.name == name]
        if len(signals) == 0:
            return None
        return signals[0]

    # Protocol definitions
    def __str__(self, *args, **kwargs):
        return 'CANDB(Version: {}, Nodes: {}, Description: {})'.format(self.version, len(self.nodes), self.description)


class CANNode(object):
    """Representation of a CAN-Node"""
    def __init__(self, name):
        """Initializes the object

        Args:
            name: Name of the Node
        """
        self._messages = {}

        self.name = name
        self.description = ""

    # Property definitions
    @property
    def messages(self):
        return self._messages

    # Method definitions
    def add_message(self, message):
        """Add a new message to the Node.

        Args:
            message: Message to add
        Raises:
            RuntimeError: If message already belongs to a node
        """
        if message.sender:
            raise RuntimeError('Message already belongs to node {}!'.format(message.sender))

        message.sender = self
        self._messages[message.can_id] = message

    # Protocol definitions
    def __str__(self, *args, **kwargs):
        return 'CANNode(Name: {}, Messages: {}, Description: {})'.format(self.name, len(self.messages), self.description)

class CANMessage(object):
    """Represents a CAN-Message"""
    def __init__(self, can_id, name, length):
        """Initializes the object

        Args:
            can_id: CAN-ID of the message.
            name:   Name of the message.
            length: Message length in bytes
        """
        self._signals = {}

        self.can_id = can_id
        self.name = name
        self.length = length

        self.description = ""
        self.sender = None

    # Property definitions
    @property
    def signals(self):
        return self._signals

    # Method definitions
    def add_signal(self, signal):
        """Adds a signal to the message

        Args:
            signal: Signal to add
        Raises:
            RuntimeError: If signal already belongs to a message
        """
        if signal.message:
            raise RuntimeError('Signal already belongs to message {}'.format(signal.message))
        self._signals[signal.name] = signal

    # Protocol definitions
    def __str__(self, *args, **kwargs):
        return 'CANMessage(CAN-ID: {}, Name: {}, Length: {})'.format(self.can_id, self.name, self.length)

    def __int__(self):
        value = 0
        for signal in self.signals.values():
            value += int(signal.bits) << signal.start_bit
        return value

class CANSignal(object):
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
        self.description = ""

    # Property definitions
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
        self.raw_value = int( (value-self.offset)/self.factor )

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
    def __str__(self, *args, **kwargs):
        return 'CANSignal(Name: {}, Start: {}, Length: {})'.format(self.name, self.start_bit, self.length)

    def __int__(self):
        return self.raw_value
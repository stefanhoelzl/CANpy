__author__ = "Stefan Hölzl"


class CANBus(object):
    """Representation of a CAN-Bus"""
    def __init__(self):
        """Initializes the object"""
        self._nodes = {}

        self.version = ""
        self.description = ""

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
            message with the given can-id
        """
        return [msg for node in self.nodes.values() for msg in node.messages if msg.can_id == can_id][0]

    def get_signal(self, can_id, name):
        """Returns signal by name and can_id

        Args:
            can_id: CAN-ID of the message which contains the signal
            name:   Signal name
        Returns:
            signal with the given name and CAN-ID
        """
        return [sig for sig in self.get_message(can_id).signals if sig.name == name][0]

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
        self._messages = []

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
        self._messages.append(message)

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
        self._signals = []

        self.can_id = can_id
        self.name = name
        self.length = length

        self.description = ""
        self.sender = None

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
        self._signals.append(signal)

    # Protocol definitions
    def __str__(self, *args, **kwargs):
        return 'CANMessage(CAN-ID: {}, Name: {}, Length: {})'.format(self.can_id, self.name, self.length)

class CANSignal(object):
    """Represents a CAN-Signal"""
    def __init__(self, name, start_bit, length, little_endian=True, signed=False, factor=1.0, offset=0.0, value_min=0,
                 value_max=0, unit="", is_multiplexer=False, multiplexer_id=None):
        self._receiver = []

        self.name = name
        self.start_bit = start_bit
        self.length = length
        self.little_endian  = little_endian
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
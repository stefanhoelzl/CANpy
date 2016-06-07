__author__ = "Stefan Hölzl"

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

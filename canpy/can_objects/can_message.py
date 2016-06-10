__author__ = "Stefan Hölzl"
__all__ = ['CANMessage']

from canpy.can_objects.can_object import CANObject


class CANMessage(CANObject):
    """Represents a CAN-Message"""
    def __init__(self, can_id, name, length):
        """Initializes the object

        Args:
            can_id: CAN-ID of the message.
            name:   Name of the message.
            length: Message length in bytes
        """
        super().__init__()
        self._signals = {}

        self.can_id = can_id
        self.name = name
        self.length = length
        self.is_active = True

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
            RuntimeError: If signal does not fit into the message layout
        """
        if signal.message:
            raise RuntimeError('Signal already belongs to message {}'.format(signal.message))
        if not self._check_if_signal_fits(signal):
            raise RuntimeError('Signal doesnt fit in message layout')
        if not self._check_if_multiplexer_settings_are_valid(signal):
            raise RuntimeError('Signal mulltiplexer settings doesnt fit to message')
        self.add_child(signal)
        self._signals[signal.name] = signal

    def get_multiplexer_signal(self):
        for signal in self.signals.values():
            if signal.is_multiplexer:
                return signal
        return None

    def _check_if_signal_fits(self, new_signal):
        """Checks if a signal fits into the message layout
        Args:
            new_signal: Signal to check
        Returns:
            True if the signal fits, False if it overlaps with another signal or exceeds the message length
        """
        if new_signal.last_bit >= self.length * 8:
            return False
        for signal in [signal for signal in self.signals.values()
                       if signal.multiplexer_id == new_signal.multiplexer_id or
                                       signal.multiplexer_id is None or
                                       new_signal.multiplexer_id is None]:
            # check if start overlaps
            if signal.start_bit <= new_signal.start_bit <= signal.last_bit:
                return False
            # check if end overlaps
            if new_signal.start_bit <= signal.start_bit <= new_signal.last_bit:
                return False
        return True

    def _check_if_multiplexer_settings_are_valid(self, new_signal):
        multiplexer_signal = self.get_multiplexer_signal()
        if new_signal.multiplexer_id and not multiplexer_signal:
            return False
        if new_signal.is_multiplexer and multiplexer_signal:
            return False
        return True

    # Protocol definitions
    def __str__(self):
        return 'CANMessage(CAN-ID: {}, Name: {}, Length: {})'.format(self.can_id, self.name, self.length)

    def __int__(self):
        value = 0
        for signal in self.signals.values():
            value += int(signal.bits) << signal.start_bit
        return value

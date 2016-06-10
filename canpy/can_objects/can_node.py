__author__ = "Stefan Hölzl"
__all__ = ['CANNode']

from canpy.can_objects.can_network import CANObject

class CANNode(CANObject):
    """Representation of a CAN-Node"""
    def __init__(self, name):
        """Initializes the object

        Args:
            name: Name of the Node
        """
        super().__init__()
        self._messages = {}

        self.name = name

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

        self.add_child(message)
        message.sender = self
        self._messages[message.can_id] = message

    # Protocol definitions
    def __str__(self):
        return 'CANNode(Name: {}, Messages: {}, Description: {})'.format(self.name, len(self.messages),
                                                                         self.description)

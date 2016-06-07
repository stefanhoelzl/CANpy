__author__ = "Stefan Hölzl"

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

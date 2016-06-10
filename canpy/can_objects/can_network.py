__author__ = "Stefan Hölzl"
__all__ = ['CANNetwork']

from canpy.can_objects import CANObject
from canpy.can_objects.can_signal import CANSignal
from canpy.can_objects.can_message import CANMessage
from canpy.can_objects.can_attribute import CANEnumAttributeDefinition, CANIntAttributeDefinition


class CANNetwork(CANObject):
    """Representation of a CAN-Network"""
    default_attribute_definitions = [
        CANEnumAttributeDefinition('GenMsgSendType', CANMessage, ['cyclic', 'triggered', 'cyclicIfActive',
                                                                  'cyclicAndTriggered', 'cyclicIfActiveAndTriggered',
                                                                  'none'], default=5),
        CANIntAttributeDefinition('GenMsgCycleTime', CANMessage, 0, 0, default=0),
        CANIntAttributeDefinition('GenMsgStartDelayTime', CANMessage, 0, 0, default=0),
        CANIntAttributeDefinition('GenMsgDelayTime', CANMessage, 0, 0, default=0),
        CANIntAttributeDefinition('GenSigStartValue', CANSignal, 0, 0, default=0),
    ]

    def __init__(self):
        """Initializes the object"""
        super().__init__()
        self._nodes = {}
        self._value_dicts = {}

        self.version = ""
        self.speed = 100

        for attr_def in CANNetwork.default_attribute_definitions:
            self.attributes.add_definition(attr_def)

    # Property definitions
    @property
    def nodes(self):
        return self._nodes

    @property
    def value_dicts(self):
        return self._value_dicts

    # Method definitions
    def add_value_dict(self, name, value_dict):
        """Adds a new value dictionary to the can network

        Args:
            name:       Name of the value dict
            value_dict: dictionary to add
        """
        self._value_dicts[name] = value_dict

    def add_node(self, node):
        """Adds a new Node to the CANDB

        Args:
            node: Node to add.
        """
        self.add_child(node)
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

    def get_consumed_messages(self, node):
        """Returns a list with all messages which contains a signals which is consumed by the given node

        Args:
            node: Node for which you want the messages
        Returns:
            List of consumed messages
        """
        return [msg for n in self.nodes.values()
                        for msg in n.messages.values()
                            for sig in msg.signals.values()
                                if node in sig.receiver]

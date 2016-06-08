__author__ = "Stefan Hölzl"

from canpy.can_objects.can_attribute import CANAttributesContainer

class CANNone(object):
    # Protoclol definitions
    def __eq__(self, other):
        if other == None:
            return True
        return super().__eq__(other)

class CANObject(CANNone):
    """Provides basic functionality for CAN-Objects"""
    @property
    def parent(self):
        if '_parent' not in self.__dict__:
            self._parent = CANNone()
        return self._parent

    @parent.setter
    def parent(self, value):
        if '_parent' not in self.__dict__:
            self._parent = None
        self._parent = value

    @property
    def attributes(self):
        if '_attributes' not in self.__dict__:
            self._attributes = CANAttributesContainer(self)
        return self._attributes

    def add_child(self, child):
        child.parent = self

    # Protocol definitions
    def __eq__(self, other):
        if other == None:
            return False
        return super().__eq__(other)
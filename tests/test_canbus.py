__author__ = "Stefan Hölzl"

import pytest

from canpy.can_bus import CANBus, CANMessage, CANNode, CANSignal, CANObject
from canpy.can_bus.can_attribute import *

class TestCANObject(object):
    def test_add_attribute(self):
        co = CANObject()
        co.add_attribute(CANAttribute(CANAttributeDefinition('Attribute', CANObject)))
        assert 'Attribute' in co.attributes

class TestCANBus(object):
    def test_add_node(self):
        cdb = CANBus()
        cdb.add_node(CANNode('TestNode'))
        assert 'TestNode' in cdb.nodes

    def test_get_node(self):
        cdb = CANBus()
        node = CANNode('TestNode')
        cdb.add_node(node)
        assert cdb.nodes['TestNode'] == node

    def test_get_message(self):
        cdb = CANBus()
        node = CANNode('TestNode')
        msg = CANMessage(1234, 'Message', 8)
        node.add_message(msg)
        cdb.add_node(node)
        assert cdb.get_message(can_id=1234) == msg

    def test_get_none_message(self):
        cdb = CANBus()
        assert cdb.get_message(can_id=1234) == None

    def test_get_signal(self):
        cdb = CANBus()
        node = CANNode('TestNode')
        msg = CANMessage(1234, 'Message', 8)
        node.add_message(msg)
        sig = CANSignal('Signal', 0, 8)
        msg.add_signal(sig)
        cdb.add_node(node)
        assert cdb.get_signal(can_id=1234, name='Signal') == sig

    def test_get_none_signal(self):
        cdb = CANBus()
        assert cdb.get_signal(can_id=1234, name='Signal') == None


class TestCANNode(object):
    def test_add_message(self):
        node = CANNode('TestNode')
        node.add_message(CANMessage(1, 'Name', 6))
        assert 1 in node.messages

    def test_set_message_sender(self):
        node = CANNode('TestNode')
        node.add_message(CANMessage(1, 'Name', 8))
        assert node.messages[1].sender == node

    def test_add_message_with_sender(self):
        msg = CANMessage(1, 'Name', 8)
        msg.sender = CANNode('TestNode')
        node = CANNode('TestNode')
        with pytest.raises(RuntimeError):
            node.add_message(msg)

class TestCANMessage(object):
    def test_add_signal(self):
        msg = CANMessage(1, 'Name', 8)
        msg.add_signal(CANSignal('Signal', 0, 8))
        assert 'Signal' in msg.signals

    def test_add_signal_with_message(self):
        sig = CANSignal('Signal', 0, 8)
        sig.message = CANMessage(1, 'Name', 8)
        msg = CANMessage(2, 'Name', 8)
        with pytest.raises(RuntimeError):
            msg.add_signal(sig)

    def test_int(self):
        msg = CANMessage(1, 'Name', 1)
        sig = CANSignal('Signal', 0, 8)
        sig.raw_value = 100
        msg.add_signal(sig)
        assert int(msg) == 100

    def test_int_splitted(self):
        msg = CANMessage(1, 'Name', 1)
        sig = CANSignal('Signal', 4, 8)
        sig.raw_value = 100
        msg.add_signal(sig)
        assert int(msg) == int(sig.bits) << 4

    def test_int_two_signals(self):
        msg = CANMessage(1, 'Name', 2)
        sig0 = CANSignal('Signal0', 0, 8)
        sig0.raw_value = 159
        msg.add_signal(sig0)
        sig1 = CANSignal('Signal1', 8, 8)
        sig1.raw_value = 96
        msg.add_signal(sig1)
        assert int(msg) == int(sig0.bits) + (int(sig1.bits) << 8)

class TestCANSignal(object):
    def test_add_receiver(self):
        node = CANNode('TestNode')
        sig = CANSignal('Signal', 0, 8)
        sig.add_receiver(node)
        assert len(sig.receiver) == 1

    def test_raw_value_getter(self):
        sig = CANSignal('Signal1', 0, 8)
        sig._raw_value = 10
        assert sig.raw_value == 10

    def test_raw_value_setter_signing_exception(self):
        sig = CANSignal('Signal', 0, 8)
        sig.signed = False
        sig.raw_value = 0
        sig.raw_value = 10
        with pytest.raises(AttributeError):
            sig.raw_value = -1
        sig.signed = True
        sig.raw_value = -1

    def test_raw_value_setter_exceed_length(self):
        sig = CANSignal('Signal', 0, 3)
        sig.raw_value = 7
        assert sig.raw_value == 7
        with pytest.raises(AttributeError):
            sig.raw_value = 8
        sig.signed = True
        sig.raw_value = 3
        assert sig.raw_value == 3
        sig.raw_value = -3
        assert sig.raw_value == -3
        with pytest.raises(AttributeError):
            sig.raw_value = 4
        assert sig.raw_value == -3
        with pytest.raises(AttributeError):
            sig.raw_value = -4
        assert sig.raw_value == -3

    def test_raw_value_setter_only_int(self):
        sig = CANSignal('Signal', 0, 3)
        with pytest.raises(AttributeError):
            sig.raw_value = None
        with pytest.raises(AttributeError):
            sig.raw_value = 'a'

    def test_value_getter(self):
        sig = CANSignal('Signal', 0, 8)
        sig.factor = 2.5
        sig.offset = 1.25
        sig.raw_value = 2
        assert sig.value == sig.raw_value*2.5 + 1.25

    def test_value_setter_raw_value(self):
        sig = CANSignal('Signal', 0, 8)
        sig.value = 10
        assert sig.raw_value == 10

    def test_value_setter_raw_value_conversion(self):
        sig = CANSignal('Signal', 0, 8)
        sig.factor = 2.5
        sig.offset = 1.25
        sig.value = 11.25
        assert sig.raw_value == 4

    def test_value_setter_min_max(self):
        sig = CANSignal('Signal', 0, 8)
        sig.value_min = 4
        sig.value_max = 8
        sig.value = 3.9
        assert sig.value == 4
        sig.value = 8.1
        assert sig.value == 8

class TestCANAttributeDefinitions(object):
    def test_string_check(self):
        cad = CANStringAttributeDefinition('StringAttribute', CANObject)
        assert cad.name == 'StringAttribute'
        assert cad.check_value('String Value') == True

    def test_float_check(self):
        cad = CANFloatAttributeDefinition('FloatAttribute', CANObject, -1.5, 1.5)
        assert cad.name == "FloatAttribute"
        assert cad.check_value(1.5) == True
        assert cad.check_value(-1.5) == True
        assert cad.check_value(-1) == True
        assert cad.check_value(1) == True
        assert cad.check_value(1.6) == False
        assert cad.check_value(-1.6) == False
        assert cad.check_value('abc') == False

    def test_int_check(self):
        cad = CANIntAttributeDefinition('IntAttribute', CANObject, -2, 2)
        assert cad.name == "IntAttribute"
        assert cad.check_value(2) == True
        assert cad.check_value(-2) == True
        assert cad.check_value(-1) == True
        assert cad.check_value(1) == True
        assert cad.check_value(2.1) == False
        assert cad.check_value(-2.1) == False
        assert cad.check_value('abc') == False

    def test_enum_check(self):
        cad = CANEnumAttributeDefinition('EnumAttribute', CANObject, ['Val0', 'Val1', 'Val2', 'Val3'])
        assert cad.name == 'EnumAttribute'
        assert cad.check_value(0) == True
        assert cad.check_value(1) == True
        assert cad.check_value(2) == True
        assert cad.check_value(3) == True
        assert cad.check_value(-1) == False
        assert cad.check_value(4) == False

class TestCANAttribute(object):
    class CANTestAttributeDefinition(CANAttributeDefinition):
        def __init__(self, name, can_obj_type, check=True, default=None):
            super().__init__(name, can_obj_type)
            self.check = check
            self.default = default

        def check_value(self, value):
            return self.check

    def test_get_name(self):
        cad = TestCANAttribute.CANTestAttributeDefinition('TestAttribute', CANAttribute)
        ca = CANAttribute(cad)
        assert ca.name == 'TestAttribute'

    def test_get_default_value(self):
        cad = TestCANAttribute.CANTestAttributeDefinition('TestAttribute', CANAttribute, default=100)
        ca = CANAttribute(cad)
        assert ca.value == 100

    def test_set_get_value(self):
        cad = TestCANAttribute.CANTestAttributeDefinition('TestAttribute', CANAttribute, default=100)
        ca = CANAttribute(cad)
        ca.value = 10
        assert ca.value == 10

    def test_set_value_fail(self):
        cad = TestCANAttribute.CANTestAttributeDefinition('TestAttribute', CANAttribute, default=100, check=False)
        ca = CANAttribute(cad)
        with pytest.raises(AttributeError):
            ca.value = 10
        assert ca.value == 100

class TestCANAttributeDefinitionsContainer(object):
    def test_add_attribute_definition(self):
        cadc = CANAttributeDefinitionsContainer()
        cad = CANAttributeDefinition('Test', CANSignal)
        cadc.add_attribute_definition(cad)
        assert CANSignal in cadc
        assert 'Test' in cadc[CANSignal]
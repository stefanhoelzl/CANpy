__author__ = "Stefan Hölzl"

import pytest

from canpy.can_objects import CANNetwork, CANMessage, CANNode, CANSignal
from canpy.can_objects.can_object import CANNone, CANObject
from canpy.can_objects.can_attribute import *
from canpy.can_objects.can_attribute import CANAttributeDefinition
from canpy.bit_array import BitArray

class TestCANObject(object):
    def test_add_attribute(self):
        co = CANObject()
        co.attributes.add(CANAttribute(CANAttributeDefinition('Attribute', CANObject)))
        assert 'Attribute' in co.attributes

    def test_set_parent(self):
        child_co = CANObject()
        parent_co = CANObject()
        child_co.parent = parent_co
        assert parent_co.parent == None
        assert child_co.parent == parent_co

    def test_inherit_default_attr_values(self):
        cn = CANNetwork()
        cad = CANIntAttributeDefinition('CANIntAttributeDefinition', CANObject, 0, 0)
        cad.default = 100
        cn.attributes.add_definition(cad)

        co = CANObject()
        cn.add_child(co)

        assert co.attributes['CANIntAttributeDefinition'].value == 100

    def test_cannone_is_none(self):
        assert CANNone() == None
        assert CANNone() != True


class TestCANNetwork(object):
    def test_add_node(self):
        cn = CANNetwork()
        node = CANNode('TestNode')
        cn.add_node(node)
        assert 'TestNode' in cn.nodes
        assert node.parent == cn

    def test_get_node(self):
        cn = CANNetwork()
        node = CANNode('TestNode')
        cn.add_node(node)
        assert cn.nodes['TestNode'] == node

    def test_get_message(self):
        cn = CANNetwork()
        node = CANNode('TestNode')
        msg = CANMessage(1234, 'Message', 8)
        node.add_message(msg)
        cn.add_node(node)
        assert cn.get_message(can_id=1234) == msg

    def test_get_none_message(self):
        cn = CANNetwork()
        assert cn.get_message(can_id=1234) == None

    def test_get_signal(self):
        cn = CANNetwork()
        node = CANNode('TestNode')
        msg = CANMessage(1234, 'Message', 8)
        node.add_message(msg)
        sig = CANSignal('Signal', 0, 8)
        msg.add_signal(sig)
        cn.add_node(node)
        assert cn.get_signal(can_id=1234, name='Signal') == sig

    def test_get_none_signal_with_message(self):
        cn = CANNetwork()
        node = CANNode('TestNode')
        msg = CANMessage(1234, 'Message', 8)
        node.add_message(msg)
        sig = CANSignal('Signal', 0, 8)
        cn.add_node(node)
        assert cn.get_signal(can_id=1234, name='Signal') == None

    def test_get_none_signal(self):
        cn = CANNetwork()
        assert cn.get_signal(can_id=1234, name='Signal') == None

    def test_add_attribute_definition(self):
        cn = CANNetwork()
        cad = CANAttributeDefinition('Test', CANSignal)
        cn.attributes.add_definition(cad)
        assert 'Test' in cn.attributes.definitions

    def test_add_value_dict(self):
        cn = CANNetwork()
        value_dict = {0: 'Val0'}
        cn.add_value_dict('ValueDict', value_dict)
        assert len(cn.value_dicts) == 1
        assert 'ValueDict' in cn.value_dicts

    def test_get_consumed_messages(self):
        cn = CANNetwork()
        cn.add_node(CANNode('SendingNode'))
        cn.add_node(CANNode('ReceivingNode'))
        cn.nodes['SendingNode'].add_message(CANMessage(1, 'Message', 1))
        sig = CANSignal('Signal', 0, 8)
        sig.add_receiver(cn.nodes['ReceivingNode'])
        cn.nodes['SendingNode'].messages[1].add_signal(sig)
        assert cn.nodes['SendingNode'].messages[1] in cn.get_consumed_messages(cn.nodes['ReceivingNode'])


class TestCANNode(object):
    def test_add_message(self):
        node = CANNode('TestNode')
        msg = CANMessage(1, 'Name', 6)
        node.add_message(msg)
        assert 1 in node.messages
        assert msg.parent == node

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
        sig = CANSignal('Signal', 0, 8)
        msg.add_signal(sig)
        assert 'Signal' in msg.signals
        assert sig.parent == msg

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
        msg = CANMessage(1, 'Name', 2)
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

    @pytest.mark.parametrize('msg_size, new_sig_def, existing_sigs_def, expected_result', [
        (1, (0, 8, False, None), [], True),
        (1, (0, 4, False, None), [(4, 4, False, None)], True),
        (1, (4, 4, False, None), [(0, 4, False, None)], True),
        (2, (4, 4, False, 1), [(8, 8, True, None), (0, 5, False, 2)], True),
        (1, (4, 5, False, None), [], False),
        (1, (4, 4, False, None), [(0, 5, False, None)], False),
        (1, (0, 5, False, None), [(4, 4, False, None)], False),
        (1, (0, 8, False, None), [(2, 2, False, None)], False),
        (1, (2, 2, False, None), [(0, 8, False, None)], False),
        (1, (2, 2, False, None), [(2, 2, False, None)], False),
        (2, (2, 2, False, None), [(8, 8, True, None), (2, 2, False, 1)], False),
        (2, (2, 2, False, 1), [(8, 8, True, None), (2, 2, False, None)], False),
        (2, (2, 2, False, 1), [(8, 8, True, None), (2, 2, False, 1)], False),
    ])
    def test_signal_fit_check(self, msg_size, new_sig_def, existing_sigs_def, expected_result):
        msg = CANMessage(1, 'Message', msg_size)
        for i, sig_def in enumerate(existing_sigs_def):
            msg.add_signal(CANSignal('Signal{}'.format(i), sig_def[0], sig_def[1],
                                     is_multiplexer=sig_def[2], multiplexer_id=sig_def[3]))
        assert msg._check_if_signal_fits(CANSignal('NewSignal', new_sig_def[0], new_sig_def[1],
                                                   is_multiplexer=new_sig_def[2], multiplexer_id=new_sig_def[3])
                                         ) == expected_result

    def test_signal_fit_check_fail(self):
        msg = CANMessage(1, 'Message', 1)
        with pytest.raises(RuntimeError):
            msg.add_signal(CANSignal('Signal', 0, 10))

    @pytest.mark.parametrize('old_sig_is_m, old_sig_m_id, new_sig_is_m, new_sig_m_id, expected_result', [
        (False, None, False, 1, False),
        (True, None, True, None, False),
        (True, None, False, 1, True),
    ])
    def test_signal_multiplexer_settings_check(self, old_sig_is_m, old_sig_m_id, new_sig_is_m, new_sig_m_id, expected_result):
        msg = CANMessage(1, 'Message', 2)
        msg.add_signal(CANSignal('OldSignal', 0, 8, multiplexer_id=old_sig_m_id, is_multiplexer=old_sig_is_m))
        assert msg._check_if_multiplexer_settings_are_valid(CANSignal('OldSignal', 0, 8,multiplexer_id=new_sig_m_id,
                                                                      is_multiplexer=new_sig_is_m)) == expected_result

    def test_signal_multiplexer_settings_check_fail(self):
        msg = CANMessage(1, 'Message', 1)
        with pytest.raises(RuntimeError):
            msg.add_signal(CANSignal('Signal', 0, 8, multiplexer_id=1))


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

    def test_int_repr(self):
        sig = CANSignal('Signal1', 0, 8)
        sig._raw_value = 10
        assert int(sig) == 10

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

    def test_bits_setter(self):
        sig = CANSignal('Signal', 0, 8)
        ba = BitArray(size=8, value=200)
        sig.bits = ba
        assert sig.raw_value == 200

    def test_value_dict(self):
        sig = CANSignal('Signal', 0, 8)
        sig.value_dict = {0: 'Value0'}
        sig.raw_value = 0
        assert sig.value == sig.value_dict[sig.raw_value]
        sig.raw_value = 1
        assert sig.value == sig.raw_value


class TestCANAttributeDefinitions(object):
    class NoStr(object):
            def __str__(self):
                raise NotImplementedError()

    @pytest.mark.parametrize('attr_definition, expected_name, test_value, expected_result', [
        (CANAttributeDefinition('CANAttribute', CANObject), 'CANAttribute', None, True),
        (CANStringAttributeDefinition('StringAttribute', CANObject), 'StringAttribute', 'String', True),
        (CANStringAttributeDefinition('StringAttribute', CANObject), 'StringAttribute', NoStr(), False),
        (CANFloatAttributeDefinition('FloatAttribute', CANObject, -1.5, 1.5), 'FloatAttribute', 1.5, True),
        (CANFloatAttributeDefinition('FloatAttribute', CANObject, -1.5, 1.5), 'FloatAttribute', -1.5, True),
        (CANFloatAttributeDefinition('FloatAttribute', CANObject, -1.5, 1.5), 'FloatAttribute', 1, True),
        (CANFloatAttributeDefinition('FloatAttribute', CANObject, -1.5, 1.5), 'FloatAttribute', -1, True),
        (CANFloatAttributeDefinition('FloatAttribute', CANObject, -1.5, 1.5), 'FloatAttribute', 0, True),
        (CANFloatAttributeDefinition('FloatAttribute', CANObject, -1.5, 1.5), 'FloatAttribute', 1.6, False),
        (CANFloatAttributeDefinition('FloatAttribute', CANObject, -1.5, 1.5), 'FloatAttribute', -1.6, False),
        (CANFloatAttributeDefinition('FloatAttribute', CANObject, -1.5, 1.5), 'FloatAttribute', 'abc', False),
        (CANFloatAttributeDefinition('FloatAttribute', CANObject, 0, 0), 'FloatAttribute', 100, True),
        (CANFloatAttributeDefinition('FloatAttribute', CANObject, 0, 0), 'FloatAttribute', -100, True),
        (CANIntAttributeDefinition('IntAttribute', CANObject, -2, 2), 'IntAttribute', 2, True),
        (CANIntAttributeDefinition('IntAttribute', CANObject, -2, 2), 'IntAttribute', -2, True),
        (CANIntAttributeDefinition('IntAttribute', CANObject, -2, 2), 'IntAttribute', -1, True),
        (CANIntAttributeDefinition('IntAttribute', CANObject, -2, 2), 'IntAttribute', 1, True),
        (CANIntAttributeDefinition('IntAttribute', CANObject, -2, 2), 'IntAttribute', 0, True),
        (CANIntAttributeDefinition('IntAttribute', CANObject, -2, 2), 'IntAttribute', -2.1, False),
        (CANIntAttributeDefinition('IntAttribute', CANObject, -2, 2), 'IntAttribute', -2.2, False),
        (CANIntAttributeDefinition('IntAttribute', CANObject, -2, 2), 'IntAttribute', 'abc', False),
        (CANEnumAttributeDefinition('EnumAttribute', CANObject, ['Val0', 'Val1', 'Val2', 'Val3']),
            'EnumAttribute', 0, True),
        (CANEnumAttributeDefinition('EnumAttribute', CANObject, ['Val0', 'Val1', 'Val2', 'Val3']),
            'EnumAttribute', 1, True),
        (CANEnumAttributeDefinition('EnumAttribute', CANObject, ['Val0', 'Val1', 'Val2', 'Val3']),
            'EnumAttribute', 2, True),
        (CANEnumAttributeDefinition('EnumAttribute', CANObject, ['Val0', 'Val1', 'Val2', 'Val3']),
            'EnumAttribute', 3, True),
        (CANEnumAttributeDefinition('EnumAttribute', CANObject, ['Val0', 'Val1', 'Val2', 'Val3']),
            'EnumAttribute', 'Val0', True),
        (CANEnumAttributeDefinition('EnumAttribute', CANObject, ['Val0', 'Val1', 'Val2', 'Val3']),
            'EnumAttribute', -1, False),
        (CANEnumAttributeDefinition('EnumAttribute', CANObject, ['Val0', 'Val1', 'Val2', 'Val3']),
            'EnumAttribute', 4, False),
        (CANEnumAttributeDefinition('EnumAttribute', CANObject, ['Val0', 'Val1', 'Val2', 'Val3']),
            'EnumAttribute', 'Val4', False),
    ])
    def test_check(self, attr_definition, expected_name, test_value, expected_result):
        assert attr_definition.name == expected_name
        assert attr_definition.check_value(test_value) == expected_result


class TestCANAttribute(object):
    class CANTestAttributeDefinition(CANAttributeDefinition):
        def __init__(self, name, can_obj_type, check=True, default=None):
            self.check = check
            super().__init__(name, can_obj_type)
            self._default = default

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


class TestCANAttributesContainer(object):
    def test_add_attributes(self):
        co = CANObject()
        cad = CANAttributeDefinition('Name', CANObject)
        ca = CANAttribute(cad)

        assert 'Name' not in co.attributes
        with pytest.raises(KeyError):
            co.attributes['Name']

        co.attributes.add(ca)
        assert len(co.attributes) == 1
        assert 'Name' in co.attributes
        assert co.attributes['Name'] == ca

    def test_lookup_chain(self):
        grandparent_co = CANObject()
        parent_co = CANObject()
        co = CANObject()
        grandparent_co.add_child(parent_co)
        parent_co.add_child(co)
        with pytest.raises(KeyError):
            co.attributes['Attribute']

        grandparent_co.attributes.add_definition(CANStringAttributeDefinition('Attribute', CANObject,
                                                                         default='GrandParentDefault'))
        assert co.attributes['Attribute'].value == 'GrandParentDefault'

        parent_co.attributes.add_definition(CANStringAttributeDefinition('Attribute', CANObject,
                                                                         default='DefaultParent'))
        assert co.attributes['Attribute'].value == 'DefaultParent'

        co.attributes.add_definition(CANStringAttributeDefinition('Attribute', CANObject, default='ObjectDefault'))
        assert co.attributes['Attribute'].value == 'ObjectDefault'

        co.attributes.add(CANAttribute(CANStringAttributeDefinition('Attribute', CANObject,
                                                                    default='AttributeDefault')))
        assert co.attributes['Attribute'].value == 'AttributeDefault'

        co.attributes.add(CANAttribute(CANStringAttributeDefinition('Attribute', CANObject, default='AttributeDefault'),
                                       value='AttributeValue'))
        assert co.attributes['Attribute'].value == 'AttributeValue'

    def test_check_default_attribute(self):
        co = CANObject()
        cad = CANAttributeDefinition('Name', CANObject)
        co.attributes.add_definition(cad)
        assert 'Name' not in co.attributes
        cad.default = 100
        assert 'Name' in co.attributes
        assert co.attributes['Name'].value == 100

    @pytest.mark.parametrize('attr_name, expected_attr_name, obj_type, def_ob_type, default', [
        ('Name', 'ExcpectedName', CANObject, CANObject, 1),
        ('Name', 'Name', CANObject, CANNetwork, 1),
        ('Name', 'Name', CANObject, CANObject, None),
    ])
    def test_check_default_attribute_fail(self, attr_name, expected_attr_name, obj_type, def_ob_type, default):
        co = obj_type()
        cad = CANAttributeDefinition(attr_name, def_ob_type)
        cad.default = default
        co.attributes.add_definition(cad)
        with pytest.raises(KeyError):
            co.attributes[expected_attr_name]

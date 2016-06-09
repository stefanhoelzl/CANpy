__author__ = "Stefan Hölzl"

import pytest

from canpy.can_objects import CANNode, CANMessage, CANSignal, CANNetwork
from canpy.can_objects.can_attribute import *
from canpy.parser.dbc_parser import DBCParser

class TestDBCParsing(object):
    @pytest.mark.parametrize("line, expected_version", [
        ('VERSION "1.0"', '1.0'),
        ('VERSION    "1.0"', '1.0'),
    ])
    def test_parse_version(self, line, expected_version):
        parser = DBCParser()
        parser._parse_line(line)
        assert parser._can_network.version == expected_version

    @pytest.mark.parametrize("line, expected_nodes", [
        ('BU_   :   Node0   Node1    Node2', ['Node0', 'Node1', 'Node2']),
        ('BU_:Node0 Node1 Node2', ['Node0', 'Node1', 'Node2']),
    ])
    def test_parse_nodes(self, line, expected_nodes):
        parser = DBCParser()
        parser._parse_line(line)
        assert len(parser._can_network.nodes) == len(expected_nodes)
        node_names = parser._can_network._nodes.keys()
        for node in expected_nodes:
            assert node in node_names

    @pytest.mark.parametrize("line, expected_name, expected_id, expected_length, expected_sender", [
        ('BO_ 1234 CANMessage:8 Node0', 'CANMessage', 1234, 8, 'Node0'),
        ('BO_  1234  CANMessage  :  8  Node0', 'CANMessage', 1234, 8, 'Node0'),
    ])
    def test_parse_message(self, line, expected_name, expected_id, expected_length, expected_sender):
        parser = DBCParser()
        sender = CANNode(expected_sender)
        parser._can_network.add_node(sender)
        parser._parse_line(line)
        msg = parser._can_network.get_message(1234)
        assert msg.name == expected_name
        assert msg.can_id == expected_id
        assert msg.length == expected_length
        assert msg.sender == sender

    testset_signal_multiplexer = ['SG_ Signal1  M   :32|32@1+ (33.3,0)[0|100] "%" Node1 Node2']
    testset_signal_multiplexed = ['SG_ Signal1  m34  :32|32@1+ (33.3,0)[0|100] "%" Node1 Node2']

    @pytest.mark.parametrize('line, signal_name, start_bit, length, little_endian, signed, factor, offset, value_min,'\
                             'value_max, unit, is_multiplexer, multiplexer_id, nodes, add_multiplexer', [
        ('SG_     Signal1     :    32|32@1+   (   33.3     ,  0    )  [0|100]     "%"     Node1   Node2',
            'Signal1', 32, 32, True, False, 33.3, 0, 0, 100, '%', False, None, ['Node1', 'Node2'], False),
        ('SG_ Signal1:32|32@1+ (33.3,0) [ 0 | 100  ] "%" Node1 Node2',
            'Signal1', 32, 32, True, False, 33.3, 0, 0, 100, '%', False, None, ['Node1', 'Node2'], False),
        ('SG_ Signal0 : 0|32@1- (1,0) [0|0] "" Node0',
            'Signal0', 0, 32, True, True, 1, 0, 0, 0, '', False, None, ['Node0'], False),
        ('SG_ Signal1  m34  :32|32@1+ (33.3,0)[0|100] "%" Node1 Node2',
            'Signal1', 32, 32, True, False, 33.3, 0, 0, 100, '%', False, 34, ['Node1', 'Node2'], True),
        ('SG_ Signal1  M   :32|32@1+ (33.3,0)[0|100] "%" Node1 Node2',
            'Signal1', 32, 32, True, False, 33.3, 0, 0, 100, '%', True, None, ['Node1', 'Node2'], False),
    ])
    def test_parse_signal(self, line, signal_name, start_bit, length, little_endian, signed, factor, offset, value_min,\
                          value_max, unit, is_multiplexer, multiplexer_id, nodes, add_multiplexer):
        parser = DBCParser()
        parser._can_network.add_node(CANNode('Sender'))
        for node in nodes:
            parser._can_network.add_node(CANNode(node))
        msg = CANMessage(2, 'CANMessage', 8)
        if add_multiplexer:
            msg.add_signal(CANSignal('MultiplexerSignal', 8, 8, is_multiplexer=True))
        parser._can_network.nodes['Sender'].add_message(msg)
        parser._mode = ('MESSAGE', msg)
        parser._parse_line(line)
        sig = msg.signals[signal_name]
        assert sig.name == signal_name
        assert sig.start_bit == start_bit
        assert sig.length == length
        assert sig.little_endian == little_endian
        assert sig.signed == signed
        assert sig.factor == factor
        assert sig.value_min == value_min
        assert sig.value_max == value_max
        assert sig.unit == unit
        assert sig.is_multiplexer == is_multiplexer
        assert sig.multiplexer_id == multiplexer_id
        for node in nodes:
            assert parser._can_network.nodes[node] in sig.receiver

    def test_parse_signal_wrong_block(self):
        parser = DBCParser()
        node = CANNode('Node0')
        parser._mode = ('NORMAL', None)
        with pytest.raises(RuntimeError):
            parser._parse_line('SG_ DUMMY_LINE')

    @pytest.mark.parametrize('line, expected_desc', [
        ('CM_ "The Description";', 'The Description'), ('CM_    \t"The Description";', 'The Description'),
    ])
    def test_parse_candb_desc(self, line, expected_desc):
        parser = DBCParser()
        parser._parse_line(line)
        assert parser._can_network.description == expected_desc

    @pytest.mark.parametrize('line, node, expected_desc', [
        ('CM_ BU_ Node0 "The Description";', 'Node0', 'The Description'),
        ('CM_    BU_   Node0    "The Description";', 'Node0', 'The Description'),
    ])
    def test_parse_node_desc(self, line, node, expected_desc):
        parser = DBCParser()
        parser._can_network.add_node(CANNode(node))
        parser._parse_line(line)
        assert parser._can_network.nodes[node].description == expected_desc

    @pytest.mark.parametrize('line, can_id, expected_desc', [
        ('CM_ BO_ 1234 "The Description";', 1234, 'The Description'),
        ('CM_    BO_   1234    "The Description";', 1234, 'The Description'),
    ])
    def test_parse_message_desc(self, line, can_id, expected_desc):
        parser = DBCParser()
        node = CANNode('Node0')
        node.add_message(CANMessage(can_id, 'CANMessage', 8))
        parser._can_network.add_node(node)
        parser._parse_line(line)
        assert parser._can_network.nodes['Node0'].messages[1234].description == expected_desc

    @pytest.mark.parametrize('line, can_id, signal_name, expected_desc', [
        ('CM_ SG_ 1234 Signal0 "The Description";', 1234, 'Signal0', 'The Description'),
        ('CM_    SG_  1234   Signal0    "The Description";', 1234, 'Signal0', 'The Description'),
    ])
    def test_parse_signal_desc(self, line, can_id, signal_name, expected_desc):
        parser = DBCParser()
        node = CANNode('Node')
        msg = CANMessage(can_id, 'Message', 8)
        sig = CANSignal(signal_name, 0, 8)
        msg.add_signal(sig)
        node.add_message(msg)
        parser._can_network.add_node(node)
        parser._parse_line(line)
        assert sig.description == expected_desc

    def test_parse_multiline_desc(self):
        parser = DBCParser()
        lines = ['CM_ " Line 1\t\n', 'Line2\n', 'Line3  ";']
        for line in lines:
            parser._parse_line(line)
        assert parser._can_network.description == ' Line 1\t\nLine2\nLine3  '

    @pytest.mark.parametrize('line, expected_speed', [
        ('BS_: 500', 500), ('BS_\t :\t 500\t ', 500),
    ])
    def test_parse_bus_config(self, line, expected_speed):
        parser = DBCParser()
        parser._parse_line(line)
        assert parser._can_network.speed == expected_speed

    @pytest.mark.parametrize('line, obj_type_expected, def_name, def_type_expected, check_config', [
                                ('BA_DEF_ SG_ "SGEnumAttribute" ENUM "Val0", "Val1", "Val2" ;', CANSignal, 'SGEnumAttribute',
                                    CANEnumAttributeDefinition, lambda ad: ad.values == ["Val0", "Val1", "Val2"]),
                                ('BA_DEF_ "FloatAttribute" FLOAT 0 50.5;', CANNetwork, 'FloatAttribute',
                                 CANFloatAttributeDefinition, lambda ad: ad.value_min == 0 and ad.value_max == 50.5),
                                ('BA_DEF_ BO_ "BOStringAttribute" STRING;', CANMessage, 'BOStringAttribute',
                                    CANStringAttributeDefinition, lambda ad: True),
                                ('BA_DEF_ BU_ "BUIntAttribute" INT 0 100;', CANNode, 'BUIntAttribute',
                                    CANIntAttributeDefinition, lambda ad: ad.value_min == 0 and ad.value_max == 100),
    ])
    def test_parse_attribute_definition(self, line, obj_type_expected, def_name,  def_type_expected, check_config):
        parser = DBCParser()
        parser._parse_line(line)
        assert def_name in parser._can_network.attributes.definitions
        ad = parser._can_network.attributes.definitions[def_name]
        assert ad.obj_type == obj_type_expected
        assert def_type_expected == type(ad)
        assert check_config(ad)

    def test_parse_attribute_definition_wrong_type(self):
        parser = DBCParser()
        with pytest.raises(AttributeError):
            parser._parse_line('BA_DEF_ BU_ "BUIntAttribute" INTEGER 0 100;')

    @pytest.mark.parametrize('line, default_value_expected, attr_definition', [
        ('BA_DEF_DEF_ "StringAttribute" "DefaultValue";', 'DefaultValue',
            CANStringAttributeDefinition('StringAttribute', None)),
        ('BA_DEF_DEF_ "IntAttribute" 25;', 25, CANIntAttributeDefinition('IntAttribute', None, 0, 50)),
        ('BA_DEF_DEF_ "FloatAttribute" 10.99;', 10.99,  CANFloatAttributeDefinition('FloatAttribute', None, 0, 11)),
        ('BA_DEF_DEF_ "EnumAttribute" 1;', 'Val1',
            CANEnumAttributeDefinition('EnumAttribute', None, ['Val0', 'Val1', 'Val2'])),
    ])
    def test_parse_attribute_default(self, line, default_value_expected, attr_definition):
        parser = DBCParser()
        parser._can_network.attributes.add_definition(attr_definition)
        parser._parse_line(line)
        attr_def = attr_definition
        assert attr_def.default == default_value_expected

    @pytest.mark.parametrize('line, expected_value, attr_definition, cfg_dict', [
        ('BA_ "FloatAttribute" 100.5;', 100.5, CANFloatAttributeDefinition('FloatAttribute', CANNetwork, 99, 101), {}),
        ('BA_ "BUIntAttribute" BU_ Node0 100;', 100,
            CANIntAttributeDefinition('BUIntAttribute', CANNode, 99, 101), {'NODE': 'Node0'}),
        ('BA_ "BOStringAttribute" BO_ 1234 "MessageAttribute";', "MessageAttribute",
            CANStringAttributeDefinition('BOStringAttribute', CANMessage), {'NODE': 'Node0', 'MESSAGE': 1234}),
        ('BA_ "SGEnumAttribute" SG_ 1234 Signal0 2;', "Val2",
            CANEnumAttributeDefinition('SGEnumAttribute', CANSignal, ['Val0', 'Val1', 'Val2']),
                {'NODE': 'Node0', 'MESSAGE': 1234, 'SIGNAL': 'Signal0'}),
    ])
    def test_parse_attribute(self, line, expected_value, attr_definition, cfg_dict):
        parser = DBCParser()
        parser._can_network.attributes.add_definition(attr_definition)

        if attr_definition.obj_type == CANNetwork:
            can_object = parser._can_network
        if attr_definition.obj_type in [CANNode, CANMessage, CANSignal]:
            cfg_dict['NODE'] = CANNode(cfg_dict['NODE'])
            parser._can_network.add_node(cfg_dict['NODE'])
            can_object = cfg_dict['NODE']
        if attr_definition.obj_type in [CANMessage, CANSignal]:
            cfg_dict['MESSAGE'] = CANMessage(cfg_dict['MESSAGE'], 'Message', 1)
            cfg_dict['NODE'].add_message(cfg_dict['MESSAGE'])
            can_object = cfg_dict['MESSAGE']
        if attr_definition.obj_type in [CANSignal]:
            cfg_dict['SIGNAL'] = CANSignal(cfg_dict['SIGNAL'], 0, 8)
            cfg_dict['MESSAGE'].add_signal(cfg_dict['SIGNAL'])
            can_object = cfg_dict['SIGNAL']

        parser._parse_line(line)
        assert can_object.attributes[attr_definition.name].value == expected_value

    @pytest.mark.parametrize('line, expected_name, expected_dict', [
        ('VAL_TABLE_ Numbers 3 "Three" 2 "Two" 1 "One" 0 "Zero";', 'Numbers', {3: 'Three', 2: 'Two', 1: 'One', 0: 'Zero'}),
    ])
    def test_parse_val_table(self, line, expected_name, expected_dict):
        parser = DBCParser()
        parser._parse_line(line)
        assert len(parser._can_network.value_dicts) == 1
        assert expected_name in parser._can_network.value_dicts
        assert parser._can_network.value_dicts[expected_name] == expected_dict

    @pytest.mark.parametrize('line, msg_id, signal_name, expected_dict, val_table_name', [
        ('VAL_ 1234 Signal0 2 "Value2" 1 "Value1" 0 "Value0";', 1234, 'Signal0', {2: 'Value2', 1: 'Value1', 0: 'Value0'}, None),
        ('VAL_ 4321 Signal1 Numbers;', 4321, 'Signal1', {3: 'Three', 2: 'Two', 1: 'One', 0: 'Zero'}, 'Numbers'),
    ])
    def test_parse_val(self, line, msg_id, signal_name, expected_dict, val_table_name):
        parser = DBCParser()
        if val_table_name:
            parser._can_network.add_value_dict(val_table_name, expected_dict)

        node = CANNode('Node')
        parser._can_network.add_node(node)
        msg = CANMessage(msg_id, 'Message', 1)
        node.add_message(msg)
        sig = CANSignal(signal_name, 0, 8)
        msg.add_signal(sig)

        parser._parse_line(line)

        assert sig.value_dict == expected_dict

def test_whole_dbc():
    parser = DBCParser()
    candb = parser.parse_file('docs/DBC_template.dbc')
    assert len(candb.nodes) == 3
    assert candb.version == "1.0"
    assert candb.speed == 500

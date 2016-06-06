__author__ = "Stefan Hölzl"

import pytest

from canpy.canbus import CANNode, CANMessage, CANSignal
from canpy.parser.dbc import DBCParser

testset_nodes = ['BU_   :   Node0   Node1    Node2', 'BU_:Node0 Node1 Node2']
testset_version = ['VERSION "1.0"', 'VERSION    "1.0"']
testset_message = ['BO_ 1234 CANMessage:8 Node0', 'BO_  1234  CANMessage  :  8  Node0']
testset_signal =  ['SG_     Signal1     :    32|32@1+   (   33.3     ,  0    )  [0|100]     "%"     Node1   Node2',
                   'SG_ Signal1:32|32@1+ (33.3,0) [ 0 | 100  ] "%" Node1 Node2']
testset_signal_multiplexer = ['SG_ Signal1  M   :32|32@1+ (33.3,0)[0|100] "%" Node1 Node2']
testset_signal_multiplexed = ['SG_ Signal1  m34  :32|32@1+ (33.3,0)[0|100] "%" Node1 Node2']
testset_desc_candb = ['CM_ "The Description";', 'CM_    "The Description";']
testset_desc_node = ['CM_ BU_ Node0 "The Description";', 'CM_    BU_   Node0    "The Description";']
testset_desc_message = ['CM_ BO_ 1234 "The Description";', 'CM_    BO_   1234    "The Description";']
testset_desc_signal = ['CM_ SG_ 1234 Signal0 "The Description";', 'CM_    SG_  1234   Signal0    "The Description";']

class TestDBCParseLine(object):
    @pytest.mark.parametrize("line", testset_version)
    def test_parse_verison(self, line):
        parser = DBCParser()
        parser._parse_line(line)
        assert parser._canbus.version == "1.0"

    @pytest.mark.parametrize("line", testset_nodes)
    def test_parse_nodes(self, line):
        parser = DBCParser()
        parser._parse_line(line)
        assert len(parser._canbus.nodes) == 3
        node_names = list(map(lambda n: n.name, parser._canbus.nodes))
        assert "Node0" in node_names
        assert "Node1" in node_names
        assert "Node2" in node_names

    @pytest.mark.parametrize("line", testset_message)
    def test_parse_message(self, line):
        parser = DBCParser()
        sender = CANNode('Node0')
        parser._canbus.add_node(sender)
        parser._parse_line(line)
        msg = parser._canbus.nodes[0].messages[0]
        assert msg.name == 'CANMessage'
        assert msg.can_id == 1234
        assert msg.length == 8
        assert msg.sender == sender

    @pytest.mark.parametrize("line", testset_signal)
    def test_parse_signal(self, line):
        parser = DBCParser()
        node0 = CANNode('Node0')
        parser._canbus.add_node(node0)
        node1 = CANNode('Node1')
        parser._canbus.add_node(node1)
        node2 = CANNode('Node2')
        parser._canbus.add_node(node2)
        msg = CANMessage(1, 'CANMessage', 8)
        node0.add_message(msg)
        parser._mode = ('MESSAGE', msg)
        parser._parse_line(line)
        sig = msg.signals[0]
        assert sig.name == 'Signal1'
        assert sig.start_bit == 32
        assert sig.length == 32
        assert sig.little_endian == True
        assert sig.signed == False
        assert sig.factor == 33.3
        assert sig.value_min == 0
        assert sig.value_max == 100
        assert sig.unit == '%'
        assert sig.is_multiplexer == False
        assert sig.multiplexer_id == None
        assert node1 in sig.receiver
        assert node2 in sig.receiver

    def test_parse_signal_wrong_block(self):
        parser = DBCParser()
        node = CANNode('Node0')
        parser._mode = ('NORMAL', None)
        with pytest.raises(RuntimeError):
            parser._parse_line(testset_signal[0])

    @pytest.mark.parametrize("line", testset_signal_multiplexer)
    def test_parse_multiplexed_signal(self, line):
        parser = DBCParser()
        node0 = CANNode('Node0')
        msg = CANMessage(1, 'CANMessage', 8)
        node0.add_message(msg)
        node1 = CANNode('Node1')
        parser._canbus.add_node(node1)
        node2 = CANNode('Node2')
        parser._canbus.add_node(node2)
        parser._mode = ('MESSAGE', msg)
        parser._parse_line(line)
        sig = msg.signals[0]
        assert sig.is_multiplexer == True
        assert sig.multiplexer_id == None

    @pytest.mark.parametrize("line", testset_signal_multiplexed)
    def test_parse_multiplexer_signal(self, line):
        parser = DBCParser()
        node0 = CANNode('Node0')
        msg = CANMessage(1, 'CANMessage', 8)
        node0.add_message(msg)
        node1 = CANNode('Node1')
        parser._canbus.add_node(node1)
        node2 = CANNode('Node2')
        parser._canbus.add_node(node2)
        parser._mode = ('MESSAGE', msg)
        parser._parse_line(line)
        sig = msg.signals[0]
        assert sig.is_multiplexer == False
        assert sig.multiplexer_id == 34

    def test_parse_candb_desc(self):
        parser = DBCParser()
        parser._parse_line(testset_desc_candb[0])
        assert parser._canbus.description == "The Description"

    def test_parse_candb_node(self):
        parser = DBCParser()
        parser._canbus.add_node(CANNode('Node0'))
        parser._parse_line(testset_desc_node[0])
        assert parser._canbus.nodes[0].description == "The Description"

    def test_parse_candb_message(self):
        parser = DBCParser()
        node = CANNode('Node0')
        node.add_message(CANMessage(1234, 'CANMessage', 8))
        parser._canbus.add_node(node)
        parser._parse_line(testset_desc_message[0])
        assert parser._canbus.nodes[0].messages[0].description == "The Description"

    def test_parse_candb_signal(self):
        parser = DBCParser()
        node = CANNode('Node0')
        msg = CANMessage(1234, 'CANMessage', 8)
        sig = CANSignal('Signal0', 0, 8)
        msg.add_signal(sig)
        node.add_message(msg)
        parser._canbus.add_node(node)
        parser._parse_line(testset_desc_signal[0])
        assert sig.description == "The Description"


class TestDBCStringParser(object):
    @pytest.mark.parametrize("line", testset_version)
    def test_parse_version(self, line):
        assert DBCParser._parse_version(line) == "1.0"

    @pytest.mark.parametrize("line", testset_nodes)
    def test_parse_nodes(self, line):
        assert DBCParser._parse_nodes(line) == ["Node0", "Node1", "Node2"]

    @pytest.mark.parametrize("line", testset_message)
    def test_parse_message(self, line):
        msg = DBCParser._parse_message(line)
        assert msg.can_id == 1234
        assert msg.name == 'CANMessage'
        assert msg.length == 8
        assert msg.sender == 'Node0'

    @pytest.mark.parametrize("line", testset_signal)
    def test_parse_signal(self, line):
        sig = DBCParser._parse_signal(line)
        assert sig.name == 'Signal1'
        assert sig.start_bit == 32
        assert sig.length == 32
        assert sig.little_endian == True
        assert sig.signed == False
        assert sig.factor == 33.3
        assert sig.min_value == 0
        assert sig.max_value == 100
        assert sig.unit == '%'
        assert sig.receivers == ['Node1', 'Node2']
        assert sig.is_multiplexer == False
        assert sig.multiplexer_id == None

    def test_parse_signal_no_unit_signed(self):
        sig = DBCParser._parse_signal('SG_ Signal0 : 0|32@1- (1,0) [0|0] "" Node1 Node2')
        assert sig.signed == True
        assert sig.unit == ""

    @pytest.mark.parametrize("line", testset_signal_multiplexer)
    def test_parse_multiplexer_signal(self, line):
        sig = DBCParser._parse_signal(line)
        assert sig.is_multiplexer == True
        assert sig.multiplexer_id == None


    @pytest.mark.parametrize("line", testset_signal_multiplexed)
    def test_parse_multiplexed_signal(self, line):
        sig = DBCParser._parse_signal(line)
        assert sig.is_multiplexer == False
        assert sig.multiplexer_id == 34

    @pytest.mark.parametrize("line", testset_desc_candb)
    def test_parse_candb_desc(self, line):
        desc = DBCParser._parse_description(line)
        assert desc.value == "The Description"
        assert desc.type == "CANDB"
        assert desc.identifier == None

    @pytest.mark.parametrize("line", testset_desc_node)
    def test_parse_candb_node(self, line):
        desc = DBCParser._parse_description(line)
        assert desc.value == "The Description"
        assert desc.type == "NODE"
        assert desc.identifier == 'Node0'

    @pytest.mark.parametrize("line", testset_desc_message)
    def test_parse_candb_message(self, line):
        desc = DBCParser._parse_description(line)
        assert desc.value == "The Description"
        assert desc.type == "MESSAGE"
        assert desc.identifier == 1234

    @pytest.mark.parametrize("line", testset_desc_signal)
    def test_parse_candb_signal(self, line):
        desc = DBCParser._parse_description(line)
        assert desc.value == "The Description"
        assert desc.type == "SIGNAL"
        assert desc.identifier == (1234, 'Signal0')

def test_whole_dbc():
    parser = DBCParser()
    candb = parser.parse_file('tests/test.dbc')
    assert len(candb.nodes) == 3
    assert candb.version == "1.0"

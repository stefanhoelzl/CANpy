__author__ = "Stefan Hölzl"

import pytest

from canpy.canbus import CANNode, CANMessage, CANSignal
from canpy.parser.dbc_parser import DBCParser

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

class TestDBCParsing(object):
    @pytest.mark.parametrize("line", testset_version)
    def test_parse_version(self, line):
        parser = DBCParser()
        parser._parse_line(line)
        assert parser._canbus.version == "1.0"

    @pytest.mark.parametrize("line", testset_nodes)
    def test_parse_nodes(self, line):
        parser = DBCParser()
        parser._parse_line(line)
        assert len(parser._canbus.nodes) == 3
        node_names = parser._canbus._nodes.keys()
        assert "Node0" in node_names
        assert "Node1" in node_names
        assert "Node2" in node_names

    @pytest.mark.parametrize("line", testset_message)
    def test_parse_message(self, line):
        parser = DBCParser()
        sender = CANNode('Node0')
        parser._canbus.add_node(sender)
        parser._parse_line(line)
        msg = parser._canbus.nodes['Node0'].messages[0]
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

    def test_parse_signal_no_unit_signed_no_receiver(self):
        parser = DBCParser()
        node0 = CANNode('Node0')
        parser._canbus.add_node(node0)
        msg = CANMessage(1, 'CANMessage', 8)
        node0.add_message(msg)
        parser._mode = ('MESSAGE', msg)
        parser._parse_line('SG_ Signal0 : 0|32@1- (1,0) [0|0] "" Node0')
        sig = msg.signals[0]
        assert sig.signed == True
        assert sig.unit == ""

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

    def test_parse_node_desc(self):
        parser = DBCParser()
        parser._canbus.add_node(CANNode('Node0'))
        parser._parse_line(testset_desc_node[0])
        assert parser._canbus.nodes['Node0'].description == "The Description"

    def test_parse_message_desc(self):
        parser = DBCParser()
        node = CANNode('Node0')
        node.add_message(CANMessage(1234, 'CANMessage', 8))
        parser._canbus.add_node(node)
        parser._parse_line(testset_desc_message[0])
        assert parser._canbus.nodes['Node0'].messages[0].description == "The Description"

    def test_parse_signal_desc(self):
        parser = DBCParser()
        node = CANNode('Node0')
        msg = CANMessage(1234, 'CANMessage', 8)
        sig = CANSignal('Signal0', 0, 8)
        msg.add_signal(sig)
        node.add_message(msg)
        parser._canbus.add_node(node)
        parser._parse_line(testset_desc_signal[0])
        assert sig.description == "The Description"

    def test_parse_multiline_desc(self):
        parser = DBCParser()
        lines = ['CM_ " Line 1\t\n', 'Line2\n', 'Line3  ";']
        for line in lines:
            parser._parse_line(line)
        assert parser._canbus.description == ' Line 1\t\nLine2\nLine3  '

def test_whole_dbc():
    parser = DBCParser()
    candb = parser.parse_file('tests/test.dbc')
    assert len(candb.nodes) == 3
    assert candb.version == "1.0"

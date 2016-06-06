__author__ = "Stefan Hölzl"

import pytest

from canpy.canbus import CANBus, CANMessage, CANNode, CANSignal

class TestCANBus(object):
    def test_add_node(self):
        cdb = CANBus()
        cdb.add_node(CANNode('TestNode'))
        assert len(cdb.nodes) == 1

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
        assert len(node.messages) == 1

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
        assert len(msg.signals) == 1

    def test_add_signal_with_message(self):
        sig = CANSignal('Signal', 0, 8)
        sig.message = CANMessage(1, 'Name', 8)
        msg = CANMessage(2, 'Name', 8)
        with pytest.raises(RuntimeError):
            msg.add_signal(sig)

class TestCANSignal(object):
    def test_add_receiver(self):
        node = CANNode('TestNode')
        sig = CANSignal('Signal', 0, 8)
        sig.add_receiver(node)
        assert len(sig.receiver) == 1

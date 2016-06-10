__author__ = 'Stefan Hölzl'

from canpy.can_communication_handler import CANCommunicationHandler
from canpy.parser.dbc_parser import DBCParser


class CANInterfaceStub(object):
    def __init__(self):
        self.registered_receiving_message_ids = []
        self.sent_messages = []

    def register_receiving_message(self, can_id):
        self.registered_receiving_message_ids.append(can_id)

    def initialize(self, speed):
        pass

    def send_message(self, can_id, data):
        self.sent_messages.append((can_id, data))


class TestCANCommunicationHandler(object):
    def test_connect_nodes_to_interface_sending_messages(self):
        ci = CANInterfaceStub()
        cn = DBCParser().parse_file('tests/test_communication_handler.dbc')
        cch = CANCommunicationHandler(cn, lambda c, t: None)
        cch.connect(['Node0'], ci)
        assert 0 in cch._registered_messages.keys()
        assert cch._registered_messages[0] == ci

    def test_connect_nodes_to_interface_receiving_messages(self):
        ci = CANInterfaceStub()
        cn = DBCParser().parse_file('tests/test_communication_handler.dbc')
        cch = CANCommunicationHandler(cn, lambda c, t: None)
        cch.connect(['Node1'], ci)
        assert 0 in ci.registered_receiving_message_ids

    def test_initialize_cyclic_messages(self):
        ci = CANInterfaceStub()
        cn = DBCParser().parse_file('tests/test_communication_handler.dbc')
        callback_cylce_times = []

        def callback(c, t):
            nonlocal callback_cylce_times
            callback_cylce_times.append(c)

        cch = CANCommunicationHandler(cn, callback)
        cch.connect(['Node0'], ci)
        cch.initialize()
        assert 10 in callback_cylce_times
        assert 100 in callback_cylce_times

    def test_send_messages(self):
        ci = CANInterfaceStub()
        cn = DBCParser().parse_file('tests/test_communication_handler.dbc')
        callbacks = []

        def callback(c, t):
            nonlocal callbacks
            callbacks.append(t)

        cch = CANCommunicationHandler(cn, callback)
        cch.connect(['Node0'], ci)
        cch.initialize()
        cn.get_message(1).is_active = False
        list(map(lambda cb: cb(), callbacks))
        assert len(ci.sent_messages) == 2


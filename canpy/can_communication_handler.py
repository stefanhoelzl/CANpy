__author__ = "Stefan Hölzl"


class CANCommunicationHandler(object):
    """Takes care of sending and receiving CAN-Messages.


    class CANInterfaceProtocol(object):
        def __init__(self):
        def register_receiving_message(self, can_id):
        def register_receive_callback(self, callback):
        def initialize(self, speed):
        def send_message(self, can_id, data):
    """
    def __init__(self, can_network, thread_register_callback):
        self._can_network = can_network
        self._thread_register_callback = thread_register_callback
        self._registered_messages = {}

    def initialize(self):
        msgs_by_cycle_time = {}
        for can_id in self._registered_messages:
            msg = self._can_network.get_message(can_id)
            if 'cyclic' in msg.attributes['GenMsgSendType'].value and msg.attributes['GenMsgCycleTime'].value > 0:
                cycle_time = msg.attributes['GenMsgCycleTime'].value
                if cycle_time not in msgs_by_cycle_time.keys():
                    msgs_by_cycle_time[cycle_time] = []
                msgs_by_cycle_time[cycle_time].append(msg)
        for cycle_time, msgs in msgs_by_cycle_time.items():
            callback = lambda m=msgs: self._send_messages(m)
            self._thread_register_callback(cycle_time, callback)

    def connect(self, node_names, can_interface):
        for node_name in node_names:
            node = self._can_network.nodes[node_name]
            for msg in node.messages.values():
                self._registered_messages[msg.can_id] = can_interface
            for recv_msg in self._can_network.get_consumed_messages(node):
                can_interface.register_receiving_message(recv_msg.can_id)

    def _send_messages(self, msgs):
        for msg in msgs:
            can_interface = self._registered_messages[msg.can_id]
            if 'IfActive' not in msg.attributes['GenMsgSendType'].value:
                can_interface.send_message(msg.can_id, int(msg))
            elif msg.is_active:
                can_interface.send_message(msg.can_id, int(msg))


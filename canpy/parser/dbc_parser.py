__author__ = "Stefan Hölzl"

import re
import collections

from canpy.canbus import CANBus, CANNode, CANMessage, CANSignal


class DBCParser(object):
    """Parses a DBC-file.
    Follows docs/DBC_Specification.md"""
    def __init__(self):
        """Initializes the object"""
        self._mode = ('NORMAL', None)
        self._canbus = CANBus()

        self._keywords = {'VERSION': self._parse_version,
                          'BU_':     self._parse_nodes,
                          'BO_':     self._parse_message,
                          'SG_':     self._parse_signal,
                          'CM_':     self._parse_description
                         }

    # Method definitions
    def parse_file(self, file_name):
        """Parses a dbc file

        Args:
            file_name: Name of the file to parse.
        Returns:
            CANDB object
        """
        self._canbus = CANBus()
        with open(file_name, 'r') as dbc_fh:
            for line in dbc_fh:
                self._parse_line(line.strip())
        return self._canbus

    def _parse_line(self, line):
        """Parses one line of a dbc file and updates the CANDB

        Args:
            line: One line of a dbc file as string
        Raises:
            RuntimeError: If signal description is not in a message block
        """

        for key, parse_function in self._keywords.items():
            if line.startswith(key):
                parse_function(line)

    def _parse_version(self, version_str):
        """Parses a version string

        Args:
            version_str: String containing version informations
        Returns:
            Version from the verstion string
        """
        reg = re.search('VERSION\s*"(?P<version>\S+)"', version_str)
        self._canbus.version = reg.group('version')
        self._mode = ('NORMAL', None)

    def _parse_nodes(self, nodes_str):
        """Parses a nodes string

        Args:
            nodes_str: String containing nodes informations
        Returns:
            List with all the node names
        """
        reg = re.search('BU_\s*:(?P<nodes>.+)', nodes_str)
        node_names_str = re.sub('\s+', ' ', reg.group('nodes')).strip()
        for node_name in node_names_str.split(' '):
            self._canbus.add_node(CANNode(node_name))
        self._mode = ('NORMAL', None)

    def _parse_message(self, message_str):
        """Parses a message string

        Args:
            message_str: String with message informations
        Returns:
            Namedtuple with can_id, name, length and sender name of the message
        """
        reg = re.search('BO_\s*(?P<can_id>\d+)\s*(?P<name>\S+)\s*:\s*(?P<length>\d+)\s*(?P<sender>\S+)', message_str)
        message = CANMessage(int(reg.group('can_id')), reg.group('name').strip(), int(reg.group('length')))
        self._canbus.get_node(reg.group('sender').strip()).add_message(message)
        self._mode = ('MESSAGE', message)

    def _parse_signal(self, signal_str):
        """Parses a signal string

        Args:
            signal_str: String with signal informations
        Returns:
            Namedtuple with the signal informations
        """
        pattern  = 'SG_\s*(?P<name>\S+)\s*(?P<is_multipexer>M)?(?P<multiplexer_id>m\d+)?\s*:\s*'
        pattern += '(?P<start_bit>\d+)\|(?P<length>\d+)\@(?P<endianness>[0|1])(?P<sign>[\+|\-])\s*'
        pattern += '\(\s*(?P<factor>\S+)\s*,\s*(?P<offset>\S+)\s*\)\s*\[\s*(?P<min_value>\S+)\s*\|\s*(?P<max_value>\S+)\s*\]'
        pattern += '\s*"(?P<unit>\S*)"\s*(?P<receivers>.+)'
        reg = re.search(pattern, signal_str)

        little_endian = True if reg.group('endianness').strip() == '1' else False
        signed = True if reg.group('sign').strip() == '-' else False
        receivers = [receiver.strip() for receiver in re.sub('\s+', ' ', reg.group('receivers')).strip().split(' ')]
        is_multiplexer = True if reg.group('is_multipexer') else False
        multiplexer_id = int(reg.group('multiplexer_id').strip()[1:]) if reg.group('multiplexer_id') else None

        if self._mode[0] != 'MESSAGE':
            raise RuntimeError('Signal description not in message block')
        signal = CANSignal(name=reg.group('name').strip(), start_bit=int(reg.group('start_bit')),
                           length=int(reg.group('length')), little_endian=little_endian, signed=signed,
                           factor=float(reg.group('factor')), offset=float(reg.group('offset')),
                           value_min=float(reg.group('min_value')), value_max=float(reg.group('max_value')),
                           unit=reg.group('unit').strip(), is_multiplexer=is_multiplexer, multiplexer_id=multiplexer_id)
        for node_name in receivers:
            node = self._canbus.get_node(node_name)
            signal.add_receiver(node)
        self._mode[1].add_signal(signal)

    def _parse_description(self, desc_str):
        """Parses a description string

        Args:
            desc_str: String with description informations
        Returns:
            Namedtuple with value, type and identifier of the description
        """
        pattern  = 'CM_\s*(?P<node>BU_)?\s*(?P<msg>BO_)?\s*(?P<sig>SG_)?\s*'
        pattern += '(?P<can_id>\d*)?\s*(?P<name>\S*)?\s*"(?P<value>.+)";'
        reg = re.search(pattern, desc_str)

        desc_type = 'CANDB'
        desc_id = None
        if reg.group('node'):
            self._canbus.get_node(reg.group('name').strip()).description = reg.group('value')
        elif reg.group('msg'):
            self._canbus.get_message(int(reg.group('can_id'))).description = reg.group('value')
        elif reg.group('sig'):
            self._canbus.get_signal(can_id=int(reg.group('can_id')), name=reg.group('name').strip()).description = reg.group('value')
        else:
            self._canbus.description = reg.group('value')

        self._mode = ('NORMAL', None)



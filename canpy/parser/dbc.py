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
        if line[:7] == 'VERSION':
            self._canbus .version = DBCParser._parse_version(line)
            self._mode = ('NORMAL', None)
        elif line[:3] == 'BU_':
            node_names = DBCParser._parse_nodes(line)
            for node_name in node_names:
                self._canbus.add_node(CANNode(node_name))
            self._mode = ('NORMAL', None)
        elif line[:3] == 'BO_':
            md = DBCParser._parse_message(line)
            message = CANMessage(md.can_id, md.name, md.length)
            self._canbus.get_node(md.sender).add_message(message)
            self._mode = ('MESSAGE', message)
        elif line[:3] == 'SG_':
            if self._mode[0] != 'MESSAGE':
                raise RuntimeError('Signal description not in message block')
            sd = DBCParser._parse_signal(line)
            signal = CANSignal(name=sd.name, start_bit=sd.start_bit, length=sd.length, little_endian=sd.little_endian,
                               signed=sd.signed, factor=sd.factor, offset=sd.offset, value_min=sd.min_value,
                               value_max=sd.max_value, unit=sd.unit,
                               is_multiplexer=sd.is_multiplexer, multiplexer_id=sd.multiplexer_id)
            for node_name in sd.receivers:
                node = self._canbus.get_node(node_name)
                signal.add_receiver(node)
            self._mode[1].add_signal(signal)
        elif line[:3] == 'CM_':
            dc = DBCParser._parse_description(line)
            if dc.type == 'CANDB':
                self._canbus.description = dc.value
            elif dc.type == 'NODE':
                self._canbus.get_node(dc.identifier).description = dc.value
            elif dc.type == 'MESSAGE':
                self._canbus.get_message(dc.identifier).description = dc.value
            elif dc.type == 'SIGNAL':
                self._canbus.get_signal(dc.identifier[0], dc.identifier[1]).description = dc.value
            self._mode = ('NORMAL', None)

    @staticmethod
    def _parse_version(version_str):
        """Parses a version string

        Args:
            version_str: String containing version informations
        Returns:
            Version from the verstion string
        """
        reg = re.search('VERSION\s*"(?P<version>\S+)"', version_str)
        return reg.group('version')

    @staticmethod
    def _parse_nodes(nodes_str):
        """Parses a nodes string

        Args:
            nodes_str: String containing nodes informations
        Returns:
            List with all the node names
        """
        reg = re.search('BU_\s*:(?P<nodes>.+)', nodes_str)
        node_names_str = re.sub('\s+', ' ', reg.group('nodes')).strip()
        return node_names_str.split(' ')

    @staticmethod
    def _parse_message(message_str):
        """Parses a message string

        Args:
            message_str: String with message informations
        Returns:
            Namedtuple with can_id, name, length and sender name of the message
        """
        reg = re.search('BO_\s*(?P<can_id>\d+)\s*(?P<name>\S+)\s*:\s*(?P<length>\d+)\s*(?P<sender>\S+)', message_str)
        cmd = collections.namedtuple('CANMessageDescription', 'can_id name length sender')
        return cmd(can_id=int(reg.group('can_id')),name=reg.group('name').strip(),
                   length=int(reg.group('length')), sender=reg.group('sender').strip())

    @staticmethod
    def _parse_signal(signal_str):
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

        csd = collections.namedtuple('CANSignalDescription', 'name start_bit length little_endian signed factor offset '
                                                             'min_value max_value unit receivers '
                                                             'is_multiplexer multiplexer_id')
        return csd(name=reg.group('name').strip(), start_bit=int(reg.group('start_bit')), length=int(reg.group('length')),
                   little_endian=little_endian, signed=signed, factor=float(reg.group('factor')),
                   offset=float(reg.group('offset')), min_value=float(reg.group('min_value')),
                   max_value=float(reg.group('max_value')), unit=reg.group('unit').strip(), receivers=receivers,
                   is_multiplexer=is_multiplexer, multiplexer_id=multiplexer_id)

    @staticmethod
    def _parse_description(desc_str):
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
            desc_type = 'NODE'
            desc_id = reg.group('name').strip()
        elif reg.group('msg'):
            desc_type = 'MESSAGE'
            desc_id = int(reg.group('can_id'))
        elif reg.group('sig'):
            desc_type = 'SIGNAL'
            desc_id = (int(reg.group('can_id')), reg.group('name').strip())

        dc = collections.namedtuple('DescriptionContainer', 'value type identifier')
        return dc(value=reg.group('value'), type=desc_type, identifier=desc_id)

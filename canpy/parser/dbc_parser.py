__author__ = "Stefan Hölzl"

import re

from canpy.can_objects import CANNetwork, CANNode, CANMessage, CANSignal
from canpy.can_objects.can_attribute import *


class DBCParser(object):
    """Parses a DBC-file.
    Follows docs/DBC_Specification.md"""
    def __init__(self):
        """Initializes the object"""
        self._mode = ('NORMAL', None)
        self._can_network = CANNetwork()

        self._keywords = {'VERSION':      self._parse_version,
                          'BU_':          self._parse_nodes,
                          'BO_ ':         self._parse_message,
                          'SG_ ':         self._parse_signal,
                          'CM_ ':         self._parse_description,
                          'BS_':          self._parse_bus_configuration,
                          'BA_DEF_ ':     self._parse_attribute_definition,
                          'BA_DEF_DEF_':  self._parse_attribute_default_value,
                          'BA_ ':         self._parse_attribute,
                          'VAL_TABLE_':   self._parse_val_table,
                          'VAL_ ':        self._parse_signal_value_dict
                         }
        self._force_parser = None

    # Method definitions
    def parse_file(self, file_name):
        """Parses a dbc file

        Args:
            file_name: Name of the file to parse.
        Returns:
            CANBus object
        """
        self._can_network = CANNetwork()
        with open(file_name, 'r') as dbc_fh:
            for line in dbc_fh:
                self._parse_line(line.strip())
        return self._can_network

    def _parse_line(self, line):
        """Parses one line of a dbc file

        Args:
            line: One line of a dbc file as string
        """
        if self._force_parser:
            self._force_parser(line)
        else:
            for key, parse_function in self._keywords.items():
                if line.startswith(key):
                    parse_function(line)

    def _parse_version(self, version_str):
        """Parses a version string and updates the CANBus

        Args:
            version_str: String containing version informations
        """
        reg = re.search('VERSION\s+"(?P<version>\S+)"', version_str)
        self._can_network.version = reg.group('version')

    def _parse_nodes(self, nodes_str):
        """Parses a nodes string and updates the CANBus

        Args:
            nodes_str: String containing nodes informations
        """
        reg = re.search('BU_\s*:\s*(?P<nodes>.+)\s*', nodes_str)
        node_names_str = re.sub('\s+', ' ', reg.group('nodes')).strip()
        for node_name in node_names_str.split(' '):
            self._can_network.add_node(CANNode(node_name))

    def _parse_message(self, message_str):
        """Parses a message string and updates the CANBus

        Args:
            message_str: String with message informations
        """
        reg = re.search('BO_\s+(?P<can_id>\d+)\s+(?P<name>\S+)\s*:\s*(?P<length>\d+)\s+(?P<sender>\S+)', message_str)
        message = CANMessage(int(reg.group('can_id')), reg.group('name').strip(), int(reg.group('length')))
        self._can_network.nodes[reg.group('sender').strip()].add_message(message)
        self._mode = ('MESSAGE', message)

    def _parse_signal(self, signal_str):
        """Parses a signal string and updates the CANBus

        Args:
            signal_str: String with signal informations
        Raises:
            RuntimeError: If signal definition is not in a message block
        """
        if self._mode[0] != 'MESSAGE':
            raise RuntimeError('Signal description not in message block')

        pattern  = 'SG_\s+(?P<name>\S+)\s*(?P<is_multipexer>M)?(?P<multiplexer_id>m\d+)?\s*:\s*'
        pattern += '(?P<start_bit>\d+)\|(?P<length>\d+)\@(?P<endianness>[0|1])(?P<sign>[\+|\-])\s*'
        pattern += '\(\s*(?P<factor>\S+)\s*,\s*(?P<offset>\S+)\s*\)\s*'
        pattern += '\[\s*(?P<min_value>\S+)\s*\|\s*(?P<max_value>\S+)\s*\]\s*"(?P<unit>\S*)"\s+(?P<receivers>.+)'
        reg = re.search(pattern, signal_str)

        little_endian = True if reg.group('endianness').strip() == '1' else False
        signed = True if reg.group('sign').strip() == '-' else False
        receivers = [receiver.strip() for receiver in re.sub('\s+', ' ', reg.group('receivers')).strip().split(' ')]
        is_multiplexer = True if reg.group('is_multipexer') else False
        multiplexer_id = int(reg.group('multiplexer_id').strip()[1:]) if reg.group('multiplexer_id') else None

        signal = CANSignal(name=reg.group('name').strip(), start_bit=int(reg.group('start_bit')),
                           length=int(reg.group('length')), little_endian=little_endian, signed=signed,
                           factor=float(reg.group('factor')), offset=float(reg.group('offset')),
                           value_min=float(reg.group('min_value')), value_max=float(reg.group('max_value')),
                           unit=reg.group('unit').strip(), is_multiplexer=is_multiplexer, multiplexer_id=multiplexer_id)
        for node_name in receivers:
            node = self._can_network.nodes[node_name]
            signal.add_receiver(node)
        self._mode[1].add_signal(signal)

    def _parse_description(self, desc_str):
        """Parses a description string and updates the CANBus

        Args:
            desc_str: String with description informations
        """
        pattern  = 'CM_\s+(?P<node>BU_)?(?P<msg>BO_)?(?P<sig>SG_)?\s*'
        pattern += '(?P<can_id>\d*)?\s*(?P<name>\S*)?\s*"(?P<value>.+)'
        reg = re.search(pattern, desc_str)

        desc_item = None
        if reg.group('node'):
            desc_item = self._can_network.nodes[reg.group('name').strip()]
        elif reg.group('msg'):
            desc_item = self._can_network.get_message(int(reg.group('can_id')))
        elif reg.group('sig'):
            desc_item = self._can_network.get_signal(can_id=int(reg.group('can_id')), name=reg.group('name').strip())
        else:
            desc_item = self._can_network

        value = reg.group('value')

        if value.strip()[-2:] == '";':
            desc_item.description = value.replace('";', '')
            self._mode = ('NORMAL', None)
        else:
            self._force_parser = self._parse_multiline_description
            self._mode = ('MULTILINE_DESCRIPTION', (desc_item, value + '\n'))

    def _parse_multiline_description(self, line):
        """Parses the following lines of a multiline description and updates the CANBus

        Args:
            line: following lines of a multiline description
        """
        if line.strip()[-2:] == '";':
            self._mode[1][0].description = self._mode[1][1] + line.replace('";', '')
            self._force_parser = False
            self._mode = ('NORMAL', None)
        else:
            self._mode = (self._mode[0], (self._mode[1][0], self._mode[1][1] + line))

    def _parse_bus_configuration(self, bus_config_str):
        """Parses a bus configuration string and updates the CANBus

        Args:
            bus_config_str: String with bus configuration definition
        """
        pattern = 'BS_\s*:\s*(?P<speed>\d+)?\s*'
        reg = re.search(pattern, bus_config_str)
        if reg.group('speed'):
            self._can_network.speed = int(reg.group('speed'))

    def _parse_attribute_definition(self, attribute_definition_str):
        """Parses a attribute definition string and updates the CANBus

        Args:
            attribute_definition_str: String with attribute definition definition
        """
        pattern  = 'BA_DEF_\s+(?P<obj_type>\S+)?\s*"(?P<attr_name>\S+)"\s+'
        pattern += '(?P<attr_type>\S+)\s*(?P<attr_config>.+)?\s*;'
        reg = re.search(pattern, attribute_definition_str)

        obj_type = CANNetwork
        if 'BU_' in reg.groups():
            obj_type = CANNode
        elif 'BO_' in reg.groups():
            obj_type = CANMessage
        elif 'SG_' in reg.groups():
            obj_type = CANSignal

        ad = None
        if reg.group('attr_type') == 'FLOAT':
            reg_cfg = re.search('\s*(?P<min>\S+)\s*(?P<max>\S+)', reg.group('attr_config'))
            ad = CANFloatAttributeDefinition(reg.group('attr_name'), obj_type,
                                             float(reg_cfg.group('min')), float(reg_cfg.group('max')))
        elif reg.group('attr_type') == 'INT':
            reg_cfg = re.search('\s*(?P<min>\S+)\s*(?P<max>\S+)', reg.group('attr_config'))
            ad = CANIntAttributeDefinition(reg.group('attr_name'), obj_type,
                                           float(reg_cfg.group('min')), float(reg_cfg.group('max')))
        elif reg.group('attr_type') == 'STRING':
            ad = CANStringAttributeDefinition(reg.group('attr_name'), obj_type)
        elif reg.group('attr_type') == 'ENUM':
            values = reg.group('attr_config').split(',')
            values = list(map(lambda val: val.replace('"', '').strip(), values))
            ad = CANEnumAttributeDefinition(reg.group('attr_name'), obj_type, values)
        else:
            raise AttributeError('Attribute definition type unkown')

        self._can_network.attributes.add_definition(ad)

    def _parse_attribute_value(self, cad, attr_value_str):
        """Parses a attribute value string

        Args:
            attr_value_str: String with attribute value
        Returns:
            Parse attribute value
        """
        if type(cad) == CANStringAttributeDefinition:
            reg_str = re.search('\s*"(?P<value>\S+)"\s*', attr_value_str)
            attr_value_str = reg_str.group('value')
        return attr_value_str

    def _parse_attribute_default_value(self, attr_default_str):
        """Parses a attribute default value string and updates the CANBus

        Args:
            attr_default_str: String with attribute default value
        """
        pattern = 'BA_DEF_DEF_\s+"(?P<attr_name>\S+)"\s+(?P<default>\S+)\s*;'
        reg = re.search(pattern, attr_default_str)

        cad = self._can_network.attributes.definitions[reg.group('attr_name')]
        default_value = self._parse_attribute_value(cad, reg.group('default'))
        cad.default = default_value

    def _parse_attribute(self, attribute_str):
        """Parses a attribute string and updates the CANBus

        Args:
            attribute_str: String with attribute
        """
        pattern  = 'BA_\s+"(?P<attr_name>\S+)"\s*(?P<node>BU_)?(?P<msg>BO_)?(?P<sig>SG_)?\s*'
        pattern += '(?P<can_id>\d*)?\s*(?P<name>\S*)?\s+(?P<value>\S+)\s*;'
        reg = re.search(pattern, attribute_str)

        can_object = self._can_network
        if reg.group('node'):
            can_object = self._can_network.nodes[reg.group('name')]
        elif reg.group('msg'):
            can_object = self._can_network.get_message(int(reg.group('can_id')))
        elif reg.group('sig'):
            can_object = self._can_network.get_signal(int(reg.group('can_id')), reg.group('name'))

        cad = self._can_network.attributes.definitions[reg.group('attr_name')]
        can_object.attributes.add(CANAttribute(cad, value=self._parse_attribute_value(cad, reg.group('value'))))

    def _parse_val_table_def(self, val_table_def_str):
        """Parses a val table definition string and updates the CANBus

        Args:
            val_table_def_str: String with val table value definition
        Returns:
            Dict representing the val table
        """
        value_dict = {}
        parts = re.split('\s+', val_table_def_str)
        for i in range(0, len(parts), 2):
            value_dict[int(parts[i])] = parts[i+1].replace('"', '')

        return value_dict

    def _parse_val_table(self, val_table_str):
        """Parses a val table string and updates the CANBus

        Args:
            val_table_str: String with val table definition
        """
        pattern = 'VAL_TABLE_\s+(?P<name>\S+)\s+(?P<val_table_def>.+)\s*;'
        reg = re.search(pattern, val_table_str)
        value_dict = self._parse_val_table_def(reg.group('val_table_def'))
        self._can_network.add_value_dict(reg.group('name'), value_dict)

    def _parse_signal_value_dict(self, sig_val_dict_str):
        """Parses a val string and updates the CANBus

        Args:
            sig_val_dict_str: String with val definition
        """
        pattern = 'VAL_\s+(?P<can_id>\d+)\s+(?P<signal_name>\S+)\s+(?P<val_table_def>.+)\s*;'
        reg = re.search(pattern, sig_val_dict_str)

        if re.search('\s+', reg.group('val_table_def')):
            value_dict = self._parse_val_table_def(reg.group('val_table_def'))
        else:
            value_dict = self._can_network.value_dicts[reg.group('val_table_def')]

        self._can_network.get_signal(int(reg.group('can_id')), reg.group('signal_name')).value_dict = value_dict


__author__ = "Stefan Hölzl"


class CANAttribute(object):
    def __init__(self, definition, value=None):
        """Initializes the can attribute

        Args:
            definition: CANAttributeDefinitions-object wich defines the attribute
            value:      Attribute value (default: None)
        """
        self.definition = definition
        self._value = None
        if value:
            self.value = value

    # Property definitions
    @property
    def name(self):
        return self.definition.name

    @property
    def value(self):
        """Gets the attribute value

        Returns:
            Attribute value, if None then the default set by the attribute definition
        """
        if self._value:
            return self._value
        return self.definition.default

    @value.setter
    def value(self, value):
        """Sets the attribute value. Calls the check_value()-methode of the definition to check if the attribute is valid

        Args:
            value: new attribute value
        Raises:
            AttributeError: If the value is not valid
        """
        if self.definition.check_value(value):
            self._value = value
        else:
            raise AttributeError('Attribute value not allowed')


class CANAttributeDefinitionsContainer(object):
    def __init__(self):
        self._attribute_definitions = {}

    # Method definitions
    def add_attribute_definition(self, definition):
        """Adds a new attribute definition

        Args:
            can_obj_type: type of the can object this attribute belongs to
            definition:   attribute definition to add
        """
        self[definition.obj_type][definition.name] = definition

    # Protocol definitions
    def __getitem__(self, item):
        if not item in self:
            self._attribute_definitions[item] = {}
        return self._attribute_definitions[item]

    def __contains__(self, item):
        if not item in self._attribute_definitions:
            return False
        return True


class CANAttributeDefinition(object):
    def __init__(self, name, can_obj_type):
        self.name = name
        self.obj_type = can_obj_type
        self.default = None

    def check_value(self, value):
        return True

class CANStringAttributeDefinition(CANAttributeDefinition):
    def check_value(self, value):
        try:
            str(value)
        except:
            return False
        return True


class CANEnumAttributeDefinition(CANAttributeDefinition):
    def __init__(self, name, can_obj_type, values):
        super().__init__(name, can_obj_type)
        self.values = values

    def check_value(self, value):
        if 0 <= value < len(self.values):
            return True
        return False


class CANFloatAttributeDefinition(CANAttributeDefinition):
    def __init__(self, name, can_obj_type, value_min, value_max):
        super().__init__(name, can_obj_type)
        self.value_min = value_min
        self.value_max = value_max

    def check_value(self, value):
        try:
            float(value)
        except:
            return False
        if self.value_min <= value <= self.value_max:
            return True
        return False


class CANIntAttributeDefinition(CANFloatAttributeDefinition):
    def check_value(self, value):
        if not super().check_value(value):
            return False
        try:
            int(value)
        except:
            return False
        return True
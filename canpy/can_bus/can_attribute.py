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
            self._value = self.definition.cast(value)
        else:
            raise AttributeError('Attribute value not allowed')


class CANAttributeDefinition(object):
    def __init__(self, name, can_obj_type):
        self.name = name
        self.obj_type = can_obj_type
        self._default = None

    @property
    def default(self):
        return self._default

    @default.setter
    def default(self, value):
        if self.check_value(value):
            self._default = self.cast(value)

    def check_value(self, value):
        return True

    def cast(self, value):
        return value

class CANStringAttributeDefinition(CANAttributeDefinition):
    def check_value(self, value):
        try:
            self.cast(value)
        except:
            return False
        return True

    def cast(self, value):
        return str(value)


class CANEnumAttributeDefinition(CANAttributeDefinition):
    def __init__(self, name, can_obj_type, values):
        super().__init__(name, can_obj_type)
        self.values = values

    def check_value(self, value):
        try:
            value = self.cast(value)
        except:
            return False
        if value in self.values:
            return True

    def cast(self, value):
        value = int(value)
        if value < 0:
            raise AttributeError('Negative enum index not allowed')
        return self.values[value]


class CANFloatAttributeDefinition(CANAttributeDefinition):
    def __init__(self, name, can_obj_type, value_min, value_max):
        super().__init__(name, can_obj_type)
        self.value_min = value_min
        self.value_max = value_max

    def check_value(self, value):
        try:
            value = self.cast(value)
        except:
            return False
        if self.value_min <= value <= self.value_max:
            return True
        return False

    def cast(self, value):
        return float(value)


class CANIntAttributeDefinition(CANFloatAttributeDefinition):
    def cast(self, value):
        return int(str(value))
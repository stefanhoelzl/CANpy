__author__ = "Stefan Hölzl"
__all__ = ['CANAttributesContainer', 'CANAttribute', 'CANStringAttributeDefinition', 'CANIntAttributeDefinition',
           'CANFloatAttributeDefinition', 'CANEnumAttributeDefinition']


class CANAttributesContainer(object):
    def __init__(self, can_object):
        self._can_object = can_object
        self._attributes = {}
        self._definitions = {}

    # Property definitions
    @property
    def definitions(self):
        return self._definitions

    # Methods definitions
    def _check_attribute_for_default_value(self, attribute_name, object_to_check=None):
        if not object_to_check:
            object_to_check = self._can_object
        if (attribute_name in object_to_check.attributes.definitions
            and object_to_check.attributes.definitions[attribute_name].obj_type == type(self._can_object)
            and object_to_check.attributes.definitions[attribute_name].default):
            default = CANAttribute(object_to_check.attributes.definitions[attribute_name],
                                   value=object_to_check.attributes.definitions[attribute_name].default)
            return default
        if object_to_check.parent:
            return self._check_attribute_for_default_value(attribute_name, object_to_check.parent)
        raise KeyError('No default definition for this attribute')

    def add(self, attribute):
        self._attributes[attribute.name] = attribute

    def add_definition(self, definition):
        """Adds a new attribute definition to the can network

        Args:
            definition: attribute definitin to add
        """
        self._definitions[definition.name] = definition

    # Protocol definitions
    def __len__(self):
        return len(self._attributes)

    def __getitem__(self, item):
        lookup_chain = [lambda: self._attributes[item],
                        lambda: self._check_attribute_for_default_value(item),
                       ]
        for look_up_item in lookup_chain:
            try:
                return look_up_item()
            except:
                pass
        raise KeyError('No attribute available')

    def __contains__(self, item):
        try:
            self[item]
            return True
        except:
            return False

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
    def __init__(self, name, can_obj_type, default=None):
        self.name = name
        self.obj_type = can_obj_type
        self.default = default

    @property
    def default(self):
        return self._default

    @default.setter
    def default(self, value):
        if self.check_value(value):
            self._default = self.cast(value)
        else:
            self._default = None

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
    def __init__(self, name, can_obj_type, values, default=None):
        self.values = values
        super().__init__(name, can_obj_type, default)

    def check_value(self, value):
        try:
            value_str = self.cast(value)
        except:
            return False
        if value_str in self.values:
            return True

    def cast(self, value):
        try:
            value = int(value)
            if value < 0:
                raise IndexError('Negative enum index not allowed')
            return self.values[value]
        except ValueError:
            value = str(value)
            if value in self.values:
                return value
            raise AttributeError('Value not in enum')


class CANFloatAttributeDefinition(CANAttributeDefinition):
    def __init__(self, name, can_obj_type, value_min, value_max, default=None):
        self.value_min = value_min
        self.value_max = value_max
        super().__init__(name, can_obj_type, default)

    def check_value(self, value):
        try:
            value = self.cast(value)
        except:
            return False
        if self.value_min <= value <= self.value_max or self.value_min == 0 == self.value_max:
            return True
        return False

    def cast(self, value):
        return float(value)


class CANIntAttributeDefinition(CANFloatAttributeDefinition):
    def cast(self, value):
        return int(str(value))
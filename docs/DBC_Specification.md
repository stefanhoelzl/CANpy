# Format description
`<...>`: Required field  
`[...]`: Optional field  
`  |  `: Or (eg. <A|B>)  

# Keywords
## Version
Version identifier of the DBC file.  
Format: `VERSION "<VersionIdentifier>"`  

## BS_
Bus configuration.  
Format:: `BS_: <Speed>`  
Speed in kbit/s  

## BU_
List of all CAN-Nodes, seperated by whitespaces.  

## BO_
Message definition.  
Format: `BO_ <CAN-ID> <MessageName>: <MessageLength> <SendingNode>`  
MessageLength in bytes.  

## SG_
Signal definition.  
Format: `SG_ <SignalName> [M|m<MultiplexerIdentifier>] : <StartBit>|<Length>@<Endianness><Signed> (<Factor>,<Offset>) [<Min>|<Max>] "[Unit]" [ReceivingNodes]`  
Length in bits.  
Signed: + = unsigned; - = signed  
Endianness: 1 = little-endian, Intel; 0 = big-endian, Motorola  
M: If M than this signals contains a multiplexer identifier.  
MultiplexerIdentifier: Signal definition is only used if the value of the multiplexer signal equals to this value.  

## CM_
Description field.  
Format: `CM_ [<BU_|BO_|SG_> [CAN-ID] [SignalName]] "<DescriptionText>";`  

## BA_DEF_
Attribute definition.  
Format: `BA_DEF_ [BU_|BO_|SG_] "<AttributeName>" <DataType> [Config];`  

DataType | Description         | Config format
---------|---------------------|----------------
INT      | integer             | `<min> <max>`
FLOAT    | floating point      | `<min> <max>`
STRING   | string              | 
ENUM     | enumeration         | `"<Value0>","<Value1>"...`

## BA_DEF_DEF_
Attribute default value  
Format: `BA_DEF_DEF_ "<AttributeName>" ["]<DefaultValue>["];`

## BA_
Attribute-  
Format: `BA_ "<AttributeName>" [BU_|BO_|SG_] [Node|CAN-ID] [SignalName] <AttributeValue>;`

## VAL_
Value definitions for signals.  
Format: `VAL_ <CAN-ID> <SignalsName> <ValTableName|ValTableDefinition>;`

## VAL_TABLE_
Value table definition for signals.  
Format: `VAL_TABLE_ <ValueTableName> <ValueTableDefinition>;`  
ValueTableDefinition: List of `IntValue "StringValue"` Pairs, seperated by whitespaces

# Sources
http://pisnoop.s3.amazonaws.com/snoop_help_dbc.htm  
http://www.racelogic.co.uk/_downloads/vbox/Application_Notes/CAN%20Format%20for%20VBOXII%20and%20PRO%20v4.pdf  
https://hackage.haskell.org/package/ecu-0.0.8/src/src/j1939_utf8.dbc
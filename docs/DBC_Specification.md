# Keywords
## Version
Version identifier of the DBC file.
Format: `VERSION "<VersionIdentifier>"`

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

# Sources
http://pisnoop.s3.amazonaws.com/snoop_help_dbc.htm
http://www.racelogic.co.uk/_downloads/vbox/Application_Notes/CAN%20Format%20for%20VBOXII%20and%20PRO%20v4.pdf
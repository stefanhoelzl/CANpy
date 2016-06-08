# CANpy

## Goal
The goal of this project is to provide a generic interface to an CAN-Bus (Nodes, Message, Signals, Attributes) based on an Description file (e.g. [DBC-File](docs/DBC_Specification.md)).
You only have to interact on a high level with this generic interface and the framework does the rest for you (sending and receiving messages, data conversion etc.).

## Status
### Parser
The DBC parser currently implements this specification [DBC specification](docs/DBC_Specification.md)

### CAN-Object abstraction
* CAN-Bus
* Nodes
* Messages
* Signals
* Attributes
* Attribute definitions
* Value tables

### Communication Handling
Working on getting the framework running under [micropython](https://github.com/micropython/micropython) using [usched](https://github.com/peterhinch/Micropython-scheduler).

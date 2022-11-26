# Stratospheric Weather Balloon Customizable Ground Station

## Project Introduction

This repository contains the ground-station project developed throughout 
the M2-TSI weather balloon missions for the March 2022 launch session. 
The communication between both balloons and the ground is made using the LoRa 
modulation technology at 433 MHz (frequency range available for amateur LoRa 
radio communication in Europe).

This ground station was first designed to be connected via serial to a TTGO LoRa ESP32 board 
serving as our receiver for data transmitted by two stratospheric weather balloons. The data 
is then parsed and stored in CSV files storage.

## Recent Changes

The most recent version of this ground station possesses a new parser imported from the 
**[ECOM Repository](https://gitlab.com/team-aster/software/ecom)** from the ASTER project. 
The main goal is to adapt our system to the use of the 
**[UnoSat Platform](https://github.com/Abestanis/UnoSat)** developed to improve two-way communication.

The GUI Layout was revamped as to allow full customization of the data displays and packets' formatting. 
Different tabs allow the user to change pretty much anything and as the project goes on, more features 
will be added. As of now, a full map GPS rendition and an ascent-descent simulator are next on the to-do list.


# Ground Station for a two Weather balloons mission :

This repository contains an installation of a ground-station used during the M2-TSI weather balloon missions of the scholar year of 2021/2022. The communication between both balloons and the ground is made using the LoRa modulation technology at 433 MHz (frequency range available for amateur LoRa radio communication in Europe) using the TTGO LoRa ESP32 OLED V2 board codable using the Arduino IDE Software.

The ground station is composed of the TTGO LoRa receiving the data transmitted by both balloons, connected by Serial Port to the user's computer. The data is then received and stored on the PC by a Python file monitoring the Serial port. Finally, a graphical user interface uses the data to display real-time interactive plots to the user.

Depending on the categories of data provided by the on-board sensors, the GUI needs to adapt itself by being able to monitor multiple values for both balloons at the same time.

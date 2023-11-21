<a name="readme-top"></a>
<img src="https://raw.githubusercontent.com/EnguerranVidal/PyStrato/main/sources/icons/SplashScreen.png" alt="Your Image Alt Text" style="width: 100%; height: auto;"/>

___

 [![HitCount](https://hits.dwyl.com/EnguerranVidal/PyStrato.svg?style=flat)](http://hits.dwyl.com/EnguerranVidal/PyStrato) [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT) [![GitHub watchers](https://badgen.net/github/watchers/EnguerranVidal/PyStrato/)](https://GitHub.com/EnguerranVidal/PyStrato/watchers/) [![GitHub stars](https://badgen.net/github/stars/EnguerranVidal/PyStrato)](https://GitHub.com/EnguerranVidal/PyStrato/stargazers/) [![GitHub commits](https://badgen.net/github/commits/EnguerranVidal/PyStrato)](https://github.com/EnguerranVidal/PyStrato/) [![GitHub branches](https://badgen.net/github/branches/EnguerranVidal/PyStrato)](https://github.com/EnguerranVidal/PyStrato/)
 [![made-with-python](https://img.shields.io/badge/Made%20with-Python-1f425f.svg)](https://www.python.org/)
## Introduction

<div style="text-align: justify;">

This repository contains the PyStrato tool which started out as 
a student project for second year Masters TSI of 2021/2022 in Toulouse, France. Its curriculum features a pair of stratospheric balloons that are designed, constructed and launched around February/March with the help of the CNES (French Space Agency). 
The communication between both balloons and the ground was achieved using the LoRa IoT
modulation technology at a frequency of 433 MHz (range available for amateur LoRa 
radio communication in Europe).

</div>



## Project Changes

<div style="text-align: justify;">

At first, this Python project relied on the use of TTGO Lora ESP32 as emitting and receiving Arduino boards, communicating in serial to the ground station that parsed the data (sent as regular ASCII bytes), stored it in CSV files and displayed it live through pre-programmed plots.
The goal of this tool going forwards was to increase its user-customization potential. One of the students of the 2021/2022 M2-TSI worked on the use of a LoRa Shield set on a regular Arduino Uno and introduced a standardized communication database system instead of just sending ASCII bytes. 
This started the use of the **[ECOM Repository](https://gitlab.com/team-aster/software/ecom)** from the ASTER project and set our main goal to adapt our platform to the use of the **[UnoSat Platform](https://github.com/Abestanis/UnoSat)** developed to improve two-way communication.

The GUI Layout was then revamped

</div>






<p align="right">(<a href="#readme-top">back to top</a>)</p>



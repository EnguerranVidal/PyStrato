<a name="readme-top"></a>
<img src="https://raw.githubusercontent.com/EnguerranVidal/PyStrato/main/sources/icons/SplashScreen.png" alt="Your Image Alt Text" style="width: 100%; height: auto;"/>

___

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT) [![GitHub watchers](https://badgen.net/github/watchers/EnguerranVidal/PyStrato/)](https://GitHub.com/EnguerranVidal/PyStrato/watchers/) [![GitHub stars](https://badgen.net/github/stars/EnguerranVidal/PyStrato)](https://GitHub.com/EnguerranVidal/PyStrato/stargazers/) [![GitHub commits](https://badgen.net/github/commits/EnguerranVidal/PyStrato)](https://github.com/EnguerranVidal/PyStrato/) [![GitHub branches](https://badgen.net/github/branches/EnguerranVidal/PyStrato)](https://github.com/EnguerranVidal/PyStrato/) ![GitHub repo size](https://img.shields.io/github/repo-size/EnguerranVidal/PyStrato) ![GitHub last commit](https://img.shields.io/github/last-commit/EnguerranVidal/PyStrato)
  [![wakatime](https://wakatime.com/badge/github/EnguerranVidal/PyStrato.svg)](https://wakatime.com/badge/github/EnguerranVidal/PyStrato) [![made-with-python](https://img.shields.io/badge/Made%20with-Python-1f425f.svg)](https://www.python.org/)


## ABOUT THE PROJECT
___
<div style="text-align: justify;">

This repository contains the PyStrato GUI software. Starting up as a part of the stratospheric weather balloon 
missions from the **[M2 TSI](http://m2tsi.eu)** from France, this tool has become a fully customizable 
balloon ground station using the **[ECOM](https://gitlab.com/team-aster/software/ecom)** software 
from the ASTER project. This ground station coded in PyQt5 retrieves telemetry data from a serial connection to a Arduino 
receptor. The data is then parsed and can update real-time graphs and tables. A weather panel has also recently been
added to aid the user's mission prediction.

Distributed under the MIT License. See **[LICENSE](https://github.com/EnguerranVidal/PyStrato/blob/main/LICENSE)** 
for more information.

</div>



## GETTING STARTED
___
### INSTALLATION
1. Cloning the Github Repository
```
git clone https://github.com/EnguerranVidal/PyStrato.git
```
2. Going in the Repository Directory
```
cd PyStrato
```
3. Creating PyEnv Environment
```
pyenv virtualenv 3.9 pystrato
pyenv local pystrato
```
4. Installing PyStrato Requirements
```
pip install -r requirements.txt
```

### STARTING GUI
```
python main.py
```




## FUTURE ROADMAP
___
- [x] Revamping Ecom Database Editing
- [ ] Add Working Display Layout Saving
- [ ] Revamping Displays
- [ ] Add Balloon Trajectory Model
- [ ] Add 3D Plots
- [ ] Add Telecommand sending



<p align="right">(<a href="#readme-top">back to top</a>)</p>



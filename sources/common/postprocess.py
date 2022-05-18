import os
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
import numpy as np


def verify_message_data(string, sign):
    if not string[sign:].replace('.', '', 1).isdigit():
        return False
    else:
        return True


def extract_data(start, finish, header):
    h_len = len(header)
    # importing and sing mission
    with open("data.txt", "r") as file:
        lines = file.readlines()
    mission = lines[start:finish - 1]
    content = {"T in": [], "T ext": [], "P": [], "H": [], "CO": [], "O3": [],
               "CO2": [], "HCOH": [], "CH4": [], "NH3": [], "NO2": [], "H2": [], "C3H8": [],
               "C4H10": [], "C2H6OH": [], "p25": [], "p10": [], "Light": []}
    n = len(mission)
    for i in range(n):
        mission[i] = mission[i][h_len:]
        content["T in"].append(int(mission[i][8:13]) / 10 ** 2)
        content["T ext"].append(int(mission[i][13:18]) / 10 ** 2)
        content["P"].append(int(mission[i][18:22]) / 10 ** 3)
        content["H"].append(int(mission[i][22:25]) / 10 ** 1)
        content["CO"].append(int(mission[i][25:29]) / 10 ** 3)
        content["O3"].append(int(mission[i][29:33]) / 10 ** 1)
        content["CO2"].append(int(mission[i][33:37]) / 10 ** 1)
        content["HCOH"].append(int(mission[i][37:41]) / 10 ** 3)
        content["CH4"].append(int(mission[i][41:46]) / 10 ** 1)
        content["NH3"].append(int(mission[i][46:50]) / 10 ** 1)
        content["NO2"].append(int(mission[i][50:53]) / 10 ** 2)
        content["H2"].append(int(mission[i][53:57]) / 10 ** 1)
        content["C3H8"].append(int(mission[i][57:62]) / 10 ** 0)
        content["C4H10"].append(int(mission[i][62:67]) / 10 ** 1)
        content["C2H6OH"].append(int(mission[i][67:71]) / 10 ** 1)
        content["p25"].append(int(mission[i][71:75]) / 10 ** 1)
        content["p10"].append(int(mission[i][75:79]) / 10 ** 1)
        content["Light"].append(int(mission[i][79:84]) / 10 ** 0)
    return content


if __name__ == '__main__':
    data = extract_data(12946, 16079, "F4KLD-1:")
    burst = 15185 - 12946
    n = len(data["T in"])
    x = np.arange(n)
    fig = plt.figure(figsize=(10, 5))
    gs = GridSpec(nrows=3, ncols=3)
    # Temperatures
    plt.title("Temperatures")
    plt.plot(x, data["T in"], label="Internal")
    plt.plot(x, data["T ext"], label="External")
    plt.axvline(x=burst, color='red', linestyle='--')
    plt.xlabel("Time")
    plt.ylabel("°C")
    plt.legend()
    plt.grid()
    plt.show()
    # Pressure
    plt.title("Pressure")
    plt.plot(x, np.array(data["P"]) * 1000)
    plt.axvline(x=burst, color='red', linestyle='--')
    plt.gca().invert_yaxis()
    plt.xlabel("Time")
    plt.ylabel("mbar")
    plt.show()
    # Light Level
    plt.title("Light Level")
    plt.plot(x, data["Light"])
    plt.axvline(x=burst, color='red', linestyle='--')
    plt.xlabel("Time")
    plt.ylabel("Lumens")
    plt.show()
    # Humidity
    plt.title("Humidity")
    plt.plot(x, data["H"])
    plt.xlabel("Time")
    plt.axvline(x=burst, color='red', linestyle='--')
    plt.ylabel("%")
    plt.show()
    # Particles
    plt.title("Particles")
    plt.axvline(x=burst, color='red', linestyle='--')
    plt.plot(x, data["p25"], label="p25")
    plt.plot(x, data["p10"], label="p10")
    plt.xlabel("Time")
    plt.ylabel("ppm")
    plt.legend()
    plt.grid()
    plt.show()

    plt.title("Carbon Monoxide")
    plt.axvline(x=burst, color='red', linestyle='--')
    plt.plot(x, data["CO"], label="CO")
    plt.xlabel("Time")
    plt.ylabel("ppm")
    plt.legend()
    plt.grid()
    plt.show()

    plt.title("Methane")
    plt.axvline(x=burst, color='red', linestyle='--')
    plt.plot(x, data["CH4"])
    plt.xlabel("Time")
    plt.ylabel("ppm")
    plt.grid()
    plt.show()

    plt.title("Defective Gas Sensors")
    plt.axvline(x=burst, color='red', linestyle='--')
    plt.plot(x, np.array(data["CO2"]) * 10, label="CO2")
    plt.plot(x, np.array(data["O3"]), label="O3")
    plt.plot(x, np.array(data["NH3"]), label="NH3")
    plt.plot(x, np.array(data["C2H6OH"]), label="C2H6OH")
    plt.plot(x, np.array(data["H2"]), label="H2")
    plt.xlabel("Time")
    plt.ylabel("ppm")
    plt.legend()
    plt.grid()
    plt.show()

    plt.title("Formaldehyde")
    plt.axvline(x=burst, color='red', linestyle='--')
    plt.plot(x, np.array(data["HCOH"]))
    plt.xlabel("Time")
    plt.ylabel("ppm")
    plt.grid()
    plt.show()

    plt.title("Hydrocarbons")
    plt.axvline(x=burst, color='red', linestyle='--')
    plt.plot(x, np.array(data["C3H8"]), label="C3H8")
    plt.plot(x, np.array(data["C4H10"]), label="C4H10")
    plt.xlabel("Time")
    plt.ylabel("ppm")
    plt.legend()
    plt.grid()
    plt.show()


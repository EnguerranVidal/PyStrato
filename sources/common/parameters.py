def load_settings(path):
    parameters = {}
    with open(path, "r") as file:
        lines = file.readlines()
    for i in range(len(lines)):
        line = lines[i].split('=')
        if line[0] == "AVAILABLE_BAUDS" or line[0] == "FORMAT_FILES" or line[0] == "SAVE_FILES":
            bauds = line[1].split(',')
            for j in range(len(bauds)):
                bauds[j] = bauds[j].rstrip("\n")
            parameters[line[0]] = bauds
        elif line[0] == "RSSI" or line[0] == "AUTOSCROLL" or line[0] == "AUTOSCALE":
            parameters[line[0]] = bool(int(line[1].rstrip("\n")))
        else:
            parameters[line[0]] = line[1].rstrip("\n")
    return parameters


def save_settings(parameters, path):
    with open(path, "r") as file:
        lines = file.readlines()
    with open(path, "w") as file:
        for i in range(len(lines)):
            line = lines[i].split('=')
            if line[0] == "AVAILABLE_BAUDS" or line[0] == "FORMAT_FILES" or line[0] == "SAVE_FILES":
                file.write(lines[i])
            elif line[0] == "RSSI" or line[0] == "AUTOSCROLL" or line[0] == "AUTOSCALE":
                file.write(line[0] + '=' + str(int(parameters[line[0]])) + '\n')
            else:
                file.write(line[0] + '=' + str(parameters[line[0]]) + '\n')

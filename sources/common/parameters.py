def load(path):
    parameters = {}
    with open(path, "r") as file:
        lines = file.readlines()
    for i in range(len(lines)):
        line = lines[i].split(';')
        if line[0] == "available_bauds" or line[0] == "format_files" or line[0] == "save_files":
            bauds = line[1].split(',')
            for j in range(len(bauds)):
                bauds[j] = bauds[j].rstrip("\n")
            parameters[line[0]] = bauds
        elif line[0] == "rssi" or line[0] == "autoscroll" or line[0] == "autoscale":
            parameters[line[0]] = bool(int(line[1].rstrip("\n")))
        else:
            parameters[line[0]] = line[1].rstrip("\n")


def save(parameters, path):
    with open(path, "r") as file:
        lines = file.readlines()
    with open(path, "w") as file:
        for i in range(len(lines)):
            line = lines[i].split(';')
            if line[0] == "available_bauds" or line[0] == "format_files" or line[0] == "save_files":
                file.write(lines[i])
            elif line[0] == "rssi" or line[0] == "autoscroll" or line[0] == "autoscale":
                file.write(line[0] + ';' + str(int(parameters[line[0]])) + '\n')
            else:
                file.write(line[0] + ';' + str(parameters[line[0]]) + '\n')

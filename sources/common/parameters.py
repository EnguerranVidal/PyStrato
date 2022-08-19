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


def save_format(packetFormat, path):
    step = 0
    lines = []
    if packetFormat['ID'] is not None:
        lines.append('ID:' + packetFormat['ID'] + ':' + str(0) + '\n')
        step += len(packetFormat['ID'])
    elif packetFormat['PIN'] is not None:
        lines.append('PIN:' + packetFormat['PIN'] + ':' + str(step) + '\n')
        step += len(packetFormat['PIN'])
    elif packetFormat['CLOCK'] is not None:
        lines.append('CLOCK:' + packetFormat['CLOCK'] + ':' + str(step) + '\n')
        step += len(packetFormat['CLOCK'])
    names = list(packetFormat['DATA'].keys())
    for i in range(len(names)):
        data = packetFormat[names[i]]
        addendum = data['SIGN'] + ':' + data['TOTAL'] + ':' + data['FLOAT'] + ':' + data['UNIT']
        lines.append('VALUE:' + names[i] + ':' + addendum + ':' + str(step) + '\n')
        step += int(data['SIGN']) + int(data['SIGN'])
    with open(path, 'r') as file:
        for i in lines:
            file.write(i)


def load_format(path):
    # Accessing Lines
    with open(path, 'r') as file:
        lines = file.readlines()
    ID, PIN, CLOCK, FILE, DATA = None, None, None, '', {}
    # Getting Format Name
    firstLine = lines[0].split(':')
    name = firstLine[1]
    for i in range(1, len(lines)):
        line = lines[i].split(':')
        if line[0] == 'VALUE':
            DATA[line[1]] = {'SIGN': line[2], 'TOTAL': line[3], 'FLOAT': line[4], 'UNIT': line[5]}
        elif line[0] == 'ID':
            ID = line[1]
        elif line[0] == 'PIN':
            PIN = line[1]
        elif line[0] == 'FILE':
            FILE = line[1]
        elif line[0] == 'CLOCK':
            CLOCK = line[1]
    return name, {'ID': ID, 'PIN': PIN, 'CLOCK': CLOCK, 'PATH': path, 'FILE': FILE, 'DATA': DATA}

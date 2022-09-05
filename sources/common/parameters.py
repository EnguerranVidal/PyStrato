import os


def load_settings(path):
    parameters = {}
    with open(path, "r") as file:
        lines = file.readlines()
    for i in range(len(lines)):
        line = lines[i].split('=')
        if line[0] == "AVAILABLE_BAUDS" or line[0] == "FORMAT_FILES":
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
            setting = line[0]
            if setting == "AVAILABLE_BAUDS" or setting == "FORMAT_FILES":
                file.write(setting + '=' + ','.join(parameters[setting]) + '\n')
            elif setting == "RSSI" or setting == "AUTOSCROLL" or setting == "AUTOSCALE":
                file.write(setting + '=' + str(int(parameters[setting])) + '\n')
            else:
                file.write(setting + '=' + str(parameters[setting]) + '\n')


def save_format(packetFormat, path):
    step = 0
    lines = ['NAME' + ':' + packetFormat['NAME'] + '\n']
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
        step += int(data['SIGN']) + int(data['TOTAL'])
    lines[-1].rstrip('\n')
    with open(path, 'r') as file:
        for i in lines:
            file.write(i)


def load_format(path):
    # Accessing Lines
    with open(path, 'r') as file:
        lines = file.readlines()
    ID, PIN, CLOCK, FILE, DATA = None, None, None, '', {}
    # Getting Format Name
    lines[0] = lines[0].rstrip('\n')
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


def check_format(path):
    keywords = ['NAME', 'ID', 'PIN', 'CLOCK', 'FILE', 'VALUE']
    filename, file_extension = os.path.splitext(path)
    namePresent, filePresent = False, False
    if file_extension == '.config':
        with open(path, 'r') as file:
            lines = file.readlines()
        for i in range(len(lines)):
            line = lines[i].split(':')
            if len(lines[i]) != 0 and line[0] not in keywords:
                return False
            if line[0] == 'NAME':
                namePresent = True
            if line[0] == 'FILE':
                filePresent = True
        if filePresent and namePresent:
            return True
        else:
            return False
    else:
        return False

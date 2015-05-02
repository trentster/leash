import os

def which(program):
    def is_exe(fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            path = path.strip('"')
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file

    return None

def network_self():
    return _read_config_set('self')

def network_host():
    return _read_config_set('host')

def _read_config_set(config_type):

    ip = ""
    subnet = ""
    gateway = ""

    f = open('config/' + config_type + '.ip', 'r')
    ip = f.read()
    f.close()

    f = open('config/' + config_type + '.netmask', 'r')
    netmask = f.read()
    f.close()

    f = open('config/' + config_type + '.gateway', 'r')
    gateway = f.read()
    f.close()

    return {'ip': ip.strip(), 'netmask': netmask.strip(), 'gateway': gateway.strip()}

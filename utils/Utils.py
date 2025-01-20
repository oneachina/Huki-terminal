import os


def in_path(path, program_name):
    path = os.environ.get('PATH')
    directories = path.split(os.pathsep)

    for directory in directories:
        program_path = os.path.join(directory, program_name)
        if os.path.isfile(program_path) or os.path.isfile(program_path + '.exe') or os.path.exists(
                path + program_path):
            return True
    return False

class Utils:
    def __init__(self):
        pass

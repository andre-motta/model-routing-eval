import configparser


def load_config(path="config.ini"):
    cp = configparser.ConfigParser()
    cp.read(path)
    return {section: dict(cp[section]) for section in cp.sections()}

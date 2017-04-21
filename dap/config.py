import yaml

with open('config.yml', 'r') as ymlfile: # TODO: use fixed path?
    CONF = yaml.load(ymlfile)


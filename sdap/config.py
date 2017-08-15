import yaml

with open('/etc/sdap/config.yml', 'r') as ymlfile:
    CONF = yaml.load(ymlfile)

def shared_db_name():
    return CONF['db']['shared_db']

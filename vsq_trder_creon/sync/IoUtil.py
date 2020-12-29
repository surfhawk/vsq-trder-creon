import yaml
import os
import socket

class AttributeDict(dict):
    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__

class AttrDictYaml(object):
    def __init__(self, attr):
        self._attr = attr
    def __getattr__(self, attr):
        if attr == '_attr':
            return None
        elif not attr in self._attr.keys():
            print('attr', attr)
            raise KeyError
        return self._attr[attr]
    def __getitem__(self, item):
        if item in self._attr.keys():
            return self._attr[item]

    def __getstate__(self):
        return self.__dict__
    def keys(self):
        return self._attr.keys()

def parse_yml_as_attrdict(yaml_file):
    with open(os.path.abspath(yaml_file)) as yaml_stream:
        def construct_map(self, node):
            # WARNING: This is copy/pasted without understanding!
            d = {}
            yield AttrDictYaml(d)
            d.update(self.construct_mapping(node))
        # https://stackoverflow.com/questions/11049117/how-to-load-a-pyyaml-file-and-access-it-using-attributes-instead-of-using-the-di
        yaml.add_constructor('tag:yaml.org,2002:map', construct_map)

        return yaml.load(yaml_stream, Loader=yaml.FullLoader)

def parse_yml_as_dict(yaml_file):
    with open(os.path.abspath(yaml_file)) as yaml_stream:
        return yaml.load(yaml_stream, Loader=yaml.FullLoader)

def is_port_free(port, ip_addr='127.0.0.1'):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return not s.connect_ex((ip_addr, port)) == 0
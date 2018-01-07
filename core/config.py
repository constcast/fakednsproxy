import yaml
import pprint

class DNSForwardPolicies:
    def __init__(self):
        self.valid_policies = ['forward',
                               'nxdomain',
                               'default_value']

    def get_valid_policies(self):
        return self.valid_policies

    def is_valid_policy(self, policy):
        if policy in self.valid_policies:
            return True
        return False

class ConfigParser:
    def __init__(self, config_obj=dict()):
        self.config = config_obj

    def parse_config(self, filename):
        with open(filename, 'r') as f:
            self.config = yaml.load(f)
        self.validate_config()

    def __getitem__(self, key):
        return self.config[key]

    def __setitem__(self, key, value):
        self.config[key] = value

    def __contains__(self, key):
        return key in self.config

    def print(self):
        printer = pprint.PrettyPrinter(indent=4)
        printer.pprint(self.config)

    def validate_config(self):
        if not 'dns_server' in self.config:
            raise RuntimeError("ERROR: Every config must contain a dns_server")
        if type(self.config['dns_server']) != dict:
            raise RuntimeError("ERROR: dns_server in configuration must be a dict")
        if not 'ip' in self.config['dns_server'] or not 'port' in self.config['dns_server']:
            raise RuntimeError("ERROR: dns_server in configuration must contain an ip and a port")
        if not 'listening_info' in self.config:
            raise RuntimeError("ERROR: Every config must contain a listening_info")
        if not 'ip' in self.config['listening_info'] or not 'port' in self.config['listening_info']:
            raise RuntimeError("ERROR: dns_server in configuration must contain an ip and a port")
        if not 'default_dns_policy' in self.config:
            raise RuntimeError("ERROR: Every config must contains a default_dns_policy")
        forward_policies = DNSForwardPolicies()
        if not DNSForwardPolicies().is_valid_policy(self.config['default_dns_policy']):
            raise RuntimeError("ERROR: default_dns_policy in config must be " \
                    "one of {}".format(','.join(forward_policies.get_valid_policies())))
        if self.config['default_dns_policy'] == 'default_value':
            if not 'default_dns_value' in self.config:
                raise RuntimeError('ERROR: "default_dns_value" required in config'
                                   ' if default_dns_policy is "default_value"') 

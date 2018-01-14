import yaml
import pprint
import socket

from twisted.names import client, dns, error, server


class DNSAnswerConfig:
    def __getitem__(self, key):
        return self.value_dict[key]

    def __setitem__(self, key, value):
        self.value_dict[key] = value

    def __contains__(self, key):
        return key in self.value_dict

    def isValidQueryType(self, query_type):
        if query_type in dns.QUERY_TYPES.values():
            return True
        return False

    def isIPv4Address(self, address):
        try:
            socket.inet_pton(socket.AF_INET, address)
        except Exception as e:
            return False
        return True
       
    def isIPv6Address(self, address):
        try:
            socket.inet_pton(socket.AF_INET6, address)
        except Exception as e:
            return False
        return True
 
    def __init__(self, value):
        self.value_dict = dict()
        policies = DNSForwardPolicies()
        if isinstance(value, str):
            # interpret a string value either as an IPv4 address or
            # an IPv6 address
            if self.isIPv4Address(value):
                self.value_dict['A'] = [ value ]
            elif self.isIPv6Address(value):
                self.value_dict['AAAA'] = [ value ]
            elif policies.is_valid_policy(value):
                self.value_dict['*'] = [ value ]
            else:
                raise RuntimeError("DNSAnswerDict: {} is not a valid IP "
                                   "address".format(value))
        elif isinstance(value, list):
            # a list of IPv4 and IPv6 addresses
            for address in value:
                if self.isIPv4Address(address):
                    self.value_dict.setdefault('A', []).append(address)
                elif self.isIPv6Address(address):
                    self.value_dict.setdefault('AAAA', []).append(address)
                else:
                    raise RuntimeError("DNSAnswerDict: {} is not a valid IP "
                                       "address".format(address))
        elif isinstance(value, dict):
            for qtype in value.keys():
                if not self.isValidQueryType(qtype):
                    raise RuntimeError('DNSAnswerDict: Query type "{}" is not a '
                                      'valid query type.'.format(qtype))
                v = value[qtype]
                if isinstance(v, str):
                    self.value_dict[qtype] = [ v ]
                else:
                    self.value_dict[qtype] = v



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
        self.generate_config_objects()
        self.validate_config()

    def generate_config_objects(self):
        """
        This method takes the dictionary stored in self.config, and replaces
        the plaintext string domain_config, default_value, etc.
        We have this extra indirection in the code, becausue we allow 
        syntatic sugar in the configuration writing:
            - A writer an just specify an IP address or list of IP
              addresses (both V4 and V6) instead of providing a dictionary
              with a list of A and AAAA objects
        """
        if 'default_dns_value' in self.config and \
            not isinstance(self.config['default_dns_value'], DNSAnswerConfig):
                self.config['default_dns_value'] = DNSAnswerConfig(self.config['default_dns_value'])
        if not 'domain_config' in self.config:
            return
        domain_config = dict()
        for domain, value in self.config['domain_config'].items():
            if isinstance(value, DNSAnswerConfig):
                domain_config[domain] = value
            else:
                domain_config[domain] = DNSAnswerConfig(value)
        self.config['domain_config'] = domain_config

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

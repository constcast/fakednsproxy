from twisted.names import client, dns, error, server

import re
import socket

class DNSAnswerConfig:
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
        if isinstance(value, str):
            # interpret a string value either as an IPv4 address or
            # an IPv6 address
            if self.isIPv4Address(value):
                self.value_dict['A'] = value
            elif self.isIPv6Address(value):
                self.value_dict['AAAA'] = value
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
            self.value_dict = value
        

class DNSReplyGenerator:
    def __init__(self, config):
        self.config = config

    def generateAnswerRecord(self, query, value):
        name = query.name.name
        answer = dns.RRHeader(name=name,
                              payload=dns.Record_A(address=value))
        return answer
 
    def generateReply(self, query):
        raise NotImplementedError()

    def getDomainConfigEntry(self, query_name):
        """
        Our matching is simple, we support the * as wildcard for our matching
        of domain names. We match the query_name against our entries in 
        domain_config:
            query_name: a.foobar.com --> *.foobar.com
        """
        if not 'domain_config' in self.config:
            raise RuntimeError("ERROR: No specific domain config in config.")
        domain_config = self.config['domain_config']

        for domain, value in domain_config.items():
            escaped_domain = re.escape(domain)
            # take our * and make them regular expression matching
            regex_domain = escaped_domain.replace('\*', '.*')
            m = re.match(regex_domain, query_name)
            if m:
                return value

        raise RuntimeError("ERROR: Could not find custom_value definition "
                           "for domain '{}' in config".format(query_name))

class NXDomainReply(DNSReplyGenerator):
    def generateReply(self, query):
        return [], [], []

class DefaultValueReply(DNSReplyGenerator):
    def generateReply(self, query):
        if type(self.config['default_dns_value']) == list:
            answers = [self.generateAnswerRecord(query, x) for x in self.config['default_dns_value']]
        else:
            answer = self.generateAnswerRecord(query,
                                               self.config['default_dns_value'])
            answers = [answer]
        return answers, [], []

class CustomValueReply(DNSReplyGenerator):
    def generateReply(self, query):
        name = query.name.name.decode()
        name_config = self.getDomainConfigEntry(name)
        if type(name_config) == list:
            answers = [self.generateAnswerRecord(query, x) for x in name_config]
        else:
            answer = self.generateAnswerRecord(query,
                                               name_config)
            answers = [answer]
        return answers, [], []


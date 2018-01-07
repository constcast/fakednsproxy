from twisted.names import client, dns, error, server

import re

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


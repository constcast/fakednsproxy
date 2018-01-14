from twisted.names import client, dns, error, server

import re

class DNSReplyGenerator:
    def __init__(self, config):
        self.config = config

    def generateAnswerRecords(self, query, domain_config):
        name = query.name.name
        qtype = query.type
        payload = None

        if not qtype in dns.QUERY_TYPES:
            raise RuntimeError("DNSReplyGenerator: received request to generate"
                               " DNS query type {}.".format(qtype))

        qtype_string = dns.QUERY_TYPES[qtype]
        if not qtype_string in domain_config:
            return []

        answers = []
        domain_entry = domain_config[qtype_string]
        
        for value in domain_entry:
            payload = self.generateAnswerRecordPayload(qtype_string,
                                                       value)
            answer = dns.RRHeader(name=name,
                                  type=qtype,
                                  payload=payload)
            answers.append(answer)
        return answers
 
    def generateAnswerRecordPayload(self, qtype_string, record_value):
        payload = None
        if qtype_string == 'A':
            payload = dns.Record_A(address=record_value)
        elif qtype_string == 'AAAA':
            payload = dns.Record_AAAA(address=record_value)
        elif qtype_string == 'MX':
            payload = dns.Record_MX(name=record_value)
        elif qtype_string == 'NS':
            payload = dns.Record_NS(name=record_value)
        elif qtype_string == 'MD':
            raise NotImplementedError()
        elif qtype_string == 'MF':
            raise NotImplementedError()
        elif qtype_string == 'CNAME':
            raise NotImplementedError()
        elif qtype_string == 'SOA':
            raise NotImplementedError()
        elif qtype_string == 'MB':
            raise NotImplementedError()
        elif qtype_string == 'MG':
            raise NotImplementedError()
        elif qtype_string == 'MR':
            raise NotImplementedError()
        elif qtype_string == 'NULL':
            raise NotImplementedError()
        elif qtype_string == 'WKS':
            raise NotImplementedError()
        elif qtype_string == 'PTR':
            raise NotImplementedError()
        elif qtype_string == 'HINFO':
            raise NotImplementedError()
        elif qtype_string == 'MINFO':
            raise NotImplementedError()
        elif qtype_string == 'TXT':
            raise NotImplementedError()
        elif qtype_string == 'RP':
            raise NotImplementedError()
        elif qtype_string == 'AFSDB':
            raise NotImplementedError()
        elif qtype_string == 'SRV':
            raise NotImplementedError()
        elif qtype_string == 'NAPTR':
            raise NotImplementedError()
        elif qtype_string == 'A6':
            raise NotImplementedError()
        elif qtype_string == 'DNAME':
            raise NotImplementedError()
        elif qtype_string == 'OPT':
            raise NotImplementedError()
        elif qtype_string == 'SPF':
            raise NotImplementedError()
        else:
            raise RuntimeError("DNSReplyGenerator: received request to generate"
                               " DNS query type {}.".format(qtype))

        return payload 

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
        answers = self.generateAnswerRecords(query, self.config['default_dns_value'])
        return answers, [], []

class CustomValueReply(DNSReplyGenerator):
    def generateReply(self, query):
        name = query.name.name.decode()
        name_config = self.getDomainConfigEntry(name)
        answers = self.generateAnswerRecords(query, name_config)
        return answers, [], []


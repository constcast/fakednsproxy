from twisted.names import client, dns, error, server

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
        domain_config = self.config['domain_config']
        if not name in domain_config:
            raise RuntimeError("ERROR: Could not find custom_value definition "
                               "for domain '{}' in config".format(name))
        name_config = domain_config[name]
        if type(name_config) == list:
            answers = [self.generateAnswerRecord(query, x) for x in name_config]
        else:
            answer = self.generateAnswerRecord(query,
                                               name_config)
            answers = [answer]
        return answers, [], []


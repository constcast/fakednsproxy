import core.config
import core.dns_reply_generators

from twisted.internet import reactor, defer
from twisted.names import client, dns, error, server

class DNSHandler(object):
    def __init__(self, config):
        self.config = config
        self.resolver = None
        if 'dns_server' in self.config:
            self.resolver = client.Resolver(servers=[
                                              (self.config['dns_server']['ip'],
                                              self.config['dns_server']['port']
                                            )])
 
    def get_action_for_query(self, query):
        if 'domain_config' in self.config:
            domain_configs = self.config['domain_config']
            query_name = str(query.name)
            if query_name in domain_configs.keys():
                if domain_configs[query_name] == 'forward' or \
                    domain_configs[query_name] == 'nxdomain' or \
                    domain_configs[query_name] == 'default_value':
                        return domain_configs[query_name]
                else:
                    return "custom_value"
        return self.config['default_dns_policy'] 

    def _dynamicResponseRequired(self, query):
        """
        This method decides whether any special handling for the DNS query
        is required. The decision is based on the configuration defined by the
        user. 
        If this method returns True, then a special handling will be started
        in method _doDynamicResponse. Otherwise, the query will be sent to the
        configured dns_server in the user configuration file
        """
        action = self.get_action_for_query(query)
        if action in [ 'forward', 'nxdomain', 'default_value', 'custom_value' ]:
            return True

        raise RuntimeError("ERROR: Do not now how to handle this query with"
                " the default policy {}. This is a bug!".format(self.config['default_dns_policy']))

    def _doDynamicResponse(self, query, timeout=None):
        """
        This method creates special responses based on the configuraiton provided
        by the user.
        """ 
        action = self.get_action_for_query(query)
        if action == "forward":
            return self.resolver.query(query, timeout)
        if action == "nxdomain":
            gen = core.dns_reply_generators.NXDomainReply(self.config)
            return defer.succeed(gen.generateReply(query))
        if action == "default_value":
            gen = core.dns_reply_generators.DefaultValueReply(self.config)
            return defer.succeed(gen.generateReply(query))
        if action == "custom_value":
            gen = core.dns_reply_generators.CustomValueReply(self.config)
            return defer.succeed(gen.generateReply(query))

        raise RuntimeError("ERROR: requested action {}, which could not be"
                " provided by DNSHandler!".format(action))

    def query(self, query, timeout=None):
        """
        This method decides how to handle 
        """
        if self._dynamicResponseRequired(query):
            return self._doDynamicResponse(query)
        else:
            return defer.fail(error.DomainError())

class CustomDNSServerFactory(server.DNSServerFactory):
    """
    The default DNS Server Factory does always set a response code
    of if a response is given. We have a special use case where we want
    to have answers that have the NXDOMAIN flag set. 
    This can with the normal Server Factory only be done with an error
    is given. 
    In our setup, this would result in the queries to be passed to the
    second resolver (which is the proxy). 
    
    We don't wont that and therefore set the NXDOMAIN flag if our answers
    are empty.
    """
    def __init__(self, authorities=None, caches=None, clients=None, verbose=0): 
        super().__init__(authorities, caches, clients, verbose)

    def gotResolverResponse(self, response, protocol, message, address):
        ans, auth, add = response
        if len(ans) > 0:
            
            # here we go to the parent as there is an answer
            return super().gotResolverResponse(response, protocol, message, address)

        response = self._responseFromMessage(
                                message=message, rCode=dns.ENAME,
                                answers=ans, authority=auth, additional=add)
        self.sendReply(protocol, response, address)

        l = len(ans) + len(auth) + len(add)
        self._verboseLog("Lookup found %d record%s" % (l, l != 1 and "s" or ""))

        if self.cache and l:
            self.cache.cacheResult(
                message.queries[0], (ans, auth, add)
            )

class FakeDnsProxy:
    def __init__(self, config_file):
        self.config_file = config_file
        self.config = core.config.ConfigParser()
        self.config.parse_config(self.config_file)
        self.is_setup = False

    def setup(self):
        self.is_setup = True
        self.dns_handler = DNSHandler(self.config)

        factory = CustomDNSServerFactory(clients=[self.dns_handler])
        protocol = dns.DNSDatagramProtocol(controller=factory)

        self.port = reactor.listenUDP(self.config['listening_info']['port'], 
                                      protocol, 
                                      interface=self.config['listening_info']['ip'])

   
    def run(self):
        self.setup()
        return reactor.run()

    def stopListening(self):
        if self.is_setup: 
            return self.port.stopListening()

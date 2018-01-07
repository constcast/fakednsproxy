from twisted.trial import unittest
from twisted.internet import reactor, defer, task
from twisted.names import dns, client, server
import twisted
import socket

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from twisted.names.dns import Query

from core.main import FakeDnsProxy
from core.main import DNSHandler
from core.config import ConfigParser

FAKE_DNS_PORT=40000
TEST_DNS_PORT=2000

def printResult(result):
    answers, authority, additional = result
    if answers:
        a = answers[0]
        print('{} IN {}'.format(a.name.name, a.payload))

class PreCondition_Tester(unittest.TestCase):
    def test_listening(self):
        """
        For these tests it is required that we can bind some fake dns services
        to the localhost ports defined by the global variables FAKE_DNS_PORT
        and TEST_DNS_PORT.
        We test if that is possible
        """
        for port in (FAKE_DNS_PORT, TEST_DNS_PORT):
            try:
                sock = socket.socket(socket.AF_INET, # Internet
                                     socket.SOCK_DGRAM) # UDP
                sock.bind(('127.0.0.1', port))
                sock.close()
            except Exception as e:
                self.fail("Could not bind port localhost:{}. This is necessary "
                        "for the tests. Error: {}.".format(port, e))
 

class MainTester(unittest.TestCase):
    config_dir = os.path.join(os.path.dirname(__file__), '..', 'test_data', 'main_tester_config')

    def setUp(self):
        config_file = os.path.join(self.config_dir, 'minimal_config.yaml')
        self.serv = FakeDnsProxy(config_file)

        # setup a DNS resolver that can be used to generate test DNS queries
        # the client will point to the port defined in the minimal_config.yaml
        # in test_data/main_tester_config/minimal_config.yaml
        self.test_dns_client = client.Resolver(servers=[('127.0.0.1', TEST_DNS_PORT)],
                                               resolv=None)
        twisted.internet.base.DelayedCall.debug = True

        # setup a fake DNS server that we can use to test DNS forwarding
        # this will fail if it cannot open port 40000 on 127.0.0.1
        class ResolverStub(object):
            def query(self, query, timeout=None):
                answer = dns.RRHeader(
                        name=query.name.name,
                        payload=dns.Record_A(address='1.2.3.4'))
                return defer.succeed(([ answer ], [], []))
 
        fake_dns_factory = server.DNSServerFactory(clients=[ResolverStub()])
        fake_dns_server_protocol = dns.DNSDatagramProtocol(controller=fake_dns_factory)
        self.fake_dns_server_port = reactor.listenUDP(FAKE_DNS_PORT, fake_dns_server_protocol,
                                                      interface='127.0.0.1')


    def tearDown(self):
        def cb(ignored):
            pass

        cleanup_actions = []
        d = self.serv.stopListening()
        if d:
            d.addCallback(cb)
            cleanup_actions.append(d)

        cleanup_actions.append(self.fake_dns_server_port.stopListening().addCallback(cb))
        cleanup_list = defer.DeferredList(cleanup_actions)
        cleanup_list.addCallback(cb)
        return cleanup_list

    def test_resolving_forward(self):
        self.serv.config['default_dns_policy'] = 'forward'
        self.serv.config['dns_server']['ip'] = '127.0.0.1'
        self.serv.config['dns_server']['port'] = FAKE_DNS_PORT
        self.serv.setup()
        p = self.test_dns_client.lookupAddress('foobar.com')
        def callBack(results):
            answers, _, _ = results
            self.assertEqual(len(answers), 1)
            answer = answers[0]
            self.assertEqual(answer.name.name, b"foobar.com")
            self.assertEqual(answer.payload.dottedQuad(), '1.2.3.4')
        p.addCallback(callBack)
        return p
        
    def test_resolving_nxdomain(self):
        self.serv.config['default_dns_policy'] = 'nxdomain'
        self.serv.config['dns_server']['ip'] = '127.0.0.1'
        self.serv.config['dns_server']['port'] = FAKE_DNS_PORT
        self.serv.setup()
        p = self.test_dns_client.lookupAddress('foobar.com')
        return self.assertFailure(p, twisted.names.error.DNSNameError)

    def test_resolving_default_value_single_ip(self):
        self.serv.config['default_dns_policy'] = 'default_value'
        self.serv.config['default_dns_value'] = '127.0.0.1'
        self.serv.config['dns_server']['ip'] = '127.0.0.1'
        self.serv.config['dns_server']['port'] = FAKE_DNS_PORT
        self.serv.setup()
        p = self.test_dns_client.lookupAddress('foobar.com')
        def callBack(results):
            answers, _, _ = results
            self.assertEqual(len(answers), 1)
            answer = answers[0]
            self.assertEqual(answer.name.name, b"foobar.com")
            self.assertEqual(answer.payload.dottedQuad(), '127.0.0.1')
        p.addCallback(callBack)
        return p
 
    def test_resolving_default_value_multiple_ips(self):
        self.serv.config['default_dns_policy'] = 'default_value'
        self.serv.config['default_dns_value'] = [ '1.2.3.4', '2.3.4.5' ]
        self.serv.config['dns_server']['ip'] = '127.0.0.1'
        self.serv.config['dns_server']['port'] = FAKE_DNS_PORT
        self.serv.setup()
        p = self.test_dns_client.lookupAddress('foobar.com')
        def callBack(results):
            answers, _, _ = results
            self.assertEqual(len(answers), 2)
            answer = answers[0]
            self.assertEqual(answer.name.name, b"foobar.com")
            self.assertEqual(answer.payload.dottedQuad(), '1.2.3.4')
            answer = answers[1]
            self.assertEqual(answer.name.name, b"foobar.com")
            self.assertEqual(answer.payload.dottedQuad(), '2.3.4.5')
        p.addCallback(callBack)
        return p

    def test_resolving_specific_value_single_ip(self):
        self.serv.config['default_dns_policy'] = 'nxdomain'
        self.serv.config['dns_server']['ip'] = '127.0.0.1'
        self.serv.config['dns_server']['port'] = FAKE_DNS_PORT
        self.serv.config['domain_config'] = {
            'foobar.com': '1.2.3.4'
        }
        self.serv.setup()
        p = self.test_dns_client.lookupAddress('foobar.com')
        def callBack(results):
            answers, _, _ = results
            self.assertEqual(len(answers), 1)
            answer = answers[0]
            self.assertEqual(answer.name.name, b"foobar.com")
            self.assertEqual(answer.payload.dottedQuad(), '1.2.3.4')
        p.addCallback(callBack)
        return p
 
    def test_resolving_specific_value_multiple_ips(self):
        self.serv.config['default_dns_policy'] = 'nxdomain'
        self.serv.config['dns_server']['ip'] = '127.0.0.1'
        self.serv.config['dns_server']['port'] = FAKE_DNS_PORT
        self.serv.config['domain_config'] = {
            'foobar.com': [ '1.2.3.4', '2.3.4.5' ]
        }
        self.serv.setup()
        p = self.test_dns_client.lookupAddress('foobar.com')
        def callBack(results):
            answers, _, _ = results
            self.assertEqual(len(answers), 2)
            answer = answers[0]
            self.assertEqual(answer.name.name, b"foobar.com")
            self.assertEqual(answer.payload.dottedQuad(), '1.2.3.4')
            answer = answers[1]
            self.assertEqual(answer.name.name, b"foobar.com")
            self.assertEqual(answer.payload.dottedQuad(), '2.3.4.5')
        p.addCallback(callBack)
        return p

    def test_resolving_wild_card(self):
        """
        Full testing of wildcarding is done in test_dns_reply_generator.py
        This test just checks that the full path for wild carding is supported.
        """
        self.serv.config['default_dns_policy'] = 'nxdomain'
        self.serv.config['dns_server']['ip'] = '127.0.0.1'
        self.serv.config['dns_server']['port'] = FAKE_DNS_PORT
        self.serv.config['domain_config'] = {
            '*.foobar.com': [ '1.2.3.4', '2.3.4.5' ]
        }
        self.serv.setup()
        p = self.test_dns_client.lookupAddress('a.foobar.com')
        def callBack(results):
            answers, _, _ = results
            self.assertEqual(len(answers), 2)
            answer = answers[0]
            self.assertEqual(answer.name.name, b"a.foobar.com")
            self.assertEqual(answer.payload.dottedQuad(), '1.2.3.4')
            answer = answers[1]
            self.assertEqual(answer.name.name, b"a.foobar.com")
            self.assertEqual(answer.payload.dottedQuad(), '2.3.4.5')
        p.addCallback(callBack)
        return p
     
class DNSHandlerTester(unittest.TestCase):
    """
    These tests verify that the DNS Handler handles packets according to 
    its configuration
    """

    def _test_dyn_resp_check(self, config, assertResult):
        dnshandler = DNSHandler(ConfigParser(config_obj=config))
        q = Query('foobar.com')
        result = dnshandler._dynamicResponseRequired(q)
        self.assertEqual(result, assertResult)

    def _test_dns_reply_generation(self, config):
        dnshandler = DNSHandler(config)
        q = Query('domain.com')
        return dnshandler._doDynamicResponse(q)


    def test_default_policy_forward_handling(self):
        config = { 'default_dns_policy' : 'forward' }
        self._test_dyn_resp_check(config, True)

    def test_default_policy_nxdomain_handling(self):
        config = { 'default_dns_policy' : 'nxdomain' }
        self._test_dyn_resp_check(config, True)

    def test_default_policy_default_value_handling(self):
        config = { 'default_dns_policy' : 'default_value' }
        self._test_dyn_resp_check(config, True)

    def test_default_policy_invalid_handling(self):
        config = { 'default_dns_policy' : 'invalid' }
        with self.assertRaises(RuntimeError):
            self._test_dyn_resp_check(config, True)


    def test_domain_policy_forward(self):
        config = { 'domain_config' : { 'foobar.com': 'forward' } }
        self._test_dyn_resp_check(config, True)

    def test_domain_policy_nxdomain(self):
        config = { 'domain_config' : { 'foobar.com': 'nxdomain' } }
        self._test_dyn_resp_check(config, True)

    def test_domain_policy_somevalue(self):
        config = { 'domain_config' : { 'foobar.com': '127.0.0.1' } }
        self._test_dyn_resp_check(config, True)

    def test_domain_wildcard_check(self):
        config = { 'domain_config' : { '*.com': '127.0.0.1' } }
        self._test_dyn_resp_check(config, True)
    
    def test_generate_nx_answer(self):
        config = { 'default_dns_policy': 'nxdomain' }
        response_deferred = self._test_dns_reply_generation(config)
        def callback(response):
            answer, _, _ = response
            self.assertEqual(len(answer), 0)
        response_deferred.addCallback(callback)

    def test_generate_default_answer_single_ip(self):
        config = { 'default_dns_policy': 'default_value',
                   'default_dns_value' : '127.1.2.3'
                 }
        response_deferred = self._test_dns_reply_generation(config)
        def callback1(response):
            answer, _, _ = response
            self.assertEqual(len(answer), 1)
            a = answer[0]
            self.assertEqual(a.name.name, b"domain.com")
            self.assertEqual(a.payload.dottedQuad(), '127.1.2.3')
        response_deferred.addCallback(callback1)
        return response_deferred

    def test_generate_default_answer(self):
        config = { 'default_dns_policy': 'default_value',
                   'default_dns_value' : [ '1.2.3.4', '2.3.4.5' ]
                 }
        r = self._test_dns_reply_generation(config)
        def callback1(response):
            answer, _, _ = response
            self.assertEqual(len(answer), 2)
            a = answer[0]
            self.assertEqual(a.name.name, b"domain.com")
            self.assertEqual(a.payload.dottedQuad(), '1.2.3.4')
            a = answer[1]
            self.assertEqual(a.name.name, b"domain.com")
            self.assertEqual(a.payload.dottedQuad(), '2.3.4.5')
        r.addCallback(callback1)
        return r
         
    def test_generate_specific_answer_single_ip(self):
        config = { 'default_dns_policy': 'default_value',
                   'default_dns_value' : [ '1.2.3.4', '2.3.4.5' ],
                   'domain_config': {
                        'domain.com': '127.0.0.1',
                    }
                 }
        r = self._test_dns_reply_generation(config)
        def callback(response):
            answer, _, _ = response
            self.assertEqual(len(answer), 1)
            a = answer[0]
            self.assertEqual(a.name.name, b"domain.com")
            self.assertEqual(a.payload.dottedQuad(), '127.0.0.1')
        r.addCallback(callback)
        return r

    def test_generate_specific_answer_multiple_ips(self):
        config = { 'default_dns_policy': 'default_value',
                   'default_dns_value' : [ '1.2.3.4' ],
                   'domain_config': {
                        'domain.com': [ '127.0.0.1', '127.0.0.2' ],
                    }
                 }
        r = self._test_dns_reply_generation(config)
        def callback(response):
            answer, _, _ = response
            self.assertEqual(len(answer), 2)
            a = answer[0]
            self.assertEqual(a.name.name, b"domain.com")
            self.assertEqual(a.payload.dottedQuad(), '127.0.0.1')
            a = answer[1]
            self.assertEqual(a.name.name, b"domain.com")
            self.assertEqual(a.payload.dottedQuad(), '127.0.0.2')
        r.addCallback(callback)
        return r



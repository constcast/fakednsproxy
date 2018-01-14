from twisted.trial import unittest
from twisted.internet import reactor, defer, task
from twisted.names import dns, client, server
import twisted
import socket

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from twisted.names.dns import Query

from core.dns_reply_generators import DNSReplyGenerator
from core.dns_reply_generators import DNSAnswerConfig

class DNSReplygeneratorMatchTester(unittest.TestCase):
    def _test_domain_match(self, config, domain, should_match=None):
        drg = DNSReplyGenerator(config)
        if should_match:
            config_entry = drg.getDomainConfigEntry(domain)
            self.assertEqual(config_entry, should_match)
        else:
            with self.assertRaises(RuntimeError):
                drg.getDomainConfigEntry(domain)

    def test_domain_match_empty_domain_conf(self):
        config = {}
        self._test_domain_match(config, 'foo.com', should_match=None)

    def test_domain_match_exact(self):
        config = { 'domain_config': {
                'foo.com': '127.0.0.1',
            }}
        self._test_domain_match(config, 'foo.com', should_match='127.0.0.1')


    def test_domain_match_no_match(self):
        config = { 'domain_config': {
                'foo.com': '127.0.0.1',
            }}
        self._test_domain_match(config, 'a.foo.com', should_match=None)


    def test_domain_match_wildcard_first(self):
        config = { 'domain_config': {
                '*.foo.com': '127.0.0.1',
            }}
        self._test_domain_match(config, 'a.foo.com', should_match='127.0.0.1')
        config = { 'domain_config': {
                '*foo.com': '127.0.0.1',
            }}
        self._test_domain_match(config, 'a.foo.com', should_match='127.0.0.1')
        self._test_domain_match(config, 'barfoo.com', should_match='127.0.0.1')


    def test_domain_match_wildcard_middle(self):
        config = { 'domain_config': {
                'a.*.com': '127.0.0.1',
            }}
        self._test_domain_match(config, 'a.foo.com', should_match='127.0.0.1')
        self._test_domain_match(config, 'a.blablab.com', should_match='127.0.0.1')

    def test_domain_match_wildcard_end(self):
        config = { 'domain_config': {
                'foo.*': '127.0.0.1',
            }}
        self._test_domain_match(config, 'foo.com', should_match='127.0.0.1')
        self._test_domain_match(config, 'foo.org', should_match='127.0.0.1')
        

    def test_domain_match_multiple_wildcards(self):
        config = { 'domain_config': {
                'foo*.bar*.com': '127.0.0.1',
            }}
        self._test_domain_match(config, 'foo.com', should_match=None)
        self._test_domain_match(config, 'foo.bar.com', should_match='127.0.0.1')
        self._test_domain_match(config, 'foobar.barfoo.com', should_match='127.0.0.1')

class DNSAnswerConfigTester(unittest.TestCase):
    def test_ip_generation(self):
        a =  DNSAnswerConfig('127.0.0.1')
        self.assertEqual(True, 'A' in a.value_dict)
        self.assertEqual('127.0.0.1', a.value_dict['A'])

    def test_ipv6_generation(self):
        a = DNSAnswerConfig('::1')
        self.assertEqual(True, 'AAAA' in a.value_dict)
        self.assertEqual('::1', a.value_dict['AAAA'])

    def test_ip_list_generation(self):
        a =  DNSAnswerConfig(['127.0.0.1', '127.0.0.2'])
        self.assertEqual(True, 'A' in a.value_dict)
        self.assertEqual(2, len(a.value_dict['A']))
        self.assertEqual('127.0.0.1', a.value_dict['A'][0])
        self.assertEqual('127.0.0.2', a.value_dict['A'][1])

    def test_ipv6_list_generation(self):
        a =  DNSAnswerConfig(['::1', '::2'])
        self.assertEqual(True, 'AAAA' in a.value_dict)
        self.assertEqual(2, len(a.value_dict['AAAA']))
        self.assertEqual('::1', a.value_dict['AAAA'][0])
        self.assertEqual('::2', a.value_dict['AAAA'][1])

    def test_ipv4_and_ipv6_list_generation(self):
        a =  DNSAnswerConfig(['::1', '127.0.0.1', '::2', '127.0.0.2'])
        self.assertEqual(True, 'AAAA' in a.value_dict)
        self.assertEqual(2, len(a.value_dict['AAAA']))
        self.assertEqual('::1', a.value_dict['AAAA'][0])
        self.assertEqual('::2', a.value_dict['AAAA'][1])
        self.assertEqual(True, 'A' in a.value_dict)
        self.assertEqual(2, len(a.value_dict['A']))
        self.assertEqual('127.0.0.1', a.value_dict['A'][0])
        self.assertEqual('127.0.0.2', a.value_dict['A'][1])

    def test_invalid_list_generation(self):
        with self.assertRaises(RuntimeError):
            a = DNSAnswerConfig(['::1', 'invalid_address'])


    def test_ip_list_invalid_address(self):
        with self.assertRaises(RuntimeError):
            a = DNSAnswerConfig('invalid_address')

    def test_is_ipv4_address(self):
        a = DNSAnswerConfig(None)
        self.assertEqual(True, a.isIPv4Address('127.0.0.1'))
        self.assertEqual(False, a.isIPv4Address('invalid'))
        self.assertEqual(False, a.isIPv4Address('::1'))

    def test_is_ipv6_address(self):
        a = DNSAnswerConfig(None)
        self.assertEqual(False, a.isIPv6Address('127.0.0.1'))
        self.assertEqual(False, a.isIPv6Address('invalid'))
        self.assertEqual(True, a.isIPv6Address('::1'))

    def test_is_valid_query_type(self):
        a = DNSAnswerConfig(None)
        self.assertEqual(True, a.isValidQueryType('A'))
        self.assertEqual(True, a.isValidQueryType('AAAA'))
        self.assertEqual(True, a.isValidQueryType('NS'))
        self.assertEqual(True, a.isValidQueryType('MX'))
        self.assertEqual(False, a.isValidQueryType('Foobar'))

    def test_query_value_valid_dict(self):
        value_dict = {
                'A': '127.0.0.1',
                'AAAA': [ '::1', "::2" ],
                'NS' : [ '::1' ]
        }
        a = DNSAnswerConfig(value_dict)
        self.assertEqual(value_dict, a.value_dict)

    def test_query_value_invalid_dict(self):
        value_dict = {
                'A': '127.0.0.1',
                'AAAAA': [ '::1', "::2" ],
                'nonexistant' : [ '::1' ]
        }
        with self.assertRaises(RuntimeError):
            a = DNSAnswerConfig(value_dict)

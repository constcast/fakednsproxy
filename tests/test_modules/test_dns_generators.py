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
from core.config import ConfigParser

class DNSReplygeneratorMatchTester(unittest.TestCase):
    def _test_domain_match(self, config, qtype, domain, should_match=None):
        cp = ConfigParser(config)
        cp.generate_config_objects()
        drg = DNSReplyGenerator(config)
        if should_match:
            config_entry = drg.getDomainConfigEntry(domain)
            self.assertEqual(config_entry[qtype], should_match)
        else:
            with self.assertRaises(RuntimeError):
                drg.getDomainConfigEntry(domain)

    def test_domain_match_empty_domain_conf(self):
        config = {}
        self._test_domain_match(config, 'A', 'foo.com', should_match=None)

    def test_domain_match_exact(self):
        config = { 'domain_config': {
                'foo.com': '127.0.0.1',
            }}
        self._test_domain_match(config, 'A', 'foo.com', should_match=['127.0.0.1'])


    def test_domain_match_no_match(self):
        config = { 'domain_config': {
                'foo.com': '127.0.0.1',
            }}
        self._test_domain_match(config, 'A', 'a.foo.com', should_match=None)


    def test_domain_match_wildcard_first(self):
        config = { 'domain_config': {
                '*.foo.com': '127.0.0.1',
            }}
        self._test_domain_match(config, 'A', 'a.foo.com', should_match=['127.0.0.1'])
        config = { 'domain_config': {
                '*foo.com': '127.0.0.1',
            }}
        self._test_domain_match(config, 'A', 'a.foo.com', should_match=['127.0.0.1'])
        self._test_domain_match(config, 'A', 'barfoo.com', should_match=['127.0.0.1'])


    def test_domain_match_wildcard_middle(self):
        config = { 'domain_config': {
                'a.*.com': '127.0.0.1',
            }}
        self._test_domain_match(config, 'A', 'a.foo.com', should_match=['127.0.0.1'])
        self._test_domain_match(config, 'A', 'a.blablab.com', should_match=['127.0.0.1'])

    def test_domain_match_wildcard_end(self):
        config = { 'domain_config': {
                'foo.*': '127.0.0.1',
            }}
        self._test_domain_match(config, 'A', 'foo.com', should_match=['127.0.0.1'])
        self._test_domain_match(config, 'A', 'foo.org', should_match=['127.0.0.1'])
        

    def test_domain_match_multiple_wildcards(self):
        config = { 'domain_config': {
                'foo*.bar*.com': '127.0.0.1',
            }}
        self._test_domain_match(config, 'A', 'foo.com', should_match=None)
        self._test_domain_match(config, 'A', 'foo.bar.com', should_match=['127.0.0.1'])
        self._test_domain_match(config, 'A', 'foobar.barfoo.com', should_match=['127.0.0.1'])



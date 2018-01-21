import unittest

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from core.main import CustomDNSServerFactory
from twisted.names import dns, client, server

class TestLogStringGeneration(unittest.TestCase):
    def _getDNSFactory(self):
        ret = CustomDNSServerFactory()
        return ret

    def _getRRHeader(self, type, record):
        answer = dns.RRHeader(
                            name='foobar.com',
                            type=type,
                            payload=record)
        return answer
 
    def test_A_record_response(self):
        f = self._getDNSFactory()
        h = self._getRRHeader(dns.A, dns.Record_A(address='1.2.3.4'))
        s = f.getDNSAnswerRecordLog(h)
        self.assertEqual('A - foobar.com - 1.2.3.4', s)

    def test_N_record_response(self):
        f = self._getDNSFactory()
        h = self._getRRHeader(dns.NS, dns.Record_NS(name=b'ns.foobar.com'))
        s = f.getDNSAnswerRecordLog(h)
        self.assertEqual('NS - foobar.com - ns.foobar.com', s)

    def test_MX_record_response(self):
        f = self._getDNSFactory()
        h = self._getRRHeader(dns.MX, dns.Record_MX(name=b'mail.foobar.com'))
        s = f.getDNSAnswerRecordLog(h)
        self.assertEqual('MX - foobar.com - mail.foobar.com', s)

    def test_AAAA_record_response(self):
        f = self._getDNSFactory()
        h = self._getRRHeader(dns.AAAA, dns.Record_AAAA(address="::1"))
        s = f.getDNSAnswerRecordLog(h)
        self.assertEqual('AAAA - foobar.com - ::1', s)

    def _createDNSResponseTemplate(self):
        """
        This method creates a template for "response", "protocol", "message",
        and "address", which can be used as input for getDNSREsponseLogMessage()
        """
        response = ([], [], [])
        protocol = None
        message = dns.Message()
        address = ('127.0.0.1', '12345')
        return (response, protocol, message, address)


    def test_simple_NX_response_DNS_messages(self):
        f = self._getDNSFactory()
        response, protocol, message, address = self._createDNSResponseTemplate()
        message.addQuery('foobar.com', dns.A)
        log_messages = f.getDNSResponseLogMessage(response, protocol, message, address)
        self.assertEqual(1, len(log_messages))
        self.assertEqual('Request from - 127.0.0.1:12345 - Query: A:foobar.com - Answer: NXDomain', log_messages[0])


    def test_simple_A_response_DNS_messages(self):
        f = self._getDNSFactory()
        response, protocol, message, address = self._createDNSResponseTemplate()
        message.addQuery('foobar.com', dns.A)
        h = self._getRRHeader(dns.A, dns.Record_A(address='1.2.3.4'))
        response = ([h], [], [])
        log_messages = f.getDNSResponseLogMessage(response, protocol, message, address)
        self.assertEqual(1, len(log_messages))
        self.assertEqual('Request from - 127.0.0.1:12345 - Query: A:foobar.com - Answer: A - foobar.com - 1.2.3.4', log_messages[0])

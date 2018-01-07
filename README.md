FakeDnsProxy
============

FakeDnsProxy is a small python tool that can be used to setup a fake DNS server. 
FakeDnsProxy can be quickly configured to 

- proxy a set of DNS requests to a legitimate DNS Server
- answer a set of DNS requests with pre-defined DNS messages
- suppress answers to DNS requests

FakeDnsProxy can be configured to have a default behavior that defines how
FakeDnsProxy reacts to unknown Domains. It can be configured to respond with
a static IP, to proxy requests to a real DNS server, or to reply with NXDOMAIN.
Furthermore, it is possible to define special behavior for individual domains.

Installation
------------

You need to install the following pre-requisites (debian packages):

- python3
- python3-yaml
- python3-dnspython
- python3-twisted

Configuration
-------------

The configuration file is a YAML file that supports the following configuration
entries:


### listening_info: (required)

Defines the IP and port that fakednsproxy should listen on. *listening_info*
takes two sub-configs *ip* and *port*.

    listening_info:
      ip: 127.0.0.1
      port: 53

### dns_server: (required)

Defines the DNS server that should be used to proxy DNS requests to. *dns_server*
takes two sub_configs *ip* and *port*:

    dns_server:
      ip: 8.8.8.8
      port: 53

### default_dns_policy: (required)

Defines the default behavior for fakednsproxy for queries. The following policies
are supported:

- *nxdomain*
  If nxdomain is configured, then FakeDnsProxy will send a NXDOMAIN response to 
  every DNS query that does not have a separately defined behavior in the config
  section *domain_config*.
- *forward*
  This policy will forward every DNS query to the server configured in *dns_server*
  if no special configuration exists for this domain in the config section
  *domain_config*.
- *default_value*
  Will send a default value to every DNS query if no special behavior is
  configured for this domain in the *domain_config* section. It is required
  to set the config *defautl_dns_value* with the value if this policy is 
  selected

Example:

    default_dns_policy: forward

### default_dns_value: (required if policy default_value was selected)

Specifies which value should be returned for the *default_value* policy. 
Valid values can either be an IP, e.g. '127.0.0.1', or a list of IPs, e.g.
[ '127.0.0.1', '127.0.0.2' ].

    default_value: '127.0.0.1'

or

    default_value: [ '127.0.0.1', '127.0.0.2' ]

### domain_config: (optional)

Defines a list of special responses for individual domains. This configuraiton
overwrites the behavior of the defined *default_dns_policy* for the configured
domains. 

Each entry is of the form:
 
    domain: <behavior>

where *domain* is the domain in the DNS query (e.g. www.github.com), and the 
behavior is one of:

- nxdomain
- forward
- <value>

Nxdomain will make FakeDnsProxy return a NXDOMAIN DNS response, forward will 
make FakeDnsProxy to forward the request to the server defined in *dns_server*.
A value is the value returned in the DNS response. Valid values can either be
an IP, e.g. '127.0.0.1', or a list of IPs, e.g. [ '127.0.0.1', '127.0.0.2' ].

Domain can also use '*' as a wildcard character.

    domain_config:
      a.com: nxdomain
      foobar.com: forward
      f.com: 127.0.0.1
      b.com: [ '127.0.0.1', '127.0.0.2' ]
      *.com: 127.0.0.1
      *.foobar.com: 1.2.3.4


Example Configurations:
-----------------------

    listening_info:
      ip: 127.0.0.1
      port: 2000
    dns_server:
      ip: 8.8.8.8
      port: 53
    default_dns_policy: default_value
    default_dns_value: 1.2.3.4
    domain_config:
      a.com: nxdomain
      foobar.com: forward
      f.com: 127.0.0.1
      b.com: [ '127.0.0.1', '127.0.0.2' ]

Testing
-------

Start up fakednsproxy (using the example config above):

    python3 fakednsproxy.py myconfig_file.yaml


Then you can test the functionality using DNS tools such das **dig**:

    dig -p 2000 @127.0.0.1 github.com
    dig -p 2000 @127.0.0.1 a.com
    ...



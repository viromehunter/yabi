# -*- coding: utf-8 -*-
### BEGIN COPYRIGHT ###
#
# (C) Copyright 2011, Centre for Comparative Genomics, Murdoch University.
# All rights reserved.
#
# This product includes software developed at the Centre for Comparative Genomics 
# (http://ccg.murdoch.edu.au/).
# 
# TO THE EXTENT PERMITTED BY APPLICABLE LAWS, YABI IS PROVIDED TO YOU "AS IS," 
# WITHOUT WARRANTY. THERE IS NO WARRANTY FOR YABI, EITHER EXPRESSED OR IMPLIED, 
# INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND 
# FITNESS FOR A PARTICULAR PURPOSE AND NON-INFRINGEMENT OF THIRD PARTY RIGHTS. 
# THE ENTIRE RISK AS TO THE QUALITY AND PERFORMANCE OF YABI IS WITH YOU.  SHOULD 
# YABI PROVE DEFECTIVE, YOU ASSUME THE COST OF ALL NECESSARY SERVICING, REPAIR
# OR CORRECTION.
# 
# TO THE EXTENT PERMITTED BY APPLICABLE LAWS, OR AS OTHERWISE AGREED TO IN 
# WRITING NO COPYRIGHT HOLDER IN YABI, OR ANY OTHER PARTY WHO MAY MODIFY AND/OR 
# REDISTRIBUTE YABI AS PERMITTED IN WRITING, BE LIABLE TO YOU FOR DAMAGES, INCLUDING 
# ANY GENERAL, SPECIAL, INCIDENTAL OR CONSEQUENTIAL DAMAGES ARISING OUT OF THE 
# USE OR INABILITY TO USE YABI (INCLUDING BUT NOT LIMITED TO LOSS OF DATA OR 
# DATA BEING RENDERED INACCURATE OR LOSSES SUSTAINED BY YOU OR THIRD PARTIES 
# OR A FAILURE OF YABI TO OPERATE WITH ANY OTHER PROGRAMS), EVEN IF SUCH HOLDER 
# OR OTHER PARTY HAS BEEN ADVISED OF THE POSSIBILITY OF SUCH DAMAGES.
# 
### END COPYRIGHT ###

"""
Configuration
=============
follows a path, reading in config files. Overlays their settings on top of a default, on top of each other.
then stores the config in a sanitised form in a hash of hashes, inside the object.

Yabi then asks for various settings when it needs them
"""

import ConfigParser
import os.path
import re

import StringIO

import urlparse
import re
re_url_schema = re.compile(r'\w+')

def parse_url(uri):
    """Parse a url via the inbuilt urlparse. But this is slightly different
    as it can handle non-standard schemas. returns the schema and then the
    tuple from urlparse"""
    uri = uri.strip()
    scheme, rest = uri.split(":",1)
    assert re_url_schema.match(scheme)
    return scheme, urlparse.urlparse(rest)

SEARCH_PATH = ["~/.yabi/yabi.conf","~/.yabi/backend/yabi.conf","~/yabi.conf","~/.yabi","/etc/yabi.conf","/etc/yabi/yabi.conf"]

##
## Support functions that do some text processing
##

def port_setting(port):
    """returns ip,port or raises exception if error"""
    if type(port) is tuple:
	return port
    
    re_port = re.compile(r'^(\d+\.\d+\.\d+\.\d+)(:\d+)?$')
    result = re_port.search(port)
    if result:
        ip = result.group(1)
        port = int(result.group(2)[1:]) if result.group(2) else 8000
        return ip, port
    try:
        if str(int(port))==port:
            return '0.0.0.0',int(port)
    except ValueError, ve:
        raise Exception, "malformed IP:port setting"

def email_setting(email):
    """process an email of the form "First Last <email@server.com>" into name and email.
    also handle just plain email address with no name
    """
    import rfc822
    return rfc822.parseaddr(email)

# process boolean string into python boolean type
boolean_proc = lambda x: x if type(x) is bool else x.lower()=="true" or x.lower()=="t" or x.lower()=="yes" or x.lower()=="y"

def path_sanitise(path):
    return os.path.normpath(os.path.expanduser(path))

class ConfigError(Exception):
    pass

##
## The Configuration store. Singleton.
##

class Configuration(object):
    """Holds the running configuration for the full yabi stack that is running under this twistd"""
    SECTIONS = ['backend']       # sections of the config file
    KEYS = ['port','path','start_http','start_https','sslport','alert_email','http_redirect_to_https','http_redirect_to_https_port','memcache_servers','logfile']
    
    # defaults
    config = {
        'backend':  {
                        "port":"0.0.0.0:8000",
                        "start_http":"true",
                        
                        "sslport":"0.0.0.0:8443",
                        "start_https":"false",
                        
                        "path":"/",
                                                
                        "telnet":"false",
                        "telnet_port":"0.0.0.0:8021",
                        
                        "fifos":None,
                        "tasklets":None,
                        "certificates":None,
                        
                        "certfile":"~/.yabi/servercert.pem",
                        "keyfile":"~/.yabi/servercert.pem",
                        
                        "hmackey":None,
                                                
                        "alert_email":"Tech Alerts <alerts@ccg.murdoch.edu.au>",
                        
                        "memcache_servers":"memcache1.localdomain:11211 memcache2.localdomain:11211",
                        "memcache_prefix":"yabibe",
                        
                        "admin":None                # none means "use the one provided here"
                    },
        'taskmanager':{
                        'simultaneous':'5',
                        'polldelay':'5',
                        'startup':'true',
                        "tasktag":None,
                    }
    }
    
    def read_from_data(self,dat):
        return self.read_from_fp(StringIO.StringIO(dat))
    
    def read_from_file(self,filename):
        return self.read_from_fp(open(filename)) if os.path.exists(filename) and os.path.isfile(filename) else None
    
    def read_from_fp(self,fp):
        conf_parser = ConfigParser.ConfigParser()
        conf_parser.readfp(fp)
        
        # main sections
        for section in self.SECTIONS:
            if conf_parser.has_section(section):
                # process section
                
                if section not in self.config:
                    self.config[section] = {}
                
                for key in self.KEYS:
                    if conf_parser.has_option(section,key):
                        self.config[section][key] = conf_parser.get(section,key)
        
        # taskmanager section
        name = "taskmanager"
        if conf_parser.has_section(name):
            self.config[name]['polldelay'] = conf_parser.get(name,'polldelay')
            self.config[name]['simultaneous'] = conf_parser.get(name,'simultaneous')
            self.config[name]['startup'] = boolean_proc(conf_parser.get(name,'startup'))
            if conf_parser.has_option(name,'tasktag'):
                self.config[name]['tasktag'] = conf_parser.get(name,'tasktag')
            
        # backend section
        name = "backend"
        if conf_parser.has_section(name):
            self.config[name]['admin'] = conf_parser.get(name,'admin')
            if conf_parser.has_option(name,'fifos'):
                self.config[name]['fifos'] = path_sanitise(conf_parser.get(name,'fifos'))
            if conf_parser.has_option(name,'tasklets'):
                self.config[name]['tasklets'] = path_sanitise(conf_parser.get(name,'tasklets'))
            if conf_parser.has_option(name,'certificates'):
                self.config[name]['certificates'] = path_sanitise(conf_parser.get(name,'certificates'))
            if conf_parser.has_option(name,'temp'):
                self.config[name]['temp'] = path_sanitise(conf_parser.get(name,'temp'))
            if conf_parser.has_option(name,'keyfile'):
                self.config[name]['keyfile'] = path_sanitise(conf_parser.get(name,'keyfile'))
            if conf_parser.has_option(name,'certfile'):
                self.config[name]['certfile'] = path_sanitise(conf_parser.get(name,'certfile'))
            if conf_parser.has_option(name,'hmackey'):
                self.config[name]['hmackey'] = conf_parser.get(name,'hmackey')
            
            
            # memcache
            if conf_parser.has_option(name,'memcache_servers'):
                self.config[name]['memcache_servers'] = conf_parser.get(name,'memcache_servers')
            if conf_parser.has_option(name,'memcache_prefix'):
                self.config[name]['memcache_prefix'] = conf_parser.get(name,'memcache_prefix')

    def read_config(self, search=SEARCH_PATH):
        for part in search:
            self.read_from_file(os.path.expanduser(part))
            
    def get_section_conf(self,section):
        return self.config[section]
    
    def sanitise(self):
        """Check the settings for sanity"""
        for section in self.SECTIONS:
            self.config[section]['start_http'] = boolean_proc(self.config[section]['start_http'])
            self.config[section]['start_https'] = boolean_proc(self.config[section]['start_https'])
            self.config[section]['port'] = port_setting(self.config[section]['port'])
            self.config[section]['sslport'] = port_setting(self.config[section]['sslport'])
            self.config[section]['alert_email'] = email_setting(self.config[section]['alert_email'])
            
            conversions = dict( 
                telnet=boolean_proc,
                telnetport=port_setting,
                debug=boolean_proc
                
            )
            
            for key, value in conversions.iteritems():
                if key in self.config[section]:
                    self.config[section][key] = value(self.config[section][key])
         
    ##
    ## Methods to gather settings
    ##
    @property
    def yabiadmin(self):
        scheme,rest = parse_url(self.config['backend']['admin'])
        return "%s:%d%s"%(rest.hostname,rest.port,rest.path)
        
    @property
    def yabiadminscheme(self):
        return parse_url(self.config['backend']['admin'])[0]

    @property
    def yabiadminserver(self):
        return parse_url(self.config['backend']['admin'])[1].hostname
        
    @property
    def yabiadminport(self):
        return parse_url(self.config['backend']['admin'])[1].port
    
    @property
    def yabiadminpath(self):
        return parse_url(self.config['backend']['admin'])[1].path
    
    
    @property
    def yabistore(self):
        return "%s:%d%s"%tuple(self.config['store']['port']+(self.config['store']['path'],))
    
    
    
    ##
    ## classify the settings into a ip/port based classification
    ##
    def classify_ports(self):
        ips = {}
        for section in self.SECTIONS:
            ip, port = self.config[section]['port']
            
            # ip number
            ipstore = ips[ip] if ip in ips else {}
            
            # then port
            portstore = ipstore[port] if port in ipstore else {}
            
            # then path
            path = self.config[section]['path']
            if path in portstore:
                # error. duplicate path
                raise ConfigError, "overlapping application paths"
            
            portstore[path] = section
            
            ipstore[port] = portstore
            ips[ip] = ipstore
            
        return ips
    
config = Configuration()
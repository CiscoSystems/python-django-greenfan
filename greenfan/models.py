#
#   Copyright 2012 Cisco Systems, Inc.
#
#   Author: Soren Hansen <sorhanse@cisco.com>
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
from crypt import crypt
import json
import random
import string
import IPy

from django.db import models
from django.template.loader import render_to_string

from jsonfield import JSONField

from greenfan import utils

class TestSpecification(models.Model):
    name = models.CharField(max_length=200)
    description = JSONField()
    log_listener_port = models.IntegerField(null=True, blank=True)
    log_listener_dir = models.CharField(max_length=200, null=True, blank=True)

    def nodes_qs(self):
        qs = Server.objects.exclude(disabled=True)
        if 'nodes' in self.description:
            nodes = self.description['nodes']
            if 'include' in nodes:
                include = nodes['include']
                if isinstance(include, basestring):
                    include = [include]
                qs = qs.filter(hardware_profile__tags__in=include)
            if 'exclude' in nodes:
                exclude = nodes['exclude']
                if isinstance(exclude, basestring):
                    exclude = [exclude]
                qs = qs.exclude(hardware_profile__tags__in=exclude)

        return qs

    def nodes(self):
        return list(self.nodes_qs())

    def build_node(self):
        return self.nodes()[0]

    def non_build_nodes(self):
        return self.nodes()[1:]

    def control_node(self):
        return self.nodes()[1]

    def compute_nodes(self):
        return self.nodes()[2:]

    def dhcp_low(self):
        nodes = self.nodes()
        nodes.sort(key=lambda node: int(IPy.IP(node.ip).strDec(), 10))
        return nodes[0].ip

    def dhcp_high(self):
        nodes = self.nodes()
        nodes.sort(key=lambda node: int(IPy.IP(node.ip).strDec(), 10))
        return nodes[-1].ip

    def json_description(self):
        return json.dumps(self.description, indent=2)

    def logging(self):
        return {'host': utils.src_ip(self.build_node().ip),
                'port': self.log_listener_port}

    def manifest(self):
        return render_to_string('manifest.tmpl',
                                {'job': self,
                                 'config': Configuration.get(),
                                 'nodes': self.nodes()})

class Configuration(models.Model):
    subnet = models.IPAddressField()
    netmask = models.IPAddressField()
    domain = models.CharField(max_length=200)
    gateway = models.IPAddressField()
    ntp_servers = models.CharField(max_length=200,
                                   help_text='Name servers (separated by spaces)')
    nameservers = models.CharField(max_length=200,
                                   help_text='Name servers (separated by spaces)')
    proxy = models.CharField(max_length=200)
    admin_user = models.CharField(max_length=200)
    admin_password = models.CharField(max_length=200)

    def save(self):
        # Poor man's singleton implementation
        if self.id is None:
            confs = Configuration.objects.all()
            if len(confs) > 1:
                raise Exception('Multiple configs found')
            elif len(confs) == 1:
                self.id = confs[0].id

        return super(Configuration, self).save()

    @classmethod
    def get(cls):
        return cls.objects.all()[0]

    def name_server_list(self):
        return self.nameservers.split(' ')

    def name_server(self):
        return self.name_server_list()[0]

    def ntp_server_list(self):
        return self.ntp_servers.split(' ')

    def ntp_server(self):
        return self.ntp_server_list()[0]

    def admin_password_crypted(self):
        alphabet = string.letters + string.digits
        salt = ''.join([random.choice(alphabet) for x in range(10)])
        return crypt(self.admin_password, '$6$%s' % (salt,))

    def subnet_as_sql(self):
        if self.netmask.endswith('0.0.0'):
            wildcards = 3
        elif self.netmask.endswith('0.0'):
            wildcards = 2
        else:
            wildcards = 1

        return '%s.%s' % ('.'.join(self.subnet.split('.')[:4-wildcards]),
                          '.'.join(['%' for x in range(wildcards)]))

class HardwareProfileTag(models.Model):
    name = models.CharField(max_length=200, primary_key=True)

    def __unicode__(self):
        return self.name


class HardwareProfile(models.Model):
    name = models.CharField(max_length=200)
    description = JSONField()
    tags = models.ManyToManyField(HardwareProfileTag)

    def __unicode__(self):
        return self.name

    def json_description(self):
        return json.dumps(self.description, indent=2)


class Server(models.Model):
    POWER_MGMT_TYPE_UCS = 'ucs'
    POWER_MGMT_TYPE_IPMITOOL = 'ipmitool'
    POWER_MGMT_TYPE_CHOICES = (
       (POWER_MGMT_TYPE_UCS, 'UCSM (Cisco UCS blades)'),
       (POWER_MGMT_TYPE_IPMITOOL, 'IPMI (Cisco UCS rack servers)'))

    name = models.CharField(max_length=200)
    ip = models.IPAddressField()
    mac = models.CharField(max_length=17)
    power_address = models.CharField(max_length=200)
    power_type = models.CharField(max_length=30,
                                  choices=POWER_MGMT_TYPE_CHOICES)
    power_user = models.CharField(max_length=30)
    power_password = models.CharField(max_length=50)
    power_id = models.CharField(max_length=200)
    hardware_profile = models.ForeignKey(HardwareProfile)
    disabled = models.BooleanField(default=False)
#    disabled_reason = models.CharField(max_length=200, null=True)

    def __unicode__(self):
        return self.name

    def fqdn(self):
        return '%s.%s' % (self.name, Configuration.get().domain)

    def preseed(self):
        return ''

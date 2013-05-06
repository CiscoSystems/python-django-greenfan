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
import os
import os.path
import random
import string
from time import sleep
import IPy

from django.db import models
from django.conf import settings
from fabric.api import env as fabric_env
from fabric.api import sudo
from jsonfield import JSONField

from greenfan import utils


class TestSpecification(models.Model):
    name = models.CharField(max_length=200)
    description = JSONField()

    def create_job(self):
        job = Job(description=self.description)
        job.save()
        return job

class Job(models.Model):
    PENDING = 1
    RUNNING = 2
    FINISHED = 3
    CANCELED = 4
    SERIES_STATES = (
        (PENDING, 'Pending'),
        (RUNNING, 'Running'),
        (FINISHED, 'Finished'),
        (CANCELED, 'Canceled'),
    )

    description = JSONField()
    log_listener_port = models.IntegerField(null=True, blank=True)
    state = models.SmallIntegerField(default=PENDING,
                                     choices=SERIES_STATES)

    def run(self):
        from django.core.management import call_command

        def step(name):
            call_command(name, '%s' % self.id)

        try:
            step('start-log-listener')
            step('list-nodes')
            step('provision-build-node')
            step('wait-for-build-node')
            step('install-and-configure-puppet')
            step('reboot-non-build-nodes')
            step('wait-for-non-build-nodes')
            step('provision-users')
            step('import-images')
            step('run-tempest')
        finally:
            step('stop-log-listener')
            step('turn-off-non-build-nodes')

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

    @property
    def logdir(self):
        return os.path.join(settings.JOB_LOG_DIR, '%s' % self.pk)

    @property
    def rsyslog_conf_file(self):
        return os.path.join(self.logdir, 'rsyslog.conf')

    @property
    def rsyslog_log_file(self):
        return os.path.join(self.logdir, 'logfile')

    @property
    def rsyslog_pid_file(self):
        return os.path.join(self.logdir, 'rsyslog.pid')

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

    def logfile(self):
        return '%s/logfile' % self.log_listener_dir

    def redirect_output(self):
        fp = open(self.logfile(), 'a+')
        os.dup2(fp.fileno(), 1)
        os.dup2(fp.fileno(), 2)
        
    def logging(self):
        return {'host': utils.src_ip(self.build_node().ip),
                'port': self.log_listener_port}

    def _get_nodes_still_installing(self):
        out = sudo('cobbler system find --netboot-enabled=true')
        nodes = out.split('\n')
        return  map(lambda x: x.strip(), nodes)

    def reboot_non_build_nodes(self):
        config = Configuration.get()

        fabric_env.host_string = '%s@%s' % (config.admin_user,
                                            self.build_node().ip)
        fabric_env.password = config.admin_password
        fabric_env.abort_on_prompts = True
        fabric_env.sudo_prefix = 'sudo -H -S -p \'%(sudo_prompt)s\' '

        nodes = self._get_nodes_still_installing()
        for node in nodes:
            sudo('timeout 10 cobbler system poweroff --name=%s' % (node,))
        sleep(5)
        for node in nodes:
            sudo('timeout 10 cobbler system poweron --name=%s' % (node,))

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

    @classmethod
    def _check_at_most_one_conf(cls):
        if Configuration.objects.count() > 1:
            raise Exception('Multiple configs found')

    def save(self):
        self._check_at_most_one_conf()

        # Poor man's singleton implementation
        if self.id is None:
            confs = Configuration.objects.all()
            if len(confs) == 1:
                self.id = confs[0].id

        return super(Configuration, self).save()

    @classmethod
    def get(cls):
        cls._check_at_most_one_conf()
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
        if self.netmask.startswith('255.255.255'):
            wildcards = 1
        elif self.netmask.startswith('255.255'):
            wildcards = 2
        else:
            wildcards = 3

        return '%s.%s' % ('.'.join(self.subnet.split('.')[:4-wildcards]),
                          '.'.join(['%']*wildcards))


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

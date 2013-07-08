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
import tempfile
import urlparse
from time import sleep, time
import IPy

from django.db import models
from django.conf import settings
from fabric.api import env as fabric_env
from fabric.api import run, sudo, put
from jsonfield import JSONField
from cloudslave import models as cloudslave_models

from greenfan import utils


class TestSpecification(models.Model):
    name = models.CharField(max_length=200)
    description = JSONField()

    def create_job(self, physical=False):
        job = Job(description=self.description, physical=physical)
        job.save()
        return job


class Node(object):
    def subnet_as_sql(self):
        if self.netmask.startswith('255.255.255'):
            wildcards = 1
        elif self.netmask.startswith('255.255'):
            wildcards = 2
        else:
            wildcards = 3

        return '%s.%s' % ('.'.join(self.subnet.split('.')[:4-wildcards]),
                          '.'.join(['%']*wildcards))


class VirtualNode(Node):
    def __init__(self, slave):
        self.slave = slave

    def __eq__(self, other):
        return self.slave == other.slave

    @property
    def mac(self):
        if self.slave.state == 'ACTIVE':
            return self.slave.run_cmd("ip --oneline link show dev eth0 | sed -e 's%.*link/ether %%g' -e 's/ .*//g'").strip()
        else:
            return 'TBD'

    @property
    def netmask(self):
        ip = self.slave.run_cmd("ip --oneline addr show dev eth0 | grep inet' ' | sed -e 's%.*inet %%g' -e 's/ .*//g'").strip()
        return IPy.IP(ip, make_net=True).netmask().strNormal()

    @property
    def subnet(self):
        ip = self.slave.run_cmd("ip --oneline addr show dev eth0 | grep inet' ' | sed -e 's%.*inet %%g' -e 's/ .*//g'").strip()
        return IPy.IP(ip, make_net=True).strNormal()

    @property
    def gateway(self):
        return self.slave.run_cmd("ip --oneline route get 8.8.8.8 | sed -e 's%.* via %%g' -e 's/ .*//g'").strip()

    @property
    def power_address(self):
        return 'fake'

    @property
    def power_type(self):
        return 'ucs'

    @property
    def power_user(self):
        return 'fake'

    @property
    def power_password(self):
        return 'fake'

    @property
    def power_id(self):
        return 'fake'

    @property
    def internal_ip(self):
        return self.slave.internal_ip

    @property
    def external_ip(self):
        return self.slave.external_ip

    @property
    def name(self):
        return self.slave.name

    @property
    def hardware_profile(self):
        # FIXME: This logic belongs in cloudslave
        return self.slave.reservation.cloud.client.flavors.get(self.slave.cloud_server.flavor['id']).name

    @property
    def fqdn(self):
        return '%s.%s' % (self.name, Configuration.get().domain)

    @property
    def admin_user(self):
        job = self.slave.reservation.job_set.all()[0]

        # The build node does not get reinstalled
        print self, job.build_node()
        if self == job.build_node():
            return 'ubuntu'

        print  job.steps.index(job.step), job.steps.index('reboot-non-build-nodes')
        if job.steps.index(job.step) > job.steps.index('reboot-non-build-nodes'):
            return Configuration.get().admin_user
        else:
            return 'ubuntu'

    @property
    def admin_password(self):
        return Configuration.get().admin_password

class PhysicalNode(Node):
    def __init__(self, server):
        self.server = server

    @property
    def mac(self):
        return self.server.mac

    @property
    def power_address(self):
        return server.power_address

    @property
    def power_type(self):
        return server.power_type

    @property
    def power_user(self):
        return server.power_user

    @property
    def power_password(self):
        return server.power_password

    @property
    def power_id(self):
        return server.power_id

    @property
    def internal_ip(self):
        return self.server.ip

    @property
    def external_ip(self):
        return self.server.ip

    @property
    def fqdn(self):
        return self.server.fqdn()

    @property
    def subnet(self):
        return Configuration.get().subnet

    @property
    def gateway(self):
        return Configuration.get().gateway

    @property
    def netmask(self):
        return Configuration.get().netmask

    @property
    def admin_user(self):
        return Configuration.get().admin_user

    @property
    def admin_password(self):
        return Configuration.get().admin_password


class NodeScheduler(object):
    def __init__(self, job):
        self.job = job

class PhysicalNodeScheduler(NodeScheduler):
    def _available_nodes_qs(self):
        ### FIXME: This should probably be two .exclude()s
        qs = Server.objects.exclude(disabled=True, job=None)
        if 'nodes' in self.job.description:
            nodes = self.job.description['nodes']
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

    def reserve_nodes(self):
        if job.pk is None:
            raise Exception("Can't reserve nodes before job has been .save()d")

        num_nodes = self.job.description.get('num_nodes', 3)
        for x in range(10):
            # Pick out three that we want
            node_set = self._available_nodes_qs()[:num_nodes]

            # Attempt to assign them to this job
            matches = self._available_nodes_qs().filter(pk__in=[n.pk for n in node_set]).update(job=self.job)

            # .update returns number of matched nodes.
            # Since we filter by availability (by way of accessing the
            # .available_nodes_qs) and pass the specific set of nodes we
            # wanted, getting a different number of matches nodes means
            # someone else grabbed one of our nodes.
            if matches != len(node_set):
                # If this happens, we release them again and start over
                self.release_nodes()
            else:
                return
        raise Exception('Could not find sufficient available nodes')

    def release_nodes(self):
        Server.objects.filter(job=self.job).update(job=None)

    def nodes(self):
        return [PhysicalNode(server) for server in Server.objects.filter(job=self.job)]


class VirtualNodeScheduler(NodeScheduler):
    def reserve_nodes(self):
        if self.job.pk is None:
            raise Exception("Can't reserve nodes before job has been .save()d")

        if 'nodes' in self.job.description:
            if ('include' in self.job.description['nodes'] or
                'exclude' in self.job.description['nodes']):
                raise exc.NodeRequestNotSatisfiable("Virtual nodes requested, but specific include/exclude rules were given.")

        num_nodes = self.job.description.get('num_nodes', 3)
        cloud = cloudslave_models.Cloud.get_random()
        self.job.cloud_slave_reservation = cloud.create_reservation(num_nodes)
        self.job.save()
        self.job.cloud_slave_reservation.start()

    def release_nodes(self):
        self.job.cloud_slave_reservation.terminate()
        self.job.cloud_slave_reservation.delete()

    def nodes(self):
        return [VirtualNode(slave) for slave in self.job.cloud_slave_reservation.slave_set.all()]


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
    physical = models.BooleanField()
    cloud_slave_reservation = models.ForeignKey(cloudslave_models.Reservation,
                                                blank=True, null=True)
    step = models.CharField(max_length=40, default='', blank=True, null=True)

    steps = ['start-log-listener'
             'list-nodes',
             'provision-build-node',
             'wait-for-build-node',
             'install-and-configure-puppet',
             'reboot-non-build-nodes',
             'wait-for-non-build-nodes',
             'provision-users',
             'import-images',
             'run-tempest']

    def run(self):
        from django.core.management import call_command

        def step(name):
            self.step = name
            self.save()
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

    @property
    def scheduler(self):
        if self.physical:
            scheduler_class = PhysicalNodeScheduler
        else:
            scheduler_class = VirtualNodeScheduler

        return scheduler_class(self)

    def nodes(self):
        return self.scheduler.nodes()

    def reserve_nodes(self):
        self.scheduler.reserve_nodes()

    def release_nodes(self):
        self.scheduler.release_nodes()

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
        nodes.sort(key=lambda node: int(IPy.IP(node.internal_ip).strDec(), 10))
        return nodes[0].internal_ip

    def dhcp_high(self):
        nodes = self.nodes()
        nodes.sort(key=lambda node: int(IPy.IP(node.internal_ip).strDec(), 10))
        return nodes[-1].internal_ip

    def json_description(self):
        return json.dumps(self.description, indent=2)

    def redirect_output(self):
        if settings.TESTING:
            return
        fp = open(self.rsyslog_log_file, 'a+')
        os.dup2(fp.fileno(), 1)
        os.dup2(fp.fileno(), 2)

    def logging(self):
        return {'host': utils.src_ip(self.build_node().internal_ip),
                'port': self.log_listener_port}

    def save(self):
        super(Job, self).save()
        if not settings.TESTING and not os.path.exists(self.logdir):
            os.mkdir(self.logdir)

    def _get_nodes_still_installing(self):
        out = sudo('cobbler system find --netboot-enabled=true').strip()
        nodes = out.split('\n')
        return  map(lambda x: x.strip(), nodes)

    def _configure_fabric(self, user, host, password):
        fabric_env.host_string = '%s@%s' % (user, host)
        fabric_env.password = password
        fabric_env.key_filename = '/home/soren/ci/kp.key'
        fabric_env.abort_on_prompts = True
        fabric_env.sudo_prefix = 'sudo -H -S -p \'%(sudo_prompt)s\' '

    def _configure_fabric_for_node(self, node):
        self._configure_fabric(node.admin_user, node.external_ip,
                               node.admin_password)

    def _configure_fabric_for_control_node(self):
        self._configure_fabric_for_node(self.control_node())

    def _configure_fabric_for_build_node(self):
        self._configure_fabric_for_node(self.build_node())

    def provision_users(self):
        self._configure_fabric_for_node(self.build_node())

        from keystoneclient.v2_0 import client
        keystone = client.Client(token='keystone_admin_token', endpoint='http://%s:35357/v2.0' % (self.control_node().external_ip,))
        role_info = {}
        for role in keystone.roles.list():
            role_info[role.name] = role

        tenant_info = dict((tenant.name, tenant) for tenant in keystone.tenants.list())
        if 'tenants' in self.description:
            tenants = self.description['tenants']
            for tenant in tenants:
                if tenant['name'] in tenant_info:
                    continue
                tenant_obj = keystone.tenants.create(tenant_name=tenant['name'], description=tenant.get('description', tenant['name']), enabled=True)
                tenant_info[tenant['name']] = tenant_obj

        user_info = dict((user.name,user) for user in keystone.users.list())
        if 'users' in self.description:
            users = self.description['users']
            for user in users:
                tenant = tenant_info[user['tenant']]

                if user['name'] in user_info:
                    user_obj = user_info[user['name']]
                else:
                    user_obj = keystone.users.create(name=user['name'],
                                                     password=user['password'],
                                                     email=user.get('email', '%s@example.com' % user['name']),
                                                     tenant_id=tenant.id)

                for role in user.get('roles', []):
                    keystone.roles.add_user_role(user_obj, role_info[role], tenant)


    def reboot_non_build_nodes(self):
        self.step = 'reboot-non-build-nodes'
        self.save()
        self._configure_fabric_for_build_node()

        nodes = self._get_nodes_still_installing()
        if self.physical:
            for node in nodes:
                sudo('timeout 10 cobbler system poweroff --name=%s' % (node,))
            sleep(5)
            for node in nodes:
                sudo('timeout 10 cobbler system poweron --name=%s' % (node,))
        else:
            nodes = filter(lambda x:x.name.split('.')[0] in nodes, self.nodes())
            for node in nodes:
                # Ubuntuisms galore
                self._configure_fabric_for_node(node)
                sudo('apt-get -y install pxe-kexec')
                sudo('pxe-kexec -n -l linux -i eth0 %s' % (self.build_node().internal_ip))

    def wait_for_non_build_nodes(self):
        self.step = 'wait-for-non-build-nodes'
        self.save()
        self._configure_fabric_for_build_node()

        timeout = time() + 60*60
        
        expected_set = set([node.fqdn for node in self.nodes()])
        while timeout > time():
	    out = sudo('cd /var/lib/puppet/reports ; ls | cat')
            actual_set = set([name.strip() for name in out.split('\n')])
            if actual_set == expected_set:
                return ''
            print 'Not done yet. %d seconds left' % (timeout - time(),)
            sleep(5)
        raise Exception('Timed out')

    def import_images(self):
        self._configure_fabric_for_control_node()

        glance_user = self.description['users'][0]
        env_string = 'OS_AUTH_URL=http://%s:5000/v2.0 OS_TENANT_NAME=%s OS_USERNAME=%s OS_PASSWORD=%s ' % (self.control_node().internal_ip, glance_user['tenant'], glance_user['name'], glance_user['password'])
        for image in self.description.get('images', []):
            glance_cmd = env_string + 'glance image-create --name "%s" --is-public true --container-format %s --disk-format %s --copy-from %s' % (image['name'], image.get('container_format', 'bare'), image.get('disk-format', 'raw'), image['url'])
            run(glance_cmd)

    def install_and_configure_puppet(self):
        self._configure_fabric_for_build_node()
        build_node = self.build_node()
        sudo('echo %s %s %s | tee --append /etc/hosts' % (build_node.internal_ip, build_node.fqdn, build_node.name))
        if 'manifest' in self.description:
            manifest_dir = utils.build_manifest_dir(self.description['manifest'],
                                                   {'job': self,
                                                    'config': Configuration.get(),
                                                    'nodes': self.nodes()})
            utils.put_recursive(manifest_dir, self.description['manifest'].get('destdir', '/etc/puppet/manifests'))

        for archive in self.description['archives']:
            sudo('apt-get install -y python-software-properties')
            sudo('add-apt-repository "%s"' % (archive['line'],))
            if 'key_data' in archive:
                with tempfile.NamedTemporaryFile() as tmpfile:
                    remote_name = '%s.key' % (archive['name'],)
                    tmpfile.write(archive['key_data'])
                    tmpfile.flush()
                    put(tmpfile.name, remote_name)
                    sudo('apt-key add %s' % (remote_name,))
            elif 'key_id' in archive:
                sudo('apt-key adv --keyserver keyserver.ubuntu.com --recv-keys %s' % (archive['key_id'],))
            if archive.get('proxy', False):
                parts = archive['line'].split(' ')
                if parts[0] == 'deb':
                    parsed_url = urlparse.urlparse(parts[1])
                    host = parsed_url.hostname
                    sudo('echo \'Acquire::http::Proxy::%s "%s";\' > /etc/apt/apt.conf.d/99proxy-%s.conf' % (host, archive['proxy'], archive['name']))

        sudo('apt-get update')
        sudo('apt-get install -y openssh-server puppetmaster-passenger puppet puppet-openstack-cisco')
        sudo('puppet apply /etc/puppet/manifests/site.pp')
        sudo('puppet agent -t || true')
        sudo("grep -q -- fence.*-z /etc/cobbler/power/power_ucs.template || sed -e '/fence/ s/$/ -z/' -i /etc/cobbler/power/power_ucs.template")


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
    job = models.ForeignKey(Job, blank=True, null=True)

    def __unicode__(self):
        return self.name

    def fqdn(self):
        return '%s.%s' % (self.name, Configuration.get().domain)

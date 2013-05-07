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
import tempfile
import urlparse

from subprocess import Popen
from time import sleep, time

from django.core.management.base import BaseCommand
from django.template import Context, Template
from fabric.api import env as fabric_env
from fabric.api import run, local, sudo, put

from greenfan import utils
from greenfan.models import Configuration, Job, Server

def run_cmd(args):
    proc = Popen(args)
    return proc.communicate()

format_string = '%-35s %-20s %-20s %-20s %s'

def header():
    print format_string % ('fqdn', 'IP', 'MAC', 'HW Profile', '')

def describe_node(node, extra_info=''):
    print format_string % (node.fqdn(), node.ip, node.mac, node.hardware_profile, extra_info)

class Command(BaseCommand):
    def handle(self, job_id, **options):
        job = Job.objects.get(id=job_id)
        config = Configuration.get()
        job.redirect_output()

        print 'General config: '
        print 'Subnet      :', config.subnet
        print 'Netmask     :', config.netmask
        print 'Domain      :', config.domain
        print 'Gateway     :', config.gateway
        print 'NTP servers :', config.ntp_servers
        print 'Name servers:', config.nameservers
        print 'Proxy       :', config.proxy
        print 'Admin user  :', config.admin_user
        print 'Admin passwd:', config.admin_password
        print
        print 'Job details:'
        print 'Ubuntu version:', job.description['ubuntu_series']
        if 'manifest' in job.description:
            print 'Manifest    :'
            print '  Repository:', job.description['manifest']['git']['repository']
            print '  Branch    :', job.description['manifest']['git']['branch']
            print '  Subdir    :', job.description['manifest']['git'].get('subdir', '.')
        print 'Users and tenants:'
        for tenant in job.description.get('tenants', []):
            print '  Tenant:'
            print '     Name       :', tenant['name']
            print '     Description:', tenant.get('description')

        for user in job.description.get('users', []):
            print '  User:'
            print '     Name    :', user['name']
            print '     Password:', user['password']
            print '     E-mail  :', user.get('email')
            print '     Tenant  :', user['tenant']
            print '     Roles   :', user.get('roles', [])
        
        print 'Images:'
        for image in job.description.get('images', []):
            print '  Image:'
            print '    Name            :', image['name']
            print '    Container format:', image.get('container_format', 'bare')
            print '    Disk format     :', image.get('disk-format', 'raw')
            print '    Source          :', image['url']

        print 'Archive information:'
        for archive in job.description['archives']:
           print '  Archive:'
           print '    Name      :', archive['name']
           print '    Pocket    :', archive['pocket']
           print '    Location  :', archive['location']
           print '    Components:', ' '.join(archive['components'])
           print '    Key ID    :', archive['key_id']
           print '    Line      :', archive['line']
           print '    Proxy     :', archive['proxy']
           print '    Key data  :'
           print '\n'.join(['      %s' % l for l in archive['key_data'].split('\n')])

        print
        print "Participating nodes:"
        header()
        for node in job.nodes():
            extra_info = []
            if node == job.build_node():
                extra_info += ['build node']
            if node == job.control_node():
                extra_info += ['controller node']
            describe_node(node, ', '.join(extra_info))


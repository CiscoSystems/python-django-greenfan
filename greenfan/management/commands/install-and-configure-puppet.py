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
from greenfan.models import Configuration, TestSpecification, Server

def run_cmd(args):
    proc = Popen(args)
    return proc.communicate()

class Command(BaseCommand):
    def handle(self, job_id, **options):
        job = TestSpecification.objects.get(id=job_id)
        config = Configuration.get()

        fabric_env.host_string = '%s@%s' % (config.admin_user, job.build_node().ip)
        fabric_env.password = config.admin_password
        fabric_env.abort_on_prompts = True
        fabric_env.sudo_prefix = 'sudo -H -S -p \'%(sudo_prompt)s\' '
 
        job.description['manifest'] = {'git': {'repository': 'http://github.com/sorenh/folsom-manifests.git',
                                               'branch': 'multi-node-templated',
                                               'subdir': 'manifests'}}
        if 'manifest' in job.description:
           manifest_dir = utils.build_manifest_dir(job.description['manifest'],
                                                   {'job': job,
                                                    'config': Configuration.get(),
                                                    'nodes': job.nodes()})
           utils.put_recursive(manifest_dir, '/etc/puppet/manifests')
       
        for archive in job.description['archives']:
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
        sudo('apt-get install -y puppet-openstack-cisco')
        sudo('puppet apply /etc/puppet/manifests/site.pp')
        sudo('/etc/init.d/puppet start')
        sudo("grep -q -- fence.*-z /etc/cobbler/power/power_ucs.template || sed -e '/fence/ s/$/ -z/' -i /etc/cobbler/power/power_ucs.template")

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

class Command(BaseCommand):
    def handle(self, job_id, **options):
        job = Job.objects.get(id=job_id)
        config = Configuration.get()
        job.redirect_output()

        fabric_env.host_string = '%s@%s' % (config.admin_user, job.build_node().ip)
        fabric_env.password = config.admin_password
        fabric_env.abort_on_prompts = True
        fabric_env.sudo_prefix = 'sudo -H -S -p \'%(sudo_prompt)s\' '
 
        timeout = time() + 60*60
        
        expected_set = set([node.fqdn() for node in job.nodes()])
        while timeout > time():
	    out = sudo('cd /var/lib/puppet/reports ; ls | cat')
            actual_set = set([name.strip() for name in out.split('\n')])
            if actual_set == expected_set:
                return ''
            print 'Not done yet. %d seconds left' % (timeout - time(),)
            self.stdout.flush()
            sleep(5)
        raise Exception('Timed out')

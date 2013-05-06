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
from subprocess import Popen, PIPE, STDOUT
from time import sleep, time

from django.core.management.base import BaseCommand
from django.template.loader import render_to_string
from fabric.api import env as fabric_env
from fabric.api import run, local, sudo
from fabric.exceptions import NetworkError

from greenfan.models import Configuration, Job, Server

def run_cmd(args):
    proc = Popen(args, stdout=PIPE, stderr=STDOUT)
    stdout, stderr = proc.communicate()
    return stdout

class Command(BaseCommand):
    def handle(self, job_id, **options):
        job = Job.objects.get(id=job_id)
        config = Configuration.get()
        job.redirect_output()

        def wait_for_ubuntu_install_to_finish():
            timeout = time() + 60*25
            while time() < timeout:
                output = run_cmd(['sudo', 'cobbler', 'system', 'dumpvars', '--name=%s' % (job.build_node().name,)])
                for l in output.split('\n'):
                    if l.startswith('netboot_enabled') and l.endswith('False'):
                        return True
                print "Not done yet. %s seconds left." % (timeout - time(),)
                self.stdout.flush()
                sleep(5)
            return False
        
        def wait_for_ssh_to_become_available():
            timeout = time() + 60*25
            while time() < timeout:
                try:
                    run('true')
                    return True
                except NetworkError, e:
                    print e
                    self.stdout.flush()
                sleep(5)
            return False

        if not wait_for_ubuntu_install_to_finish():
            return False

        run_cmd(['sudo', 'cobbler', 'system', 'remove', '--name=%s' % (job.build_node().name,)])

        fabric_env.host_string = '%s@%s' % (config.admin_user, job.build_node().ip)
        fabric_env.password = config.admin_password
        fabric_env.abort_on_prompts = True
               
        if not wait_for_ssh_to_become_available():
            return False

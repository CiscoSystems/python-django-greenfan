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
import os
import os.path
from subprocess import Popen
from time import sleep 

from django.core.management.base import BaseCommand
from django.template.loader import render_to_string
from greenfan.models import Configuration, TestSpecification, Server

def run_cmd(args):
    print args
    proc = Popen(args)
    return proc.communicate()

class Command(BaseCommand):
    def handle(self, job_id, **options):
        job = TestSpecification.objects.get(id=job_id)
        config = Configuration.get()

        preseed_path = os.path.join(os.getcwd(), 'preseeds', 'build-node.preseed')

        with open(preseed_path, 'w') as fp:
            fp.write(render_to_string('build-node.preseed.tmpl',
                                      {'config': config}))

        try:
            run_cmd(['sudo', 'cobbler', 'system', 'remove', '--name=%s' % (job.build_node().name,)])
        except:
            pass
        run_cmd(['sudo', 'cobbler', 'system', 'add',
                                '--name=%s' % (job.build_node().name,),
                                '--mac-address=%s' % (job.build_node().mac,),
                                '--profile=%s-x86_64' % (job.description['ubuntu_series'],),
                                '--ip-address=%s' % (job.build_node().ip,),
                                '--dns-name=%s' % (job.build_node().fqdn(),),
                                '--hostname=%s' % (job.build_node().fqdn(),),
                                '--kickstart=%s' % (preseed_path,),
                                '--kopts="netcfg/disable_autoconfig=true '
                                         'netcfg/dhcp_failed=true '
                                         "netcfg/dhcp_options='Configure network manually' "
                                         'netcfg/get_nameservers=%s '
                                         'netcfg/get_ipaddress=%s '
                                         'netcfg/get_netmask=%s '
                                         'netcfg/get_gateway=%s '
                                         'netcfg/confirm_static=true '
                                         'clock-setup/ntp-server=%s '
                                         'partman-auto/disk=%s"' % (config.name_server(),
                                                                    job.build_node().ip,
                                                                    config.netmask,
                                                                    config.gateway,
                                                                    config.ntp_server(),
                                                                    job.build_node().hardware_profile.description['boot_disk']), 
                                '--power-user=%s' % (job.build_node().power_user,),
                                '--power-address=%s' % (job.build_node().power_address,),
                                '--power-pass=%s' % (job.build_node().power_password,),
                                '--power-id=%s' % (job.build_node().power_id,),
                                '--power-type=%s' % (job.build_node().power_type,),])

        run_cmd(['sudo', 'cobbler', 'system', 'edit', '--name=%s' % (job.build_node().name,), '--netboot-enabled=true'])
        run_cmd(['sudo', 'cobbler', 'sync'])
        run_cmd(['sudo', 'cobbler', 'system', 'poweroff', '--name=%s' % (job.build_node().name,)])
	sleep(5)        
        run_cmd(['sudo', 'cobbler', 'system', 'poweron', '--name=%s' % (job.build_node().name,)])

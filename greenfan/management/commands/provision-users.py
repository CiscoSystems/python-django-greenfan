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

        fabric_env.host_string = '%s@%s' % (config.admin_user, job.build_node().ip)
        fabric_env.password = config.admin_password
        fabric_env.abort_on_prompts = True
        fabric_env.sudo_prefix = 'sudo -H -S -p \'%(sudo_prompt)s\' '
 
        from keystoneclient.v2_0 import client
        keystone = client.Client(token='keystone_admin_token', endpoint='http://%s:35357/v2.0' % (job.control_node().ip,))
        role_info = {}
        for role in keystone.roles.list():
            role_info[role.name] = role

        tenant_info = dict((tenant.name, tenant) for tenant in keystone.tenants.list())
        if 'tenants' in job.description:
            tenants = job.description['tenants']
            for tenant in tenants:
                if tenant['name'] in tenant_info:
                    continue
                tenant_obj = keystone.tenants.create(tenant_name=tenant['name'], description=tenant.get('description', tenant['name']), enabled=True)
                tenant_info[tenant['name']] = tenant_obj

        user_info = dict((user.name,user) for user in keystone.users.list())
        if 'users' in job.description:
            users = job.description['users']
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

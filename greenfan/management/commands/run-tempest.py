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
from StringIO import StringIO

from subprocess import Popen
from time import sleep, time

from django.core.management.base import BaseCommand
from django.template import Context, Template
from fabric.api import env as fabric_env
from fabric.api import run, local, sudo, put, get

import glanceclient
from keystoneclient.v2_0 import client as ksclient

from greenfan import utils
from greenfan.models import Configuration, TestSpecification, Server

tempest_default_overrides = {}

def get_ksclient(username, password, tenant_name, auth_url):
    return ksclient.Client(username=username,
                           password=password,
                           tenant_name=tenant_name,
                           auth_url=auth_url)

def get_glance_connection(username, password, tenant_name, auth_url):
    ksc = get_ksclient(username, password, tenant_name, auth_url)
    endpoint = ksc.service_catalog.url_for(service_type='image',
                                           endpoint_type='publicURL')
    token = ksc.auth_token   
    endpoint = endpoint[:-(len('v1/')-1)]
    return glanceclient.Client('1', endpoint, token=token)
    
class Command(BaseCommand):
    def handle(self, job_id, **options):
        job = TestSpecification.objects.get(id=job_id)
        config = Configuration.get()

        fabric_env.host_string = '%s@%s' % (config.admin_user, job.control_node().ip)
        fabric_env.password = config.admin_password
        fabric_env.abort_on_prompts = True
        fabric_env.sudo_prefix = 'sudo -H -S -p \'%(sudo_prompt)s\' '
 
        # This is crude and horrible
        admin_user = job.description['users'][0]
        non_priv_user1 = job.description['users'][1]
        non_priv_user2 = job.description['users'][2]
        tempest_default_overrides['ALL'] = {'username' : non_priv_user1['name'],
                                            'tenant_name': non_priv_user1['tenant'],
                                            'password': non_priv_user1['password'],
                                            'alt_username' : non_priv_user2['name'],
                                            'alt_tenant_name': non_priv_user2['tenant'],
                                            'alt_password': non_priv_user2['password']}
        tempest_default_overrides['identity-admin'] = {'username' : admin_user['name'],
                                                      'tenant_name': admin_user['tenant'],
                                                      'password': admin_user['password']}
        tempest_default_overrides['compute-admin'] = tempest_default_overrides['identity-admin']
                                                     
                                                    
        
        glance = get_glance_connection(username=non_priv_user1['name'],
                                       password=non_priv_user1['password'],
                                       tenant_name=non_priv_user1['tenant'],
                                       auth_url='http://%s:5000/v2.0/' % (job.control_node().ip))
        print list(glance.images.list())
        image = list(glance.images.list(name=job.description['images'][0]['name']))[0]

        if not 'ALL' in tempest_default_overrides:
            tempest_default_overrides['ALL'] = {}

        tempest_default_overrides['ALL']['image_ref'] = image.id
        tempest_default_overrides['ALL']['image_ref_alt'] = image.id
        sudo('apt-get -y install git python-unittest2')
#        run('git clone https://github.com/CiscoSystems/tempest')
      
        conf_sample = StringIO()
        get('tempest/etc/tempest.conf.sample', conf_sample)
        
        out = ''
        for l in conf_sample.getvalue().split('\n'):
            if l.startswith('['):
                section = l[1:-1]
            elif l.strip() == '':
                pass
            elif l.startswith('#'):
                pass
            else:
                k, v = l.split('=')
                k, v = k.strip(), v.strip()
                if section in tempest_default_overrides and k in tempest_default_overrides[section]:
                    v = tempest_default_overrides[section][k]
                elif 'ALL' in tempest_default_overrides and k in tempest_default_overrides['ALL']:
                    v = tempest_default_overrides['ALL'][k]
                l = "%s = %s" % (k, v)
            out += "%s\n" % (l,)

        put(StringIO(out), 'tempest/etc/tempest.conf')
        run('cd tempest ; nosetests -v tempest')

#        glance_user = job.description['users'][0]
#        env_string = 'OS_AUTH_URL=http://%s:5000/v2.0 OS_TENANT_NAME=%s OS_USERNAME=%s OS_PASSWORD=%s ' % (job.control_node().ip, glance_user['tenant'], glance_user['name'], glance_user['password'])
#        run(env_string + 'glance image-create --name "precise" --is-public true --container-format bare --disk-format raw --copy-from http://cloud-images.ubuntu.com/precise/current/precise-server-cloudimg-amd64-disk1.img')

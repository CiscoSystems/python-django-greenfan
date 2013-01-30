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

format_string = '%-35s %-20s %-20s %s'

def header():
    print format_string % ('fqdn', 'IP', 'MAC', '')

def describe_node(node, extra_info=''):
    print format_string % (node.fqdn(), node.ip, node.mac, extra_info)

class Command(BaseCommand):
    def handle(self, job_id, **options):
        job = TestSpecification.objects.get(id=job_id)
        config = Configuration.get()

        print "Participating nodes:"
        header()
        for node in job.nodes():
            extra_info = []
            if node == job.build_node():
                extra_info += ['build node']
            if node == job.control_node():
                extra_info += ['controller node']
            describe_node(node, ', '.join(extra_info))


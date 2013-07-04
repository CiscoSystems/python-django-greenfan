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
        job.redirect_output()
        job.wait_for_non_build_nodes()


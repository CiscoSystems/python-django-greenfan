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
import shutil

from subprocess import Popen, PIPE

from django.core.management.base import BaseCommand
from greenfan.models import TestSpecification


def run_cmd(args, capture_stdout=True):
    if capture_stdout:
        kwargs = {'stdout': PIPE}
    else:
        kwargs = {}
    proc = Popen(args, **kwargs)
    return proc.communicate()


class Command(BaseCommand):
    def handle(self, job_id, **options):
        job = TestSpecification.objects.get(id=job_id)

        if job.log_listener_dir:
            with open(os.path.join(job.log_listener_dir, 'pid'), 'r') as fp:
                pid = int(fp.read())
            os.kill(pid, 2)

            with open(os.path.join(job.log_listener_dir, 'tail.pid'), 'r') as fp:
                pid = int(fp.read())
            os.kill(pid, 2)

            shutil.rmtree(job.log_listener_dir)

        job.log_listener_dir = None
        job.save()

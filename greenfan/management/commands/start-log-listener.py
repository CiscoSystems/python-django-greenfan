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
import re
import tempfile
import time

from subprocess import Popen, PIPE

from django.core.management.base import BaseCommand
from django.template.loader import render_to_string

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
        try:
            job = TestSpecification.objects.get(id=job_id)

            ports_in_use = set()
            stdout, stderr = run_cmd(['netstat', '-lun'])
            for l in stdout.split('\n')[2:]:
                parts = re.split('\s+', l, 4)
                if len(parts) != 5:
                    continue
                _, __, ___, local, ____ = parts
                port = local.split(':')[-1]
                ports_in_use.add(int(port))

            for port in range(59000, 60000):
                if port not in ports_in_use:
                     break

            job.log_listener_port = port

            tmpdir = tempfile.mkdtemp()
            rsyslog_conf_file = os.path.join(tmpdir, 'rsyslog.conf')
            rsyslog_log_file = os.path.join(tmpdir, 'logfile')
            rsyslog_pid_file = os.path.join(tmpdir, 'pid')
            tail_pid_file = os.path.join(tmpdir, 'tail.pid')

            with open(rsyslog_conf_file, 'w') as fp:
                fp.write(render_to_string('rsyslog.conf',
                                          {'port': port,
                                           'logfile': rsyslog_log_file}))

            # 'strace', '-o', '/tmp/nc.log', '-f', 
            rsyslog = Popen(['/usr/sbin/rsyslogd', '-c5', '-f', rsyslog_conf_file, '-i', rsyslog_pid_file])
            job.log_listener_dir = tmpdir

            # Let rsyslog start and create the file
            time.sleep(1)
            proc = Popen(['tail', '-f', rsyslog_log_file])

            with open(tail_pid_file, 'w') as fp:
                fp.write(str(proc.pid))
            
            job.save()
        finally:
            pass

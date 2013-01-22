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
from glob import glob
import os
import shutil
from subprocess import Popen, PIPE
import tempfile

from django.template import Context, Template

from fabric.api import run, local, sudo, put
import paramiko

def run_cmd(args, capture_stdout=False):
    if capture_stdout:
        kwargs = {'stdout': PIPE}
    else:
        kwargs = {}
    proc = Popen(args, **kwargs)
    return proc.communicate()


def run_cmd_over_ssh(username, address, cmd, input=None, output_callback=lambda x:None):
    out = ''
    for data in run_cmd_over_ssh_streaming(username, address, cmd, input):
        output_callback(data)
        out += data

    return out

def run_cmd_over_ssh_streaming(username, address, cmd, input=None):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(address, username=username, pkey=self.paramiko_private_key)

    transport = ssh.get_transport()

    chan = transport.open_session()
    chan.exec_command(cmd)
    chan.set_combine_stderr(True)
    if input:
        chan.sendall(input)
        chan.shutdown_write()

    while True:
        r, _, __ = select.select([chan], [], [], 1)
        if r:
            if chan in r:
                if chan.recv_ready():
                    s = chan.recv(4096)
                    if len(s) == 0:
                        break
                    yield s
                else:
                    status = chan.recv_exit_status()
                    if status != 0:
                        raise Exception('Command %s failed' % cmd)
                    break

    ssh.close()

def git_cmd_from_git_info(git_info, tmpdir):
    cmd = ['git', 'clone']
    cmd += [git_info['repository']]
    if 'branch' in git_info:
        cmd += ['-b', git_info['branch']]
    checkout_dir = os.path.join(tmpdir, 'checkout')
    cmd += [checkout_dir]
    return cmd


def render(src, dst, context):
    with file(src, 'r') as fp:
        tmpl = Template(fp.read())
    with file(dst, 'w') as fp:
        fp.write(tmpl.render(context))


def render_template_recursive(src, dst, context, topdir=None):
    context = Context(context)
    return _render_template_recursive(src, dst, context)


def _render_template_recursive(src, dst, context, topdir=None):
    if not topdir:
        if os.path.isdir(src):
           if src.endswith('/'):
               src = src[:len(src)-1]
           topdir = src
        else:
           topdir = os.path.dirname(src)

    dstpath = os.path.join(dst, src[len(topdir)+1:])

    if os.path.isdir(src):
        dstpath = dstpath[:len(dstpath)]
        dstpath = dstpath.rstrip('/')
        if not os.path.exists(dstpath):
            os.mkdir(dstpath)
    	for f in glob(os.path.join(src, '*')):
            _render_template_recursive(f, dst, context, topdir)
    else:
        render(src, dstpath, context)

def put_recursive(src, dst, topdir=None):
    if not topdir:
        if os.path.isdir(src):
           if src.endswith('/'):
               src = src[:len(src)-1]
           topdir = src
        else:
           topdir = os.path.dirname(src)

    dstpath = os.path.join(dst, src[len(topdir)+1:])

    if os.path.isdir(src):
        dstpath = dstpath[:len(dstpath)]
        dstpath = dstpath.rstrip('/')
        sudo('mkdir -p %s' % (dstpath,))
    	for f in glob(os.path.join(src, '*')):
            put_recursive(f, dst, topdir)
    else:
        put(src, dstpath, use_sudo=True)
        
def generate_manifests_from_git(git_info, tmpdir, outdir, context):
    cmd = git_cmd_from_git_info(git_info, tmpdir)
    run_cmd(cmd)
    subdir = git_info.get('subdir', '.')
    srcdir = os.path.join(tmpdir, 'checkout', subdir)
    render_template_recursive(srcdir, outdir, context)

def build_manifest_dir(manifest_info, context):
    tmpdir = tempfile.mkdtemp()
    manifest_dir = tempfile.mkdtemp()
    
    if 'content' in manifest_info:
        template = Template(manifest_info['content'])
        sitepp = os.path.join(manifest_dir, 'site.pp')
        with file(sitepp, 'w') as fp:
            fp.write(template.render(Context(context)))
    elif 'git' in manifest_info:
        generate_manifests_from_git(manifest_info['git'], tmpdir, manifest_dir, context)
    shutil.rmtree(tmpdir)
    return manifest_dir

def src_ip(dest_ip='8.8.8.8'):
    stdout, stderr = run_cmd(['ip', '-o', 'route', 'get', dest_ip], capture_stdout=True)
    parts = stdout.split(' ')
    return parts[parts.index('src')+1]

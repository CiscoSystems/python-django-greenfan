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

import crypt
import mock
import os
import shutil
import tempfile
import textwrap
from StringIO import StringIO

from django.core import management
from django.test import TestCase

from greenfan import models
from greenfan import utils

class UtilsTest(TestCase):
    def test_render_recursive(self):
        srcdir = tempfile.mkdtemp()
        dstdir = tempfile.mkdtemp()
        try:
            with file('%s/file1' % (srcdir,), 'w') as fp:
                fp.write('{{ foo }}')
            with file('%s/file2' % (srcdir,), 'w') as fp:
                fp.write('{{ bar }}')
            os.mkdir('%s/dir1' % (srcdir,))
            with file('%s/dir1/file3' % (srcdir,), 'w') as fp:
                fp.write('{{ baz }}')

            utils.render_template_recursive('%s/' % (srcdir,),
                                            dstdir, {'foo': 'data1',
                                                     'bar': 'data2',
                                                     'baz': 'data3'})

            self.assertTrue(os.path.exists('%s/file1' % (dstdir,)))
            self.assertTrue(os.path.exists('%s/file2' % (dstdir,)))
            self.assertTrue(os.path.exists('%s/dir1' % (dstdir,)))
            self.assertTrue(os.path.exists('%s/dir1/file3' % (dstdir,)))

            with open('%s/file1' % (dstdir,), 'r') as fp:
                self.assertEquals(fp.read(), 'data1')

            with open('%s/file2' % (dstdir,), 'r') as fp:
                self.assertEquals(fp.read(), 'data2')

            with open('%s/dir1/file3' % (dstdir,), 'r') as fp:
                self.assertEquals(fp.read(), 'data3')

        finally:
            shutil.rmtree(srcdir)
            shutil.rmtree(dstdir)

    def test_put_recursive(self):
        tmpdir = tempfile.mkdtemp()
        try:
            with file('%s/file1' % (tmpdir,), 'w') as fp:
                fp.write('file1 contents')
            with file('%s/file2' % (tmpdir,), 'w') as fp:
                fp.write('file2 contents')
            os.mkdir('%s/dir1' % (tmpdir,))
            with file('%s/dir1/file3' % (tmpdir,), 'w') as fp:
                fp.write('file3 contents')
            with mock.patch.multiple('greenfan.utils',
                                     put=mock.DEFAULT, sudo=mock.DEFAULT) as mocks:
                put, sudo = mocks['put'], mocks['sudo']

                # This is needed to check the order in which put calls were
                # made relative to sudo calls
                manager = mock.MagicMock()
                manager.attach_mock(put, 'put')
                manager.attach_mock(sudo, 'sudo')

                utils.put_recursive('%s/' % (tmpdir,), '/dst/dir')

                self.assertEquals(put.call_count, 3)

                topdir_mkdir = mock.call.sudo('mkdir -p /dst/dir')
                dir1_mkdir = mock.call.sudo('mkdir -p /dst/dir/dir1')
                file1_put = mock.call.put('%s/file1' % (tmpdir,), '/dst/dir/file1', use_sudo=True)
                file2_put = mock.call.put('%s/file2' % (tmpdir,), '/dst/dir/file2', use_sudo=True)
                file3_put = mock.call.put('%s/dir1/file3' % (tmpdir,), '/dst/dir/dir1/file3', use_sudo=True)

                self.assertIn(file1_put, manager.mock_calls)

                # Some ordering must be in place
                self.assertTrue(manager.mock_calls.index(topdir_mkdir) < manager.mock_calls.index(file1_put))
                self.assertTrue(manager.mock_calls.index(topdir_mkdir) < manager.mock_calls.index(file2_put))
                self.assertTrue(manager.mock_calls.index(topdir_mkdir) < manager.mock_calls.index(dir1_mkdir))
                self.assertTrue(manager.mock_calls.index(dir1_mkdir) < manager.mock_calls.index(file3_put))

                self.assertEquals(put.call_count, 3)
                self.assertEquals(sudo.call_count, 2)
        finally:
            shutil.rmtree(tmpdir)

    def test_git_cmd_from_git_info(self):
        git_info = {'repository': 'git://example.com/foo.git'}
        self.assertEquals(utils.git_cmd_from_git_info(git_info, 'temp'),
                          ['git', 'clone', 'git://example.com/foo.git', 'temp/checkout'])

    def test_git_cmd_from_git_info_with_branch(self):
        git_info = {'repository': 'git://example.com/foo.git',
                    'branch': 'other'}
        self.assertEquals(utils.git_cmd_from_git_info(git_info, 'temp'),
                          ['git', 'clone', 'git://example.com/foo.git', '-b', 'other', 'temp/checkout'])

    def _test_run_cmd_no_capture(self, returned, echoed, capture):
        r, w = os.pipe()
        orig_stdout = os.dup(1)
        os.dup2(w, 1)
        os.close(w)
        try:
            self.assertEquals(utils.run_cmd(['echo', 'foo'],
                                            capture_stdout=capture),
                              (returned, None))
        finally:
            os.dup2(orig_stdout, 1)
            os.close(orig_stdout)
        self.assertEquals(os.fdopen(r, 'r').read(), echoed)

    def test_run_cmd_no_capture(self):
        self._test_run_cmd_no_capture(None, 'foo\n', capture=False)

    def test_run_cmd_capture(self):
        self._test_run_cmd_no_capture('foo\n', '', capture=True)


class ModelTests(TestCase):
    fixtures = ['test_nodes.yaml']

    def test_server_str(self):
        node = models.Server.objects.get(id=1)
        self.assertEquals('%s' % node, 'pod4node1')

    def test_server_fqdn(self):
        node = models.Server.objects.get(id=1)
        self.assertEquals(node.fqdn(), 'pod4node1.example.com')

    def _test_nodeset(self, nodesspec, expected_servers):
        description = {}
        if nodesspec:
            description['nodes'] = nodesspec

        testspec = models.TestSpecification(name='all', description=description)

        self.assertEquals(set(node.name for node in testspec.nodes()),
                          set(expected_servers))

    def test_testspec_nodes_no_filters(self):
        self._test_nodeset(None, ['pod4node1', 'pod4node2',
                                  'pod5node1', 'pod5node2'])

    def test_testspec_nodes_exclude(self):
        self._test_nodeset({'exclude': 'rack'}, ['pod4node1', 'pod4node2'])

    def test_testspec_nodes_include(self):
        self._test_nodeset({'include': 'rack'}, ['pod5node1', 'pod5node2'])

    def test_testspec_nodes_include_and_exclude(self):
        self._test_nodeset({'include': 'rack',
                            'exclude': '1nic'}, ['pod5node1'])

    def test_testspec_build_node_not_control_node(self):
        testspec = models.TestSpecification(name='all', description={})
        self.assertNotEquals(testspec.build_node(), testspec.control_node())

    def test_testspec_build_node_not_in_non_build_nodes(self):
        testspec = models.TestSpecification(name='all', description={})
        build_node = testspec.build_node()
        non_build_nodes = testspec.non_build_nodes()
        self.assertNotIn(build_node, non_build_nodes)

    def test_testspec_build_node_plus_non_build_nodes_equals_all_nodes(self):
        testspec = models.TestSpecification(name='all', description={})
        all_nodes = testspec.nodes()
        build_node = testspec.build_node()
        non_build_nodes = testspec.non_build_nodes()
        self.assertEquals(set(all_nodes), set([build_node] + non_build_nodes))

    def test_testspec_build_node_and_control_node_not_in_compute_nodes(self):
        testspec = models.TestSpecification(name='all', description={})
        build_node = testspec.build_node()
        control_node = testspec.control_node()
        compute_nodes = testspec.compute_nodes()
        self.assertNotIn(build_node, compute_nodes)
        self.assertNotIn(control_node, compute_nodes)

    def test_testspec_dhcp_low_and_high(self):
        testspec = models.TestSpecification(name='all', description={})

        self.assertEquals(testspec.dhcp_low(), '10.10.4.1')
        self.assertEquals(testspec.dhcp_high(), '10.10.5.2')

        # Reverse the list
        nodes = testspec.nodes()
        nodes.reverse()
        testspec.nodes = lambda: nodes
        self.assertEquals(testspec.dhcp_low(), '10.10.4.1')
        self.assertEquals(testspec.dhcp_high(), '10.10.5.2')

    def test_testspec_logging(self):
        testspec = models.TestSpecification(name='all', description={}, log_listener_port=9876)
        with mock.patch('greenfan.models.utils.run_cmd') as run_cmd:
            run_cmd.return_value = ('1.2.3.4 dev vmnet1  src 10.30.1.1 \    cache', '')
            self.assertEquals(testspec.logging(),
                              {'port': 9876,
                               'host': '10.30.1.1'})

    def test_testspec_json_description(self):
        testspec = models.TestSpecification(name='all', description=[{'foo': 'bar'}, 1, "foo"])
        self.assertEquals(testspec.json_description(),
                          textwrap.dedent("""\
                             [
                               {
                                 "foo": "bar"
                               }, 
                               1, 
                               "foo"
                             ]"""))

    def test_configuration_save_new_conf_overrides_old(self):
        self.assertEquals(models.Configuration.objects.count(), 1)

        conf = models.Configuration.objects.all()[0]
        conf.pk = None
        conf.domain = 'somethingelse.com'
        conf.save()

        self.assertEquals(models.Configuration.objects.count(), 1)
        conf = models.Configuration.get()
        self.assertEquals(conf.domain, 'somethingelse.com')

    def test_configuration_save_raises_if_multiple_confs(self):
        self.assertEquals(models.Configuration.objects.count(), 1)
        conf = models.Configuration.objects.all()[0]
        conf.pk = None

        super(models.Configuration, conf).save()
        self.assertEquals(models.Configuration.objects.count(), 2)

        self.assertRaises(Exception, conf.save)

    def test_configuration_name_server_list(self):
        conf = models.Configuration.get()
        self.assertEquals(conf.name_server_list(), ['10.20.2.1', '10.20.2.2'])

    def test_configuration_name_server(self):
        conf = models.Configuration.get()
        self.assertEquals(conf.name_server(), '10.20.2.1')

    def test_configuration_ntp_server_list(self):
        conf = models.Configuration.get()
        self.assertEquals(conf.ntp_server_list(), ['10.20.1.1', '10.20.1.2'])

    def test_configuration_ntp_server(self):
        conf = models.Configuration.get()
        self.assertEquals(conf.ntp_server(), '10.20.1.1')

    def test_configuration_admin_password_crypted(self):
        conf = models.Configuration.get()
        crypted_password = conf.admin_password_crypted()
        self.assertEquals(crypted_password[:3], '$6$', "Is not a sha512sum")
        self.assertEquals(crypt.crypt(conf.admin_password, crypted_password), crypted_password) 

    def test_subnet_as_sql(self):
        conf = models.Configuration.get()

        conf.subnet = '10.20.30.0'
        conf.netmask = '255.255.255.0'
        self.assertEquals(conf.subnet_as_sql(), '10.20.30.%')

        conf.subnet = '10.20.30.0'
        conf.netmask = '255.255.0.0'
        self.assertEquals(conf.subnet_as_sql(), '10.20.%.%')

        conf.subnet = '10.20.30.0'
        conf.netmask = '255.0.0.0'
        self.assertEquals(conf.subnet_as_sql(), '10.%.%.%')

        conf.subnet = '10.20.30.0'
        conf.netmask = '255.128.0.0'
        self.assertEquals(conf.subnet_as_sql(), '10.%.%.%')

    def test_hardwareprofiletag_str(self):
        blade = models.HardwareProfileTag.objects.get(name='blade')
        self.assertEquals('%s' % (blade,), 'blade')

    def test_hardwareprofile_str(self):
        hwp = models.HardwareProfile.objects.get(name='B-series')
        self.assertEquals('%s' % (hwp,), 'B-series')

    def test_hardwareprofile_description(self):
        hwp = models.HardwareProfile(name='foo', description=[{'foo': 'bar'}, 1, "foo"])
        self.assertEquals(hwp.json_description(),
                          textwrap.dedent("""\
                             [
                               {
                                 "foo": "bar"
                               }, 
                               1, 
                               "foo"
                             ]"""))


class CommandsTests(TestCase):
    fixtures = ['test_nodes.yaml', 'test_testspec.yaml']

    def test_reboot_non_build_nodes(self):
        from fabric.api import env as fabric_env

        expected_calls = [
                    'cobbler system find --netboot-enabled=true',
                    'timeout 10 cobbler system poweroff --name=foo',
                    'timeout 10 cobbler system poweroff --name=bar',
                    'timeout 10 cobbler system poweron --name=foo',
                    'timeout 10 cobbler system poweron --name=bar']

        def faked_responses(cmd):
            if cmd == 'cobbler system find --netboot-enabled=true':
                return 'foo\nbar\n'
            else:
                return ''

        with mock.patch('fabric.api.sudo', side_effect=faked_responses) as sudo:
            with mock.patch('time.sleep') as sleep:
                management.call_command('reboot-non-build-nodes', '1')

                for call in expected_calls:
                    sudo.assert_any_call(call)

                sleep.assert_called_with(5)
        self.assertEquals(fabric_env.host_string, 'adminuser@10.10.4.1')
        self.assertEquals(fabric_env.password, 'adminpass')
        self.assertEquals(fabric_env.abort_on_prompts, True)
        self.assertEquals(fabric_env.sudo_prefix, 'sudo -H -S -p \'%(sudo_prompt)s\' ')

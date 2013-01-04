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
"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

import mock
import os
import shutil
import tempfile

from django.test import TestCase

from greenfan import utils

class SimpleTest(TestCase):
    def test_basic_addition(self):
        """
        Tests that 1 + 1 always equals 2.
        """
        self.assertEqual(1 + 1, 2)

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

            utils.render_template_recursive(srcdir, dstdir, {'foo': 'data1',
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

                utils.put_recursive(tmpdir, '/dst/dir')

                self.assertEquals(put.call_count, 3)

                topdir_mkdir = mock.call.sudo('mkdir -p /dst/dir')
                dir1_mkdir = mock.call.sudo('mkdir -p /dst/dir/dir1')
                file1_put = mock.call.put('%s/file1' % (tmpdir,), '/dst/dir/file1')
                file2_put = mock.call.put('%s/file2' % (tmpdir,), '/dst/dir/file2')
                file3_put = mock.call.put('%s/dir1/file3' % (tmpdir,), '/dst/dir/dir1/file3')

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

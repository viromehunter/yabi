# Yabi - a sophisticated online research environment for Grid, High Performance and Cloud computing.
# Copyright (C) 2015  Centre for Comparative Genomics, Murdoch University.
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
# 
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import unittest
from .support import YabiTestCase, StatusResult, FileUtils
from .fixture_helpers import admin
import os
import tarfile
from six.moves import filter
import logging

from yabi.yabi import models

ONE_GB = 1 * 1024 * 1024 * 1024

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class FileUploadTest(YabiTestCase, FileUtils):

    def setUp(self):
        YabiTestCase.setUp(self)
        FileUtils.setUp(self)
        admin.create_tool_cksum(testcase=self)

    def tearDown(self):
        YabiTestCase.tearDown(self)
        FileUtils.tearDown(self)

    def test_cksum_of_large_file(self):
        FILESIZE = ONE_GB / 1024
        filename = self.create_tempfile(size=FILESIZE)
        result = self.yabi.run(['cksum', filename])
        self.assertTrue(result.status == 0, "Yabish command shouldn't return error!")

        expected_cksum, expected_size = self.run_cksum_locally(filename)

        returned_lines = list(filter(lambda l: l.startswith(expected_cksum), result.stdout.split("\n")))
        self.assertEqual(len(returned_lines), 1, 'Expected cksum %s result not returned or checksum is incorrect' % expected_cksum)
        our_line = returned_lines[0]
        actual_cksum, actual_size, rest = our_line.split()
        self.assertEqual(expected_cksum, actual_cksum)
        self.assertEqual(expected_size, actual_size)


class FileUploadAndDownloadTest(YabiTestCase, FileUtils):

    def setUpAdmin(self):
        admin.create_tool_dd(testcase=self)

    def setUp(self):
        YabiTestCase.setUp(self)
        FileUtils.setUp(self)
        FILESIZE = ONE_GB / 1024
        self.filename = self.create_tempfile(size=FILESIZE)
        logger.debug("temp file {0}".format(self.filename))
        self.setUpAdmin()

    def tearDown(self):
        FileUtils.tearDown(self)
        YabiTestCase.tearDown(self)

    def test_dd(self):
        self._test_dd()

    def test_nolink_nolcopy(self):
        dd = models.Tool.objects.get(desc__name='dd')
        dd.lcopy_supported = False
        dd.link_supported = False
        dd.save()
        self._test_dd()

    def test_nolink_lcopy(self):
        dd = models.Tool.objects.get(desc__name='dd')
        dd.lcopy_supported = True
        dd.link_supported = False
        dd.save()
        self._test_dd()

    def test_link_nolcopy(self):
        dd = models.Tool.objects.get(desc__name='dd')
        dd.lcopy_supported = False
        dd.link_supported = True
        dd.save()
        self._test_dd()

    def _test_dd(self):
        logger.debug("dd if={0} of=output_file".format(self.filename))
        result = self.yabi.run(['dd', 'if=%s'%self.filename, 'of=output_file'])
        self.assertEqual(result.status, 0, "Yabish command shouldn't return error!")

        logger.debug("performing checksum")
        expected_cksum, expected_size = self.run_cksum_locally(self.filename)
        copy_cksum, copy_size = self.run_cksum_locally('output_file')
        if os.path.isfile('output_file'):
            os.unlink('output_file')

        self.assertEqual(expected_size, copy_size)
        self.assertEqual(expected_cksum, copy_cksum)

class FileUploadSmallFilesTest(YabiTestCase, FileUtils):

    def setUpAdmin(self):
        admin.create_tool('tar', testcase=self)
        admin.add_tool_to_all_tools('tar')
        tool = models.ToolDesc.objects.get(name='tar')
        tool.accepts_input = True

        value_only = models.ParameterSwitchUse.objects.get(display_text='valueOnly')
        both = models.ParameterSwitchUse.objects.get(display_text='both')
        switch_only = models.ParameterSwitchUse.objects.get(display_text='switchOnly')

        tool_param_c = models.ToolParameter.objects.create(tool=tool, rank=1, switch_use=switch_only, file_assignment = 'none', switch='-c')
        tool_param_f = models.ToolParameter.objects.create(tool=tool, rank=2, switch_use=both, file_assignment = 'none', output_file=True, switch='-f')
        all_files = models.FileType.objects.get(name='all files')
        tool_param_f.accepted_filetypes.add(all_files)
        tool_param_files = models.ToolParameter.objects.create(tool=tool, switch_use=value_only, rank=99, file_assignment = 'all', switch='files')
        tool_param_files.accepted_filetypes.add(all_files)

        tool.save()

    def setUp(self):
        YabiTestCase.setUp(self)
        FileUtils.setUp(self)
        self.delete_output_file()
        self.setUpAdmin()

    def tearDown(self):
        YabiTestCase.tearDown(self)
        FileUtils.tearDown(self)
        self.delete_output_file()

    def delete_output_file(self):
        if os.path.exists('file_1_2_3.tar'):
            os.unlink('file_1_2_3.tar')

    def test_tar_on_a_few_files(self):
        MB = 1024 * 1024
        dirname = self.create_tempdir() + "/"
        file1 = self.create_tempfile(size=1 * MB, parentdir=dirname)
        file2 = self.create_tempfile(size=2 * MB, parentdir=dirname)
        file3 = self.create_tempfile(size=3 * MB, parentdir=dirname)
        files = dict([(os.path.basename(f), f) for f in (file1, file2, file3)])

        result = self.yabi.run(['tar', '-c', '-f', 'file_1_2_3.tar', dirname])
        self.assertTrue(result.status == 0, "Yabish command shouldn't return error!")

        extract_dirname = self.create_tempdir()
        tar = tarfile.TarFile('file_1_2_3.tar')
        tar.extractall(extract_dirname)

        tarfiles = tar.getnames()
        self.assertEqual(len(tarfiles), 3)
        for extracted_f in tarfiles:
            full_name = os.path.join(extract_dirname, extracted_f)
            self.assertTrue(os.path.basename(extracted_f) in files, '%s (%s) should be in %s' % (os.path.basename(extracted_f), extracted_f, files))
            matching_f = files[os.path.basename(extracted_f)]
            self.compare_files(matching_f, full_name)

    def compare_files(self, file1, file2):
        expected_cksum, expected_size = self.run_cksum_locally(file1)
        actual_cksum, actual_size = self.run_cksum_locally(file2)
        self.assertEqual(expected_cksum, actual_cksum)
        self.assertEqual(expected_size, actual_size)

#
# pip3 install --user pytest
#
# How to run:
# mkdir -p /tmp/dropbox/client
# mkdir -p /tmp/dropbox/server
#
# The following enviroment variables are used to run a client & a server.
# export CLIENT_CMD='python3 -c "import test_homework as th; th.client()" -- hey_client /tmp/dropbox/client /tmp/dropbox/server'
# export SERVER_CMD='python3 -c "import test_homework as th; th.server()" -- hey_client /tmp/dropbox/client /tmp/dropbox/server'
#
# Verbose, with stdout, filter by test name
# pytest -vv -s . -k 'test_some_name'
# Quiet, show summary in the end
# pytest -q -rapP
# Verbose, with stdout, show summary in the end
# pytest -s -vv -q -rapP
#
from sys import argv, stderr, stdout
from glob import glob
from time import sleep
from shutil import copytree, rmtree
from signal import SIGKILL, SIGTERM
from hashlib import md5
from unittest import TestCase, skip
from itertools import chain
from subprocess import Popen, TimeoutExpired
from os import environ, getpgid, killpg, mkdir, remove, setsid, walk
from os.path import exists, getsize, isfile, join, normpath, sep


ASSERT_TIMEOUT = 90.0
ASSERT_STEP = 1.0
SHUTDOWN_TIMEOUT = 10.0

SERVER_PATH = '/tmp/test/server'
CLIENT_PATH = '/tmp/test/client'


def spit(filename, data):
    """Save data into the given filename."""
    with open(filename, 'w') as file_:
        file_.write(data)


def reset_path(path):
    """Remove directory recursively and recreate again (empty)."""
    if exists(path):
        rmtree(path)
    mkdir(path)


def sync_paths(source_path, dest_path):
    """Sync paths so that they contain exactly the same set of files."""
    files = chain(glob(join(dest_path, '*')), glob(join(dest_path, '.*')))
    for filename in files:
        if isfile(filename):
            remove(filename)
        else:
            rmtree(filename)
    if exists(dest_path):
        rmtree(dest_path)
    copytree(source_path, dest_path)


def get_md5(filename):
    if not isfile(filename):
        return '0'
    hash_md5 = md5()
    with open(filename, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def path_content_to_string(path):
    """Convert contents of a directory recursively into a string for easier comparison."""
    lines = []
    prefix_len = len(path + sep)
    for root, dirs, files in walk(path):
        for dir_ in dirs:
            full_path = join(root, dir_)
            relative_path = full_path[prefix_len:]
            size = 0
            type_ = 'dir'
            hash_ = '0'
            line = '{},{},{},{}'.format(relative_path, type_, size, hash_)
            lines.append(line)

        for filename in files:
            full_path = join(root, filename)
            relative_path = full_path[prefix_len:]
            size = getsize(full_path)
            type_ = 'file' if isfile(full_path) else 'dir'
            hash_ = get_md5(full_path)
            line = '{},{},{},{}'.format(relative_path, type_, size, hash_)
            lines.append(line)

    lines = sorted(lines)
    return '\n'.join(lines)


def assert_paths_in_sync(path1, path2, timeout=ASSERT_TIMEOUT, step=ASSERT_STEP):
    current_time = 0
    while current_time < timeout:
        contents1 = path_content_to_string(path1)
        contents2 = path_content_to_string(path2)
        if contents1 == contents2:
            return
        sleep(step)
        current_time += step
    assert contents1 == contents2


def client():
    """Dumbest reference implementation of a client that copies files recursively."""
    print('CLIENT STARTED', argv)
    client_path = argv[-2]
    server_path = argv[-1]
    sync_paths(client_path, server_path)
    while True:
        if path_content_to_string(client_path) != path_content_to_string(server_path):
            print('Client syncing...')
            sync_paths(client_path, server_path)
        print('Client sleeping 1 second')
        sleep(1.0)
    print('CLIENT DONE', argv)


def server():
    """Server reference implementation, does nothing, just for demo purposes."""
    print('SERVER STARTED', argv)
    while True:
        print('Server sleeping 1 second')
        sleep(1.0)
    print('SERVER DONE', argv)


class Process:
    def __init__(self, cmd_line):
        print('Starting ', cmd_line)
        self._process = Popen(cmd_line, shell=True, preexec_fn=setsid,
                              stdout=stdout, stderr=stderr)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.shutdown()

    def shutdown(self):
        killpg(getpgid(self._process.pid), SIGTERM)
        try:
            self._process.wait(SHUTDOWN_TIMEOUT)
        except TimeoutExpired:
            killpg(getpgid(self._process.pid), SIGKILL)
        sleep(2.0)


class TestBasic(TestCase):

    def setUp(self):
        self.spath = SERVER_PATH
        self.cpath = CLIENT_PATH
        reset_path(self.spath)
        reset_path(self.cpath)
        self.server_cmd = environ['SERVER_CMD']
        self.client_cmd = environ['CLIENT_CMD']
        print(self.server_cmd)
        print(self.client_cmd)
        self.server_process = Process(self.server_cmd)
        sleep(1.0)
        self.client_process = Process(self.client_cmd)
        sleep(1.0)
        assert_paths_in_sync(self.cpath, self.spath)

    def tearDown(self):
        self.server_process.shutdown()
        self.client_process.shutdown()

    def test_single_file_completely_changes_3_times(self):
        spit(join(self.cpath, 'newfile.txt'), 'contents')
        assert_paths_in_sync(self.cpath, self.spath)

        spit(join(self.cpath, 'newfile.txt'), 'contents more')
        assert_paths_in_sync(self.cpath, self.spath)

        spit(join(self.cpath, 'newfile.txt'), 'beginning contents more')
        assert_paths_in_sync(self.cpath, self.spath)

        spit(join(self.cpath, 'newfile.txt'), 'new content')
        assert_paths_in_sync(self.cpath, self.spath)

    def test_single_file_change_and_remove(self):
        spit(join(self.cpath, 'newfile.txt'), 'contents')
        assert_paths_in_sync(self.cpath, self.spath)

        remove(join(self.cpath, 'newfile.txt'))
        assert_paths_in_sync(self.cpath, self.spath)

    def test_add_empty_dir(self):
        mkdir(join(self.cpath, 'newemptydir'))
        assert_paths_in_sync(self.cpath, self.spath)

    def test_add_and_remove_empty_dir(self):
        mkdir(join(self.cpath, 'newemptydir'))
        assert_paths_in_sync(self.cpath, self.spath)

        rmtree(join(self.cpath, 'newemptydir'))
        assert_paths_in_sync(self.cpath, self.spath)

    def test_3_new_files_1mb_each_add_instantly(self):
        spit(join(self.cpath, 'file1.txt'), '*' * 10**6)
        spit(join(self.cpath, 'file2.txt'), '*' * 10**6)
        spit(join(self.cpath, 'file3.txt'), '*' * 10**6)
        assert_paths_in_sync(self.cpath, self.spath)

    def test_3_new_files_1mb_each_add_with_delay(self):
        spit(join(self.cpath, 'file1.txt'), '*' * 10**6)
        sleep(1.0)
        spit(join(self.cpath, 'file2.txt'), '*' * 10**6)
        sleep(1.0)
        spit(join(self.cpath, 'file3.txt'), '*' * 10**6)
        assert_paths_in_sync(self.cpath, self.spath)

    def test_single_file_change_1_byte_beginning(self):
        spit(join(self.cpath, 'file1.txt'), '0' + '*' * 10**6)
        sleep(1.0)
        assert_paths_in_sync(self.cpath, self.spath)

        spit(join(self.cpath, 'file1.txt'), '1' + '*' * 10**6)
        sleep(1.0)
        assert_paths_in_sync(self.cpath, self.spath)

    def test_1_empty_file(self):
        spit(join(self.cpath, 'file1.txt'), '')
        assert_paths_in_sync(self.cpath, self.spath)

    def test_3_empty_files_add_instantly(self):
        spit(join(self.cpath, 'file1.txt'), '')
        spit(join(self.cpath, 'file2.txt'), '')
        spit(join(self.cpath, 'file3.txt'), '')
        assert_paths_in_sync(self.cpath, self.spath)

    def test_3_empty_files_add_with_delay(self):
        spit(join(self.cpath, 'file1.txt'), '')
        sleep(1.0)
        spit(join(self.cpath, 'file2.txt'), '')
        sleep(1.0)
        spit(join(self.cpath, 'file3.txt'), '')
        assert_paths_in_sync(self.cpath, self.spath)

    def test_1_file_grows_twice_with_delay(self):
        spit(join(self.cpath, 'file1.txt'), '*' * 10**6)
        assert_paths_in_sync(self.cpath, self.spath)
        sleep(1.0)
        spit(join(self.cpath, 'file1.txt'), '*' * 20**6)
        assert_paths_in_sync(self.cpath, self.spath)

    def test_1_file_shrinks_twice_with_delay(self):
        spit(join(self.cpath, 'file1.txt'), '*' * 20**6)
        assert_paths_in_sync(self.cpath, self.spath)
        sleep(1.0)
        spit(join(self.cpath, 'file1.txt'), '*' * 10**6)
        assert_paths_in_sync(self.cpath, self.spath)


class TestInitialSync(TestCase):

    def setUp(self):
        self.spath = SERVER_PATH
        self.cpath = CLIENT_PATH
        reset_path(self.spath)
        reset_path(self.cpath)
        self.server_cmd = environ['SERVER_CMD']
        self.client_cmd = environ['CLIENT_CMD']
        print(self.server_cmd)
        print(self.client_cmd)

    def test_one_file(self):
        spit(join(self.cpath, 'newfile.txt'), 'contents')

        self.server_process = Process(self.server_cmd)
        sleep(1.0)
        self.client_process = Process(self.client_cmd)
        sleep(1.0)
        assert_paths_in_sync(self.cpath, self.spath)

        self.server_process.shutdown()
        self.client_process.shutdown()

    def test_file_and_empty_dir(self):
        spit(join(self.cpath, 'newfile.txt'), 'contents')
        mkdir(join(self.cpath, 'newemptydir'))

        self.server_process = Process(self.server_cmd)
        sleep(1.0)
        self.client_process = Process(self.client_cmd)
        sleep(1.0)
        assert_paths_in_sync(self.cpath, self.spath)

        self.server_process.shutdown()
        self.client_process.shutdown()

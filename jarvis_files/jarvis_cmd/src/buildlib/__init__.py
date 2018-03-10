import hashlib
import os
import re
import click

from contextlib import contextmanager

from jarvis.core import cd, ensure_dir


class BuildError(Exception):
    pass


class Builder:
    def __init__(self, wksp, dir_, name):
        self.dir_ = dir_
        self.full_path = os.path.join(wksp.root, self.dir_)
        self.name = name

    def _hash_file(self, filepath, algo):
        hasher = algo()
        blocksize = 64 * 1024
        with open(filepath, 'rb') as fp:
            while True:
                data = fp.read(blocksize)
                if not data:
                    break
                hasher.update(data)
        return hasher.hexdigest()

    def _hash_dir(self):
        hash_algo = hashlib.sha256
        assert os.path.isdir(self.full_path)
        intermediate_hashes = []
        for root, dirs, files in os.walk(
                self.full_path, topdown=True, followlinks=False):
            if not re.search(r'/\.', root):
                intermediate_hashes.extend(
                    [
                        self._hash_file(os.path.join(root, f), hash_algo)
                        for f in files
                        if not f.startswith('.') and not re.search(r'/\.', f)
                        and self.is_relevant_file(f)
                    ]
                )
        hasher = hash_algo()
        for hashvalue in sorted(intermediate_hashes):
            hasher.update(hashvalue.encode('utf-8'))
        return hasher.hexdigest()

    def _rebuild_necessary(self):
        hash_file_path = os.path.join(self.wksp.hash_store, self.name)
        saved_hash = b''
        try:
            with open(hash_file_path) as hash_file:
                saved_hash = hash_file.read()
        except:
            pass

        computed_hash = self._hash_dir()

        return saved_hash != computed_hash

    def _save_hash(self):
        hash_file_path = os.path.join(self.wksp.hash_store, self.name)
        with open(hash_file_path, 'w') as hash_file:
            hash_file.write(self._hash_dir())

    @contextmanager
    def _intermediate(self):
        intermediate_dir = os.path.join(self.wksp.intermediate, self.name)
        ensure_dir(intermediate_dir)
        # TODO make symlinks for all files marked as relevant?
        with cd(intermediate_dir):
            yield intermediate_dir

    def build(self):
        try:
            if self._rebuild_necessary():
                with self._intermediate():
                    self._build()
            self._save_hash()
        except BuildError as e:
            click.secho("BUILD FAILED: {}".format(e.message))

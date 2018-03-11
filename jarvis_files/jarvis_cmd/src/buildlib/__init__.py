import hashlib
import os
import re
import click

from contextlib import contextmanager

from jarvis.core import cd, ln, ensure_dir


class BuildError(Exception):
    pass


class Builder:
    def __init__(self, wksp, dir_, name, **kwargs):
        self.dir_ = dir_
        self.wksp = wksp
        self.full_path = os.path.join(wksp.root, self.dir_)
        self.name = name
        self.params = kwargs

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
        ensure_dir(self.wksp.hash_store)
        with open(hash_file_path, 'w') as hash_file:
            hash_file.write(self._hash_dir())

    def _relpath(self, root, name):
        return os.path.relpath(
                os.path.join(root, name), self.full_path)

    @contextmanager
    def _intermediate(self):
        intermediate_dir = os.path.join(self.wksp.intermediate, self.name)
        ensure_dir(intermediate_dir)
        for root, dirs, files in os.walk(
                self.full_path, topdown=True, followlinks=False):
            if not re.search(r'/\.', root):
                for name in dirs:
                    if (not name.startswith('.') and
                            not re.search(r'/\.', name)):
                        subtree_path = self._relpath(root, name)
                        intermediate_name = os.path.join(
                                intermediate_dir, subtree_path)
                        ensure_dir(intermediate_name)
                for name in files:
                    if (not name.startswith('.') and
                            not re.search(r'/\.', name) and
                            self.is_relevant_file(name)):
                        subtree_path = self._relpath(root, name)
                        intermediate_name = os.path.join(
                                intermediate_dir, subtree_path)
                        ln(os.path.join(root, name), intermediate_name)
        with cd(intermediate_dir):
            yield intermediate_dir

    def build(self):
        try:
            self.wksp.ensure_product_env()
            if self._rebuild_necessary():
                with self._intermediate() as intermediate:
                    self._build(intermediate)
            self._save_hash()
        except BuildError as e:
            click.secho("BUILD FAILED: {}".format(str(e)))

    def _build(self, intermediate):
        raise BuildError("Not implemented")

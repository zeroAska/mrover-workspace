import os
import subprocess

from jarvis.core import shell, cd, exec_in_venv

from . import Builder, BuildError


def run_pytest(env, command):
    try:
        exec_in_venv(env, command)
    except subprocess.CalledProcessError as e:
        if e.returncode != 5:
            return False
    return True


class PythonBuilder(Builder):
    def is_relevant_file(self, name):
        return os.path.splitext(name)[1] == '.py'

    def _build(self, intermediate):
        shell('touch src/__init__.py')
        self.wksp.template(
                'setup.py',
                os.path.join(intermediate, 'setup.py'),
                component=self.name,
                executable=self.params.get('executable', False))
        shell('flake8')
        with cd('src'):
            if not (run_pytest(
                    self.wksp.product_env, ('pytest', '--doctest-modules'))):
                raise BuildError("doctests failed")

        if not run_pytest(self.wksp.product_env, ('pytest',)):
            raise BuildError("unit tests failed")

        exec_in_venv(self.wksp.product_env, ('python', 'setup.py', 'develop'))

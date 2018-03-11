from setuptools import setup, find_packages

setup(
    name="jarvis",
    version="2.1",
    author="MRover",
    package_dir={'': 'src'},
    packages=find_packages('src'),
    install_requires=[
        'Click',
        'click-didyoumean',
        'flake8'
    ],
    entry_points={
        'console_scripts': [
            'jarvis=jarvis.cli:cli'
        ]
    }
)

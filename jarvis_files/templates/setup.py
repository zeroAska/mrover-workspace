from setuptools import setup, find_packages

setup(
    name="{{ component }}",
    version="0.1",
    author="MRover",
    package_dir={'{{ component }}': 'src'},
    packages=find_packages('src'),
{% if executable %}
    entry_points={
        'console_scripts': [
            '{{ component }}={{ component }}.__main__:main'  # noqa
        ]
    }
{% endif %}
)


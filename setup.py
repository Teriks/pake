from setuptools import setup, find_packages
import re

import sys


if sys.version_info < (3, 5):
    exit('Python < 3.5 is not supported.  You are currently running Python {}.{}.{}'.format(*sys.version_info[:3]))

with open('pake/__init__.py') as f:
    version = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]', f.read(), re.MULTILINE).group(1)

if not version:
    raise RuntimeError('version is not set.')

with open('README.rst', 'r', encoding='utf-8') as f:
    readme = f.read()

setup(name='python-pake',
      author='Teriks',
      author_email='Teriks@users.noreply.github.com',
      url='https://github.com/Teriks/pake',
      version=version,
      packages=find_packages(exclude=('tests',)),
      license='BSD 3-Clause',
      description='A make-like build utility entirely in python.',
      long_description=readme,
      include_package_data=True,
      install_requires=[],
      entry_points={
          'console_scripts': [
              'pake = pake.entry_points.pake_command:main'
          ]
      },
      classifiers=[
          'Development Status :: 3 - Alpha',
          'License :: OSI Approved :: BSD License',
          'Intended Audience :: Developers',
          'Natural Language :: English',
          'Operating System :: OS Independent',
          'Programming Language :: Python :: 3.5',
          'Topic :: Software Development :: Build Tools',
          'Topic :: Utilities',
      ]
      )

from setuptools import setup, find_packages
import re, os

version = ''
with open('pake/__init__.py') as f:
    version = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]', f.read(), re.MULTILINE).group(1)

if not version:
    raise RuntimeError('version is not set')

readme = ''
with open('README.md') as f:
    readme = f.read()

setup(name='pake',
      author='Teriks',
      url='https://github.com/Teriks/pake',
      version=version,
      packages=find_packages(),
      license='BSD 3-Clause',
      description='A make like build utility using python.',
      long_description=readme,
      include_package_data=True,
      classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'License :: OSI Approved :: BSD 3-Clause License',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Topic :: Software Development :: Build Tools',
        'Topic :: Utilities',
      ]
)
from setuptools import setup, find_packages
import re

version = ''
with open('pake/__init__.py') as f:
    version = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]', f.read(), re.MULTILINE).group(1)

if not version:
    raise RuntimeError('version is not set')

# alpha 1
version += 'a1'

readme = ''
with open('README.md', 'r', encoding='utf-8') as f:
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
      install_requires=[],
      entry_points={
          'console_scripts': [
              'pake = pake.entry_points.pake_command:main'
          ]
      },
      classifiers=[
          'Development Status :: 3 - Alpha',
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

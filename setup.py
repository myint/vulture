#!/usr/bin/env python

import ast
from distutils.core import setup

from wake import __version__


def version():
    """Return version string."""
    with open('wake.py') as input_file:
        for line in input_file:
            if line.startswith('__version__'):
                return ast.parse(line).body[0].value.s


with open('README.rst') as _readme:
    with open('NEWS.rst') as _news:
        DESCRIPTION = _readme.read() + '\n\n' + _news.read()


setup(name='vulture',
      version=__version__,
      description='Find dead code',
      long_description=DESCRIPTION,
      keywords='vulture',
      author='Jendrik Seipp',
      author_email='jendrikseipp@web.de',
      url='https://bitbucket.org/jendrikseipp/vulture',
      license='GPL3+',
      py_modules=['wake'],
      scripts=['vulture'],
      classifiers=[
      'Environment :: Console',
      'Intended Audience :: Developers',
      'License :: OSI Approved :: GNU General Public License (GPL)',
      'Programming Language :: Python',
      'Programming Language :: Python :: 3'
      'Topic :: Software Development',
      'Topic :: Utilities',
      ],
      )

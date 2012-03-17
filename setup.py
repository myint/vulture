#! /usr/bin/env python

from distutils.core import setup

VERSION = '0.1'

setup(name='vulture',
      version=VERSION,
      description="Find dead code",
      long_description='\n\n'.join([open('README.txt').read(),
                                    open('NEWS.txt').read()]),
      keywords='vulture',
      author='Jendrik Seipp',
      author_email='jendrikseipp@web.de',
      url='https://bitbucket.org/jendrikseipp/vulture',
      license='GPL3+',
      py_modules=['wake'],
      scripts=['vulture'],
      classifiers=[
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU General Public License (GPL)",
        "Programming Language :: Python",
        "Topic :: Software Development",
        "Topic :: Utilities",
        ],
      )

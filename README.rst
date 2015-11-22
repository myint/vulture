vulture
=======

.. image:: https://travis-ci.org/myint/vulture.svg?branch=master
    :target: https://travis-ci.org/myint/vulture
    :alt: Build status

`vulture` finds unused classes, functions and variables in your code. This
helps you cleanup and find errors in your programs. If you run it on both your
library and test suite you can find untested code.

Due to Python's dynamic nature it is impossible to find all dead code for a
static code analyzer like vulture, because it ignores scopes and scans only
token names. Additionally some dynamic items that are not explicitly called
in the code may be incorrectly reported as dead code.

This is a fork of the original_ that adds the ``--level`` option to optionally
reduce false positives. This fork also detects Python scripts without having
to rely on file extensions.

.. _original: https://bitbucket.org/jendrikseipp/vulture


Features
--------

* Fast: Uses static code analysis.
* Lightweight: Only one module.
* Tested: Comes with a test suite.
* Complements *pyflakes* and has the same output syntax.


Installation
------------

* vulture supports Python 2.7 and 3.x.

You can install vulture with this command::

    $ pip install --upgrade git+https://github.com/myint/vulture


Usage
-----

::

    $ vulture --help

After you have found and deleted dead code, run vulture again, because it
may discover more dead code.


Similar programs
----------------

* vulture can be used together with *pyflakes*.
* The *coverage* module can find unused code more reliably, but requires all
  branches of the code to actually be run.


About the name
--------------

A *vulture* eats dead animals. A group of feeding vultures is called a *wake*.

========
Overview
========

.. start-badges

.. list-table::
    :stub-columns: 1

    * - docs
      - |docs|
    * - tests
      - | |requires|
        |
    * - package
      - | |version| |wheel| |supported-versions| |supported-implementations|
        | |commits-since|
.. |docs| image:: https://readthedocs.org/projects/pdCIFplotter/badge/?style=flat
    :target: https://pdCIFplotter.readthedocs.io/
    :alt: Documentation Status

.. |requires| image:: https://requires.io/github/rowlesmr/pdCIFplotter/requirements.svg?branch=master
    :alt: Requirements Status
    :target: https://requires.io/github/rowlesmr/pdCIFplotter/requirements/?branch=master

.. |version| image:: https://img.shields.io/pypi/v/pdCIFplotter.svg
    :alt: PyPI Package latest release
    :target: https://pypi.org/project/pdCIFplotter

.. |wheel| image:: https://img.shields.io/pypi/wheel/pdCIFplotter.svg
    :alt: PyPI Wheel
    :target: https://pypi.org/project/pdCIFplotter

.. |supported-versions| image:: https://img.shields.io/pypi/pyversions/pdCIFplotter.svg
    :alt: Supported versions
    :target: https://pypi.org/project/pdCIFplotter

.. |supported-implementations| image:: https://img.shields.io/pypi/implementation/pdCIFplotter.svg
    :alt: Supported implementations
    :target: https://pypi.org/project/pdCIFplotter

.. |commits-since| image:: https://img.shields.io/github/commits-since/rowlesmr/pdCIFplotter/v0.0.0.svg
    :alt: Commits since latest release
    :target: https://github.com/rowlesmr/pdCIFplotter/compare/v0.0.0...master



.. end-badges

A program for the visualisation of diffraction data in pdCIF format.

* Free software: Apache Software License 2.0

Installation
============

::

    pip install pdCIFplotter

You can also install the in-development version with::

    pip install https://github.com/rowlesmr/pdCIFplotter/archive/master.zip


Documentation
=============


https://pdCIFplotter.readthedocs.io/


Development
===========

To run all the tests run::

    tox

Note, to combine the coverage data from all the tox environments run:

.. list-table::
    :widths: 10 90
    :stub-columns: 1

    - - Windows
      - ::

            set PYTEST_ADDOPTS=--cov-append
            tox

    - - Other
      - ::

            PYTEST_ADDOPTS=--cov-append tox
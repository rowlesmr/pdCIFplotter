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

.. |commits-since| image:: https://img.shields.io/github/commits-since/rowlesmr/pdCIFplotter/v0.0.4.svg
    :alt: Commits since latest release
    :target: https://github.com/rowlesmr/pdCIFplotter/compare/v0.0.4...master



.. end-badges

A program for the visualisation of diffraction data in pdCIF format.

Crystallographic Information Framework (CIF; https://www.iucr.org/resources/cif) files are a way of storing
crystallographic information in a standard human- and machine-readable format. This particular program is focussed
on visualising powder diffraction data stored in CIF format, and, in particular, serial or in situ/operando data.

* Free software: Apache Software License 2.0

Pre-installation
================

If you are on Windows, you must read this step. If you are on Linuz, you can continue.

``pdCIFplotter`` requires ``PyCifRW >= 4.4.3``. If you install ``PyCifRW`` from `PyPI <https://pypi.org/>`_ via ``pip``, then you will also need to compile the included C modules. To do so requires `Microsoft Visual C++ 14.0 or greater <https://visualstudio.microsoft.com/visual-cpp-build-tools/>`_. If you don't have this installed, or do not wish to install it, `precompiled wheel files are available <https://www.lfd.uci.edu/~gohlke/pythonlibs/#pycifrw>`_. You must download the wheel file corresponding to your Python installation.

To obtain information about your Python installation, run the command::

	python -VV

An example output is `Python 3.9.4 (tags/v3.9.4:1f2e308, Apr  6 2021, 13:40:21) [MSC v.1928 64 bit (AMD64)]`, showing that this is 64 bit Python 3.9.

Using ``pip`` version 19.2 or newer, install your downloaded wheel file as::

	pip install c:\path\to\file\name_of_file.whl

This should install ``PyCifRW``, and you can move on to the next step. If you encounter any issues in the installation,
please lodge an `issue <https://github.com/rowlesmr/pdCIFplotter/issues>`_.


Installation
============

To install the release version of ``pdCIFplotter`` from PyPI::

    pip install pdCIFplotter

You can also install the in-development version from GitHub with::

    pip install https://github.com/rowlesmr/pdCIFplotter/archive/master.zip

Quick usage
===========

To run pdCIFplotter as a standalone program::

    python -m pdCIFplotter

or::

	pdcifplotter

Documentation
=============

https://pdCIFplotter.readthedocs.io/en/latest/

Development
===========

This isn't fully implemented yet.

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

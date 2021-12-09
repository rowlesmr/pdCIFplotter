
Changelog
=========

0.0.6 (2021-12-09)
------------------

* Can normalise intensities to counts from provided weights or errors; possible in single, stack, and surface
* hkl ticks labelled by phase name, if present, else, phase id: now including surface plot.
* (ongoing) Refactoring of plot_cif


0.0.5 (2021-11-16)
------------------

* Better hkl checkbox checking
* Doesn't crash if CIF with no diffraction pattern is loaded
* Gracefully handles NANs in data when calculating hkl tick offsets
* Datablock names replaced with block_id values on single plot title and dropdown data box
* hkl ticks labelled by phase name, if present, else, phase id.
* Large refactoring of parse_cif


0.0.4 (2021-11-11)
------------------

* Added hkl ticks to stack plot
* Enabled hkl ticks to be plotted above the diffraction patterns


0.0.3 (2021-11-10)
------------------

* Separated GUI and plotting code
* Fixed crash on changing to surface tab before opening CIF


0.0.2 (2021-11-07)
------------------

* Update install requirements - mplcursors 0.5 is now available, rather than installing from git.
* Can now launch from command line with just ``> pdcifplotter``

0.0.1 (2021-11-06)
------------------

* Update install requirements and provided prompting to user on installing packages not available on PyPi.

0.0.0 (2021-11-05)
------------------

* First release on PyPI.

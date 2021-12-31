
Changelog
=========

0.0.10 (2021-12-31)
------------------

* Updated type hints to maintain compatibility with Python <=v3.8.


0.0.9 (2021-12-31)
------------------

* Single plot - subtitle now shows the datetime, temperature, pressure, Rwp, and GoF, if available in the CIF file. Rwp and GoF is also calculated and displayed in brackets if possible. Gof calculation uses N, and not N-P, so it is only an approximation.
* Stack plot - Hovertext now shows the datetime, temperature, pressure, Rwp, and GoF, if available in the CIF file.
* Surface plot - Can now plot temperature, pressure, quantitative phase analysis (QPA), Rwp, and GoF (if available in the CIF file) next to the surface plot. QPA phases are linked together by their _pd_phase_name, so it is important that the same string is used to denote the same phases in different patterns.


0.0.8 (2021-12-20)
------------------

* Updated some of the zoom behaviour
* Can now use arrow buttons to move between consecutive diffraction patterns in the single plot


0.0.7 (2021-12-18)
------------------

* Zoom persists in single plots when changing between diffraction patterns or altering the view in some way.


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

=====
Usage
=====

It is possible to use pdCIFplotter in a project::

	import pdCIFplotter


However, it is more likely you'll want to run pdCIFplotter as a standalone program::

	pdCIFplotter


A single CIF file can be loaded at a time using the LOAD button, and then various visualisations are available.

It is assumed that all datablocks in a single CIF file have some sort of experimental relationship to each other,
such as from an in-situ experiment, and that it makes sense to visualise them together.

-----------
Single plot
-----------
This plot shows a single diffraction pattern at a time. Each datablock in the given CIF file that contains diffraction
data is shown in the dropdown.

All possible combinations of x- and y-ordinates given in the chosen datablock are capable of being plotted. The
line styles can be customised to your liking.

If both Yobs and Ycalc ordinates are chosen, then a difference and/or a cummulative chi-sq plot can be shown.
The difference plot is simply the difference between Yobs and Ycalc. The cumulative chi-sq value is an indication of
the contribution of each point in the diffraction pattern to the final value of chi-sq; large vertical steps indicate
misfits in the model.

If HKLs are given, and the chosen x-ordinate allows it, tick marks can be plotted showing the positions of reflections.

Both the X and Y axes can be independently scaled to show data in linear, square root, or logarithmic space.

-----------
Stack plot
-----------
This plot shows all diffraction patterns in the CIF file that have both the x- and y-ordinates chosen. The individual
plots are vertically offset by a user-selectable amount. This plot is useful for seeing changes in peak positions,
shapes, and intensities between diffraction patterns.

Both the X and Y axes can be independently scaled to show data in linear, square root, or logarithmic space.



-----------
Surface plot
-----------
This plot shows all diffraction patterns in the CIF file that have both the x- and z-ordinates chosen. In this plot,
the colour scale represent the diffracted intensity, with the y-axis being "patter number"; i.e. the order of that
particular diffraction pattern in the CIF file.

This plot is useful for seeing changes in peak positions and intensities between diffraction patterns, particularly
in in-situ/operando experiments.

The X, Y, and Z axes can be independently scaled to show data in linear, square root, or logarithmic space.








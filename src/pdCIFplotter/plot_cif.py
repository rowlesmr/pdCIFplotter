from pdCIFplotter import parse_cif
import numpy as np
import math
import matplotlib.pyplot as plt
import matplotlib.colors as mc  # a lot of colour choices in here to use
# from timeit import default_timer as timer  # use as start = timer() ...  end = timer()
import mplcursors

DEBUG = True


def debug(*args):
    if DEBUG:
        print(*args)


# LINE_MARKER_COLORS = list(mc.CSS4_COLORS.keys())
# from here: https://matplotlib.org/stable/gallery/color/named_colors.html
_by_hsv = sorted((tuple(mc.rgb_to_hsv(mc.to_rgb(color))), name) for name, color in mc.CSS4_COLORS.items())
LINE_MARKER_COLORS = [name for hsv, name in _by_hsv]
MARKER_STYLES = [None, ".", "o", "s", "*", "+", "x", "D"]
LINE_STYLES = ["solid", "None", "dashed", "dashdot", "dotted"]
LINE_MARKER_SIZE = [str(s) for s in range(1, 10)]

SURFACE_COLOR_MAPS_SOURCE = [
    'viridis', 'plasma', 'inferno', 'magma', 'cividis', 'Greys', 'Purples', 'Blues', 'Greens', 'Oranges', 'Reds',
    'YlOrBr', 'YlOrRd', 'OrRd', 'PuRd', 'RdPu', 'BuPu', 'GnBu', 'PuBu', 'YlGnBu', 'PuBuGn', 'BuGn', 'YlGn']

SURFACE_COLOR_MAPS = []
for c in SURFACE_COLOR_MAPS_SOURCE:
    SURFACE_COLOR_MAPS.append(c)
    SURFACE_COLOR_MAPS.append(c + "_r")

TABLEAU_COLORS = mc.TABLEAU_COLORS
TABLEAU_COLOR_VALUES = list(TABLEAU_COLORS.values())


def _x_axis_title(x_ordinate, wavelength=None):
    if wavelength is None:
        wavelength = "(Wavelength unknown)"
    else:
        wavelength = f"(\u03BB = {wavelength} \u212b)"
    X_AXIS_TITLES = {"_pd_meas_2theta_scan": f"\u00B0 2\u03b8 {wavelength}",
                     "_pd_proc_2theta_corrected": f"\u00B0 2\u03b8 corrected {wavelength}",
                     "_pd_meas_time_of_flight": "Time of flight (\u00b5s)",
                     "_pd_meas_position": "Position (mm)",
                     "_pd_proc_energy_incident": "Incident energy (eV)",
                     "_pd_proc_wavelength": "Incident wavelength (\u212b)",
                     "_pd_proc_d_spacing": "d spacing (\u212b)",
                     "_pd_proc_recip_len_Q": "q (1/\u212b)",
                     "d": "d spacing (\u212b)",
                     "q": "q (1/\u212b)"}
    return X_AXIS_TITLES[x_ordinate]


def _scale_ordinate(axis_scale: dict, val, ordinate):
    if axis_scale[ordinate] == "log":
        val = np.log10(val)
    elif axis_scale[ordinate] == "sqrt":
        val = np.sqrt(val)
    return val


def _scale_x_ordinate(x, axis_scale):
    return _scale_ordinate(axis_scale, x, "x")


def _scale_y_ordinate(y, axis_scale):
    return _scale_ordinate(axis_scale, y, "y")


def _scale_z_ordinate(z, axis_scale):
    return _scale_ordinate(axis_scale, z, "z")


def _scale_xy_ordinates(x, y, axis_scale: dict):
    return _scale_x_ordinate(x, axis_scale), _scale_y_ordinate(y, axis_scale)


def _scale_xyz_ordinates(x, y, z, axis_scale: dict):
    return _scale_x_ordinate(x, axis_scale), _scale_y_ordinate(y, axis_scale), _scale_z_ordinate(z, axis_scale)


def _scale_title(axis_scale: dict, title, ordinate):
    if axis_scale[ordinate] == "log":
        title = f"Log10[{title}]"
    elif axis_scale[ordinate] == "sqrt":
        title = f"Sqrt[{title}]"
    return title


def _scale_x_title(title, axis_scale):
    return _scale_title(axis_scale, title, "x")


def _scale_y_title(title, axis_scale):
    return _scale_title(axis_scale, title, "y")


def _scale_z_title(title, axis_scale):
    return _scale_title(axis_scale, title, "z")


def _scale_xy_title(xtitle, ytitle, axis_scale: dict):
    return _scale_x_title(xtitle, axis_scale), _scale_y_title(ytitle, axis_scale)


def _scale_xyz_title(xtitle, ytitle, ztitle, axis_scale: dict):
    return _scale_x_title(xtitle, axis_scale), _scale_y_title(ytitle, axis_scale), _scale_z_title(ztitle, axis_scale)


class PlotCIF:
    hkl_x_ordinate_mapping = {"_pd_proc_d_spacing": "_refln_d_spacing", "d": "_refln_d_spacing", "q": "refln_q", "_pd_meas_2theta_scan": "refln_2theta",
                              "_pd_proc_2theta_corrected": "refln_2theta"}

    def __init__(self, cif: dict, canvas_x, canvas_y):
        self.canvas_x = canvas_x
        self.canvas_y = canvas_y

        self.single_y_style = {"yobs": {"color": "mediumblue", "marker": "+", "linestyle": "none", "linewidth": "2"},
                               "ycalc": {"color": "red", "marker": None, "linestyle": "solid", "linewidth": "1"},
                               "ybkg": {"color": "gray", "marker": None, "linestyle": "solid", "linewidth": "2"},
                               "ydiff": {"color": "lightgrey", "marker": None, "linestyle": "solid", "linewidth": "2"},
                               "cchi2": {"color": "lightgrey", "marker": None, "linestyle": "solid", "linewidth": "1"}}

        self.surface_z_color = "viridis"
        self.surface_plot_data = {"x_ordinate": "", "y_ordinate": "", "z_ordinate": "",
                                  "x_data": None, "y_data": None, "z_data": None, "plot_list": []}

        self.cif = cif

    def get_all_xy_data(self, x_ordinate, y_ordinate):
        """
        Give an x and y-ordinate, return arrays holding all x ad y data from all patterns in the cif
        that have both of those ordinates. Also return a list of the pattern names which where included
        in the arrays
        :param x_ordinate: str representing the x_ordinate eg _pd_proc_d_spacing
        :param y_ordinate: str representing the y_ordinate eg _pd_meas_intensity_total
        :return: tuple of xs, ys, list of pattern names
        """
        xs = []
        ys = []
        plot_list = []
        for pattern in self.cif.keys():
            cifpat = self.cif[pattern]
            if not (x_ordinate in cifpat and y_ordinate in cifpat):
                continue
            # now the cif pat has both x and y
            xs.append(cifpat[x_ordinate])
            ys.append(cifpat[y_ordinate])
            plot_list.append(pattern)
        return xs, ys, plot_list

    def get_all_xyz_data(self, x_ordinate, y_ordinate, z_ordinate):
        # need to construct a single array for each x, y, z, by looping through only those
        # patterns which have the ordinates necessary to make the piccie I want to see.
        xs = []
        ys = []
        zs = []
        i = 1
        plot_list = []
        min_x = 9999999999
        max_x = -min_x
        x_step = 0
        # get all of the original data
        for pattern in self.cif.keys():
            cifpat = self.cif[pattern]
            if not (x_ordinate in cifpat and
                    (y_ordinate in cifpat or y_ordinate == "Pattern number") and
                    z_ordinate in cifpat):
                continue
            # we now know that both x and z are in the pattern
            x = cifpat[x_ordinate]
            z = cifpat[z_ordinate]
            if y_ordinate == "Pattern number":
                y = i
            else:
                y = cifpat[y_ordinate]

            # interpolation only works if the x-ordinate is increasing.
            # if it doesn't, I need to flip all the ordinates to maintain
            # the relative ordering.
            if x[0] > x[-1]:
                x = np.flip(x)
                y = np.flip(y)
                z = np.flip(z)

            # keep track of min, max, and average step size so
            # I can do a naive linear interpolation to grid the data
            min_x = min(min_x, min(x))
            max_x = max(max_x, max(x))
            x_step += np.average(np.diff(x))

            xs.append(x)
            ys.append(y)
            zs.append(z)
            plot_list.append(pattern)
            i += 1
        else:
            x_step /= i

        # create the x interpolation array and interpolate each diffraction pattern
        xi = np.arange(min_x, max_x, math.fabs(x_step))
        for j in range(len(xs)):
            zs[j] = np.interp(xi, xs[j], zs[j], left=float("nan"), right=float("nan"))

        # https://stackoverflow.com/a/33943276/36061
        # https://stackoverflow.com/a/38025451/36061
        xx, yy = np.meshgrid(xi, ys)
        zz = np.array(zs)
        return xx, yy, zz, plot_list

    def single_update_plot(self, pattern: str,
                           x_ordinate: str, y_ordinates: list,
                           plot_hkls: dict, plot_diff: bool, plot_cchi2: bool,
                           axis_scale: dict,
                           fig):
        dpi = plt.gcf().get_dpi()
        if fig is not None:
            # this is needed for the hkl position calculations
            single_height_px = fig.get_size_inches()[1] * dpi
        else:
            single_height_px = 382

        # if single_fig is None or single_ax is None:
        if fig is not None:
            plt.close(fig)
        fig, ax = plt.subplots(1, 1)
        fig = plt.gcf()
        fig.set_size_inches(self.canvas_x / float(dpi), self.canvas_y / float(dpi))
        fig.set_tight_layout(True)
        plt.margins(x=0)

        cifpat = self.cif[pattern]
        x = _scale_x_ordinate(cifpat[x_ordinate], axis_scale)
        ys = []
        for y in y_ordinates:
            if y != "None":
                ys.append(_scale_y_ordinate(cifpat[y], axis_scale))
            else:
                ys.append(None)

        # need to calculate diff after the y axis transforms to get the right magnitudes
        if plot_diff:
            ydiff = ys[0] - ys[1]
            ys.append(ydiff)
            y_ordinates.append("Diff")
        else:
            ys.append(None)
            y_ordinates.append("Diff")

        min_plot = 999999999
        max_plot = -min_plot
        cchi2_zero = 0
        for y, y_name, y_type in zip(ys, y_ordinates, self.single_y_style.keys()):
            debug(f"{y=} {y_name=} {y_type=}")
            if y is not None:
                if y_name == "Diff":
                    offset = min_plot - np.nanmax(y)
                    y += offset
                    # this is to plot the 'sero' line for the diff plot
                    plt.plot(x, [offset] * len(x), color="black", marker=None, linestyle=(0, (5, 10)), linewidth=1)  # "loosely dashed"

                plt.plot(x, y, label=" " + y_name,
                         color=self.single_y_style[y_type]["color"], marker=self.single_y_style[y_type]["marker"],
                         linestyle=self.single_y_style[y_type]["linestyle"], linewidth=self.single_y_style[y_type]["linewidth"],
                         markersize=float(self.single_y_style[y_type]["linewidth"]) * 3
                         )
                # keep track of min and max to plot hkl ticks and diff correctly
                min_plot = min(min_plot, min(y))
                max_plot = max(max_plot, max(y))
                if y_name != "Diff":
                    cchi2_zero = min_plot

        # hkl plotting below     single_height_px
        single_hovertexts = []
        single_hkl_artists = []
        if plot_hkls["above"] or plot_hkls["below"]:
            y_range = max_plot - min_plot
            hkl_markersize_pt = 6
            hkl_markersize_px = hkl_markersize_pt * 72 / dpi
            num_hkl_rows = len(cifpat["str"].keys())
            hkl_tick_spacing = (((y_range / (single_height_px - hkl_markersize_px * num_hkl_rows)) * single_height_px) - y_range) / num_hkl_rows

            hkl_x_ordinate = PlotCIF.hkl_x_ordinate_mapping[x_ordinate]
            for i, phase in enumerate(cifpat["str"].keys()):
                hkl_x = _scale_x_ordinate(cifpat["str"][phase][hkl_x_ordinate], axis_scale)
                if plot_hkls["below"]:
                    hkl_y = np.array([min_plot - 4 * (i + 1) * hkl_tick_spacing] * len(hkl_x))
                    markerstyle = "|"
                    scalar = 1.0
                else:  # plot above
                    yobs = ys[0]
                    ycalc = ys[1]
                    markerstyle = 7  # a pointing-down triangle with the down tip being the point described by th x,y coordinate
                    scalar = 1.04
                    if yobs is None:
                        hkl_y = np.interp(hkl_x, x, ycalc, left=float("nan"), right=float("nan"))
                    elif ycalc is None:
                        hkl_y = np.interp(hkl_x, x, yobs, left=float("nan"), right=float("nan"))
                    else:  # both are not none
                        hkl_y1 = np.interp(hkl_x, x, yobs, left=float("nan"), right=float("nan"))
                        hkl_y2 = np.interp(hkl_x, x, ycalc, left=float("nan"), right=float("nan"))
                        hkl_y = np.maximum(hkl_y1, hkl_y2)

                hkl_tick, = ax.plot(hkl_x, hkl_y * scalar, label=" " + phase, marker=markerstyle, linestyle="none", markersize=hkl_markersize_pt)
                single_hkl_artists.append(hkl_tick)
                if "refln_hovertext" in cifpat["str"][phase]:
                    single_hovertexts.append(cifpat["str"][phase]["refln_hovertext"])
                else:
                    single_hovertexts.append([phase] * len(hkl_x))

            # https://stackoverflow.com/a/58350037/36061
            single_hkl_hover_dict = dict(zip(single_hkl_artists, single_hovertexts))
            mplcursors.cursor(single_hkl_artists, hover=mplcursors.HoverMode.Transient).connect(
                "add", lambda sel: sel.annotation.set_text(single_hkl_hover_dict[sel.artist][sel.index]))
        # end hkl if

        if plot_cchi2:
            # https://stackoverflow.com/a/10482477/36061
            def align_cchi2(ax_1, v1, ax_2):
                """adjust cchi2 ylimits so that 0 in cchi2 axis is aligned to v1 in main axis"""
                miny1, maxy1 = ax_1.get_ylim()
                rangey1 = maxy1 - miny1
                f = (v1 - miny1) / rangey1
                _, maxy2 = ax_2.get_ylim()
                miny2 = (f / (f - 1)) * maxy2
                ax_2.set_ylim(miny2, maxy2)

            cchi2 = _scale_y_ordinate(parse_cif.calc_cumchi2(cifpat, y_ordinates[0], y_ordinates[1]), axis_scale)

            ax2 = ax.twinx()
            ax2.plot(x, cchi2, label=" c\u03C7\u00b2",
                     color=self.single_y_style["cchi2"]["color"], marker=self.single_y_style["cchi2"]["marker"],
                     linestyle=self.single_y_style["cchi2"]["linestyle"], linewidth=self.single_y_style["cchi2"]["linewidth"],
                     markersize=float(self.single_y_style["cchi2"]["linewidth"]) * 3
                     )
            ax2.set_yticklabels([])
            ax2.set_yticks([])
            ax2.margins(x=0)
            ax2.set_ylabel("c\u03C7\u00b2")
            align_cchi2(ax, cchi2_zero, ax2)

            # organise legends:
            # https://stackoverflow.com/a/10129461/36061
            # ask matplotlib for the plotted objects and their labels
            lines, labels = ax.get_legend_handles_labels()
            lines2, labels2 = ax2.get_legend_handles_labels()
            ax2.legend(lines + lines2, labels + labels2, loc='upper right', frameon=False)

        if not plot_cchi2:
            plt.legend(frameon=False, loc='upper right')  # loc='best')

        if "intensity" in y_ordinates[0]:
            y_axis_title = "Intensity (arb. units)"
        else:
            y_axis_title = "Counts"

        wavelength = parse_cif.get_from_cif(cifpat, "wavelength")
        x_axis_title, y_axis_title = _scale_xy_title(_x_axis_title(x_ordinate, wavelength), y_axis_title, axis_scale)

        if x_ordinate in ["d", "_pd_proc_d_spacing"]:
            plt.gca().invert_xaxis()

        ax.set_xlabel(x_axis_title)
        ax.set_ylabel(y_axis_title)
        plt.title(pattern, loc="left")

        # https://stackoverflow.com/a/30506077/36061
        if plot_cchi2:
            ax.set_zorder(ax2.get_zorder() + 1)
            ax.patch.set_visible(False)

        return fig

    def stack_update_plot(self,
                          x_ordinate: str, y_ordinate: str, offset: float,
                          plot_hkls: dict, axis_scale: dict,
                          fig):
        debug(f"stack {x_ordinate=}")
        debug(f"stack {y_ordinate=}")
        debug(f"stack {offset=}")
        debug(f"stack {axis_scale=}")

        dpi = plt.gcf().get_dpi()
        if fig is not None:
            plt.close(fig)
        fig, ax = plt.subplots(1, 1)
        fig = plt.gcf()
        fig.set_size_inches(self.canvas_x / float(dpi), self.canvas_y / float(dpi))
        fig.set_tight_layout(True)
        plt.margins(x=0)

        # xs and ys hold unscaled values
        xs, ys, plot_list = self.get_all_xy_data(x_ordinate, y_ordinate)
        offset = _scale_y_ordinate(offset, axis_scale)
        # compile all of the patterns' data
        # need to loop backwards so that the data comes out in the correct order for plotting
        for i in range(len(plot_list) - 1, -1, -1):
            pattern = plot_list[i]
            x, y = _scale_xy_ordinates(xs[i], ys[i], axis_scale)
            plt.plot(x, y + i * offset, label=pattern)  # do I want to fill white behind each plot?

        # https://mplcursors.readthedocs.io/en/stable/examples/artist_labels.html
        stack_artists = ax.get_children()
        mplcursors.cursor(stack_artists, hover=mplcursors.HoverMode.Transient).connect("add", lambda sel: sel.annotation.set_text(sel.artist.get_label()))

        stack_hovertexts = []
        stack_hkl_artists = []
        if plot_hkls["above"] or plot_hkls["below"]:
            hkl_markersize_pt = 6
            hkl_x_ordinate = PlotCIF.hkl_x_ordinate_mapping[x_ordinate]
            for i in range(len(plot_list) - 1, -1, -1):
                pattern = plot_list[i]
                cifpat = self.cif[pattern]
                if "str" not in cifpat:
                    continue

                debug(f"Now plotting hkls for {pattern}")
                for j, phase in enumerate(cifpat["str"].keys()):
                    hkl_x = _scale_x_ordinate(cifpat["str"][phase][hkl_x_ordinate], axis_scale)
                    if plot_hkls["below"]:
                        hkl_y = np.array([min(ys[i])] * len(hkl_x))
                        markerstyle = 3
                        scalar = 1.0
                    else:  # plot above
                        markerstyle = 7
                        scalar = 1.04
                        hkl_y = np.interp(hkl_x, _scale_x_ordinate(xs[i], axis_scale), ys[i], left=float("nan"), right=float("nan"))

                    hkl_y = _scale_y_ordinate(hkl_y, axis_scale) * scalar

                    debug(f"{phase=}")
                    debug(f"{hkl_x=}")
                    debug(f"{hkl_y=}")

                    idx = j % len(TABLEAU_COLOR_VALUES)
                    hkl_tick, = ax.plot(hkl_x, hkl_y + i * offset, label=" " + phase, marker=markerstyle, linestyle="none", markersize=hkl_markersize_pt,
                                        color=TABLEAU_COLOR_VALUES[idx])
                    stack_hkl_artists.append(hkl_tick)
                    if "refln_hovertext" in cifpat["str"][phase]:
                        hovertext = [f"{phase}: {hkls}" for hkls in cifpat["str"][phase]["refln_hovertext"]]
                        stack_hovertexts.append(hovertext)
                    else:
                        stack_hovertexts.append([phase] * len(hkl_x))

            # https://stackoverflow.com/a/58350037/36061
            single_hkl_hover_dict = dict(zip(stack_hkl_artists, stack_hovertexts))
            mplcursors.cursor(stack_hkl_artists, hover=mplcursors.HoverMode.Transient).connect(
                "add", lambda sel: sel.annotation.set_text(single_hkl_hover_dict[sel.artist][sel.index]))
        # end hkl if

        if x_ordinate in ["d", "_pd_proc_d_spacing"]:
            plt.gca().invert_xaxis()

        if "intensity" in y_ordinate:
            y_axis_title = "Intensity (arb. units)"
        else:
            y_axis_title = "Counts"

        # check that the wavelength for all patterns is the same
        wavelength = parse_cif.get_from_cif(self.cif[plot_list[0]], "wavelength")
        for pattern in plot_list:
            if wavelength != parse_cif.get_from_cif(self.cif[pattern], "wavelength"):
                wavelength = None
                break

        x_axis_title, y_axis_title = _scale_xy_title(_x_axis_title(x_ordinate, wavelength), y_axis_title, axis_scale)
        ax.set_xlabel(x_axis_title)
        ax.set_ylabel(y_axis_title)

        return fig

    def surface_update_plot(self,
                            x_ordinate: str, y_ordinate: str, z_ordinate: str,
                            plot_hkls: bool, axis_scale: dict,
                            fig):
        dpi = plt.gcf().get_dpi()

        if fig is not None:
            plt.close(fig)
        fig, ax = plt.subplots(1, 1)
        fig = plt.gcf()
        fig.set_size_inches(self.canvas_x / float(dpi), self.canvas_y / float(dpi))
        fig.set_tight_layout(True)
        plt.margins(x=0)

        # am I plotting the data I already have? If all the ordinates are the same, then I don't need to regrab all of the data
        #  and I can just use what I already have.
        if self.surface_plot_data["x_ordinate"] == x_ordinate and \
            self.surface_plot_data["y_ordinate"] == y_ordinate and \
            self.surface_plot_data["z_ordinate"] == z_ordinate:
            debug("reusing surface plot data")
            xx = self.surface_plot_data["x_data"]
            yy = self.surface_plot_data["y_data"]
            zz = self.surface_plot_data["z_data"]
            plot_list = self.surface_plot_data["plot_list"]
        else:
            xx, yy, zz, plot_list = self.get_all_xyz_data(x_ordinate, y_ordinate, z_ordinate)
            # update the surface_plot_data information, so I don't need to do those recalculations everytime if I don't have to.
            self.surface_plot_data["x_ordinate"] = x_ordinate
            self.surface_plot_data["y_ordinate"] = y_ordinate
            self.surface_plot_data["z_ordinate"] = z_ordinate
            self.surface_plot_data["x_data"] = xx
            self.surface_plot_data["y_data"] = yy
            self.surface_plot_data["z_data"] = zz
            self.surface_plot_data["plot_list"] = plot_list
        # end of if

        debug("scaling surface plot data")
        xx, yy, zz = _scale_xyz_ordinates(xx, yy, zz, axis_scale)

        debug("plotting surface plot")
        print(f"{xx=}")
        print(f"{yy=}")
        print(f"{zz=}")
        plt.pcolormesh(xx, yy, zz, shading='nearest', cmap=self.surface_z_color)

        if x_ordinate in ["d", "_pd_proc_d_spacing"]:
            plt.gca().invert_xaxis()

        # hkl plotting below     single_height_px
        surface_hovertexts = []
        surface_hkl_artists = []
        if plot_hkls:
            debug("plotting hkls")
            hkl_markersize_pt = 6

            hkl_x_ordinate = PlotCIF.hkl_x_ordinate_mapping[x_ordinate]
            for pattern, ys in zip(plot_list, yy):
                cifpat = self.cif[pattern]
                y = ys[0]
                if "str" not in cifpat:
                    continue

                for i, phase in enumerate(cifpat["str"].keys()):
                    debug(f"Should be plotting hkls for {phase}, which is number {i}.")

                    hkl_x = _scale_x_ordinate(cifpat["str"][phase][hkl_x_ordinate], axis_scale)
                    hkl_y = _scale_y_ordinate([y] * len(hkl_x), axis_scale)
                    idx = i % len(TABLEAU_COLOR_VALUES)
                    hkl_tick, = ax.plot(hkl_x, hkl_y, label=" " + phase, marker="|", linestyle="none", markersize=hkl_markersize_pt, color=TABLEAU_COLOR_VALUES[idx])
                    surface_hkl_artists.append(hkl_tick)
                    if "refln_hovertext" in cifpat["str"][phase]:
                        hovertext = [f"{phase}: {hkls}" for hkls in cifpat["str"][phase]["refln_hovertext"]]
                        surface_hovertexts.append(hovertext)
                    else:
                        surface_hovertexts.append([phase] * len(hkl_x))

            # https://stackoverflow.com/a/58350037/36061
            surface_hkl_hover_dict = dict(zip(surface_hkl_artists, surface_hovertexts))
            mplcursors.cursor(surface_hkl_artists, hover=mplcursors.HoverMode.Transient).connect(
                "add", lambda sel: sel.annotation.set_text(surface_hkl_hover_dict[sel.artist][sel.index]))
        # end hkl if

        debug("Setting surface plot axis labels")
        # check that the wavelength for all patterns is the same
        wavelength = parse_cif.get_from_cif(self.cif[plot_list[0]], "wavelength")
        for pattern in plot_list:
            if wavelength != parse_cif.get_from_cif(self.cif[pattern], "wavelength"):
                wavelength = None
                break
        x_axis_title, y_axis_title, z_axis_title = _scale_xyz_title(_x_axis_title(x_ordinate, wavelength), "Pattern number", z_ordinate, axis_scale)

        plt.xlabel(x_axis_title)
        plt.ylabel(y_axis_title)
        plt.colorbar(label=z_axis_title)

        return fig

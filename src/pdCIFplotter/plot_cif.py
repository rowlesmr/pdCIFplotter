from numpy import ndarray

from pdCIFplotter import parse_cif
import numpy as np
import math
import matplotlib.figure as mf
import matplotlib.axes as ma
import matplotlib.pyplot as plt
import matplotlib.colors as mc  # a lot of colour choices in here to use
# from timeit import default_timer as timer  # use as start = timer() ...  end = timer()
import mplcursors
from typing import List, Tuple, Any

DEBUG = True


def debug(*args):
    if DEBUG:
        print(*args)


# LINE_MARKER_COLORS = list(mc.CSS4_COLORS.keys())
# from here: https://matplotlib.org/stable/gallery/color/named_colors.html
_by_hsv = sorted((tuple(mc.rgb_to_hsv(mc.to_rgb(color))), name) for name, color in mc.CSS4_COLORS.items())
LINE_MARKER_COLORS = [name for hsv, name in _by_hsv]
MARKER_STYLES: List[str] = [None, ".", "o", "s", "*", "+", "x", "D"]
LINE_STYLES: List[str] = ["solid", "None", "dashed", "dashdot", "dotted"]
LINE_MARKER_SIZE: List[str] = [str(s) for s in range(1, 10)]

SURFACE_COLOR_MAPS_SOURCE: List[str] = [
    'viridis', 'plasma', 'inferno', 'magma', 'cividis', 'Greys', 'Purples', 'Blues', 'Greens', 'Oranges', 'Reds',
    'YlOrBr', 'YlOrRd', 'OrRd', 'PuRd', 'RdPu', 'BuPu', 'GnBu', 'PuBu', 'YlGnBu', 'PuBuGn', 'BuGn', 'YlGn']

SURFACE_COLOR_MAPS = []
for c in SURFACE_COLOR_MAPS_SOURCE:
    SURFACE_COLOR_MAPS.append(c)
    SURFACE_COLOR_MAPS.append(c + "_r")

TABLEAU_COLORS = mc.TABLEAU_COLORS
TABLEAU_COLOR_VALUES: List[str] = list(TABLEAU_COLORS.values())


def _x_axis_title(x_ordinate: str, wavelength: float = None) -> str:
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


def _scale_ordinate(axis_scale: dict, val, ordinate: str):
    if axis_scale[ordinate] == "log":
        val = np.log10(val)
    elif axis_scale[ordinate] == "sqrt":
        val = np.sqrt(val)
    return val


def _scale_x_ordinate(x, axis_scale: dict):
    return _scale_ordinate(axis_scale, x, "x")


def _scale_y_ordinate(y, axis_scale: dict):
    return _scale_ordinate(axis_scale, y, "y")


def _scale_z_ordinate(z, axis_scale: dict):
    return _scale_ordinate(axis_scale, z, "z")


def _scale_xy_ordinates(x, y, axis_scale: dict):
    return _scale_x_ordinate(x, axis_scale), _scale_y_ordinate(y, axis_scale)


def _scale_xyz_ordinates(x, y, z, axis_scale: dict):
    return _scale_x_ordinate(x, axis_scale), _scale_y_ordinate(y, axis_scale), _scale_z_ordinate(z, axis_scale)


def _scale_title(axis_scale: dict, title: str, ordinate: str) -> str:
    if axis_scale[ordinate] == "log":
        title = f"Log10[{title}]"
    elif axis_scale[ordinate] == "sqrt":
        title = f"Sqrt[{title}]"
    return title


def _scale_x_title(title: str, axis_scale: dict) -> str:
    return _scale_title(axis_scale, title, "x")


def _scale_y_title(title: str, axis_scale: dict) -> str:
    return _scale_title(axis_scale, title, "y")


def _scale_z_title(title: str, axis_scale: dict) -> str:
    return _scale_title(axis_scale, title, "z")


def _scale_xy_title(xtitle: str, ytitle: str, axis_scale: dict) -> Tuple[str, str]:
    return _scale_x_title(xtitle, axis_scale), _scale_y_title(ytitle, axis_scale)


def _scale_xyz_title(xtitle: str, ytitle: str, ztitle: str, axis_scale: dict) -> Tuple[str, str, str]:
    return _scale_x_title(xtitle, axis_scale), _scale_y_title(ytitle, axis_scale), _scale_z_title(ztitle, axis_scale)


class PlotCIF:
    hkl_x_ordinate_mapping = {"_pd_proc_d_spacing": "_refln_d_spacing", "d": "_refln_d_spacing", "q": "refln_q", "_pd_meas_2theta_scan": "refln_2theta",
                              "_pd_proc_2theta_corrected": "refln_2theta"}

    def __init__(self, cif: dict, canvas_x: int, canvas_y: int):
        self.canvas_x = canvas_x
        self.canvas_y = canvas_y

        self.single_y_style = {"yobs": {"color": "mediumblue", "marker": "+", "linestyle": "none", "linewidth": "2"},
                               "ycalc": {"color": "red", "marker": None, "linestyle": "solid", "linewidth": "1"},
                               "ybkg": {"color": "gray", "marker": None, "linestyle": "solid", "linewidth": "2"},
                               "ydiff": {"color": "lightgrey", "marker": None, "linestyle": "solid", "linewidth": "2"},
                               "cchi2": {"color": "lightgrey", "marker": None, "linestyle": "solid", "linewidth": "1"},
                               "norm_int": {"color": "lightgrey", "marker": None, "linestyle": "solid", "linewidth": "1"}}

        self.surface_z_color = "viridis"
        self.surface_plot_data = {"x_ordinate": "", "y_ordinate": "", "z_ordinate": "",
                                  "x_data": None, "y_data": None, "z_data": None, "z_norm": None,
                                  "plot_list": []}

        self.cif: dict = cif

    def get_all_xy_data(self, x_ordinate: str, y_ordinate: str) -> Tuple[List, List, List[str]]:
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
            if x_ordinate not in cifpat or y_ordinate not in cifpat:
                continue
            # now the cif pat has both x and y
            xs.append(cifpat[x_ordinate])
            ys.append(cifpat[y_ordinate])
            plot_list.append(pattern)
        return xs, ys, plot_list

    def get_all_scaled_xy_data(self, x_ordinate: str, y_ordinate: str, axis_scale:dict) -> Tuple[List, List, List[str]]:
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
            if x_ordinate not in cifpat or y_ordinate not in cifpat:
                continue
            # now the cif pat has both x and y
            xs.append(_scale_x_ordinate(cifpat[x_ordinate], axis_scale))
            ys.append(_scale_y_ordinate(cifpat[y_ordinate], axis_scale))
            plot_list.append(pattern)
        return xs, ys, plot_list


    def get_xy_ynorm_data(self, x_ordinate: str, y_ordinate: str) -> List:
        """
        Give an x and y-ordinate, return arrays holding y_norm values from all patterns in the cif
        that have both of those ordinates.
        :param x_ordinate: str representing the x_ordinate eg _pd_proc_d_spacing
        :param y_ordinate: str representing the y_ordinate eg _pd_meas_intensity_total
        :return: list of y_norm values
        """
        y_norms = []
        for pattern in self.cif.keys():
            cifpat = self.cif[pattern]
            if x_ordinate not in cifpat or y_ordinate not in cifpat:
                continue
            # now the cifpat has both x and y
            y = cifpat[y_ordinate]
            if "_pd_proc_ls_weight" in cifpat:
                y_norm = y * cifpat["_pd_proc_ls_weight"]
            else:
                y_norm = y / cifpat[y_ordinate + "_err"] ** 2
            y_norms.append(y_norm)
        return y_norms

    def get_all_xyz_znorm_data(self, x_ordinate: str, y_ordinate: str, z_ordinate: str, z_norm_ordinate: str) -> tuple[Any, Any, ndarray, ndarray, list[Any]]:
        # need to construct a single array for each x, y, z, by looping through only those
        # patterns which have the ordinates necessary to make the piccie I want to see.
        xs = []
        ys = []
        zs = []
        znorms = []
        i = 1
        plot_list = []
        min_x = 9999999999
        max_x = -min_x
        x_step = 0
        for pattern in self.cif.keys():
            cifpat = self.cif[pattern]
            if (
                x_ordinate not in cifpat
                or y_ordinate not in cifpat
                and y_ordinate != "Pattern number"
                or z_ordinate not in cifpat
            ):
                continue
            # we now know that both x and z are in the pattern
            x = cifpat[x_ordinate]
            z = cifpat[z_ordinate]
            y = i if y_ordinate == "Pattern number" else cifpat[y_ordinate]
            z_norm = cifpat[z_norm_ordinate]
            z_norm = z_norm * cifpat["_pd_proc_ls_weight"] if "_pd_proc_ls_weight" in cifpat else z_norm / cifpat[z_ordinate + "_err"] ** 2
            # interpolation only works if the x-ordinate is increasing.
            # if it doesn't, I need to flip all the ordinates to maintain
            # the relative ordering.
            if x[0] > x[-1]:
                x = np.flip(x)
                y = np.flip(y)
                z = np.flip(z)
                z_norm = np.flip(z_norm)

            # keep track of min, max, and average step size so
            # I can do a naive linear interpolation to grid the data
            min_x = min(min_x, min(x))
            max_x = max(max_x, max(x))
            x_step += np.average(np.diff(x))

            xs.append(x)
            ys.append(y)
            zs.append(z)
            znorms.append(z_norm)
            plot_list.append(pattern)
            i += 1
        x_step /= i

        # create the x interpolation array and interpolate each diffraction pattern
        xi = np.arange(min_x, max_x, math.fabs(x_step))
        for j in range(len(xs)):
            zs[j] = np.interp(xi, xs[j], zs[j], left=float("nan"), right=float("nan"))
            znorms[j] = np.interp(xi, xs[j], znorms[j], left=float("nan"), right=float("nan"))

        # https://stackoverflow.com/a/33943276/36061
        # https://stackoverflow.com/a/38025451/36061
        xx, yy = np.meshgrid(xi, ys)
        zz = np.array(zs)
        zn = np.array(znorms)
        return xx, yy, zz, zn, plot_list

    def single_update_plot(self, pattern: str,
                           x_ordinate: str, y_ordinates: list,
                           plot_hkls: dict, plot_diff: bool, plot_cchi2: bool, plot_norm_int: bool,
                           axis_scale: dict,
                           fig: mf.Figure) -> mf.Figure:
        # todo: look at https://stackoverflow.com/a/63152341/36061 for idea on zooming
        dpi = plt.gcf().get_dpi()
        single_height_px = fig.get_size_inches()[1] * dpi if fig is not None else 382  # this is needed for the hkl position calculations
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

        if plot_norm_int and y_ordinates[0] != "None":
            y = cifpat[y_ordinates[0]]
            if "_pd_proc_ls_weight" in cifpat:
                y_norm = y * np.maximum(cifpat["_pd_proc_ls_weight"], 1e-6)
            else:
                y_norm = y / cifpat[y_ordinates[0] + "_err"] ** 2
        else:
            y_norm = np.ones(len(x))

        for y in y_ordinates:
            if y != "None":
                ys.append(_scale_y_ordinate(cifpat[y] * y_norm, axis_scale))
            else:
                ys.append(None)

        # need to calculate diff after the y axis transforms to get the right magnitudes
        if plot_diff:
            ydiff = ys[0] - ys[1]
            ys.append(ydiff)
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
                    ax.plot(x, [offset] * len(x), color="black", marker=None, linestyle=(0, (5, 10)), linewidth=1)  # "loosely dashed"

                label = f" {y_name}" if not plot_norm_int else f" {y_name} (norm.)"
                ax.plot(x, y, label=label,
                        color=self.single_y_style[y_type]["color"], marker=self.single_y_style[y_type]["marker"],
                        linestyle=self.single_y_style[y_type]["linestyle"], linewidth=self.single_y_style[y_type]["linewidth"],
                        markersize=float(self.single_y_style[y_type]["linewidth"]) * 3
                        )
                # keep track of min and max to plot hkl ticks and diff correctly
                min_plot = min(min_plot, np.nanmin(y))
                max_plot = max(max_plot, np.nanmax(y))
                if y_name != "Diff":
                    cchi2_zero = min_plot

        if plot_hkls["above"] or plot_hkls["below"]:
            single_hovertexts, single_hkl_artists = self.plot_hkls(plot_hkls["below"], cifpat, x_ordinate, x, ys, axis_scale, min_plot, max_plot, 0, True, dpi, single_height_px, ax)
            self.add_hovertext_to_hkls(single_hkl_artists, single_hovertexts)

        if plot_cchi2:
            ax2 = self.single_plot_cchi2(cifpat, x, [y_ordinates[0], y_ordinates[1]], axis_scale, cchi2_zero, ax)

        if not plot_cchi2:
            plt.legend(frameon=False, loc='upper right')  # loc='best')

        if plot_norm_int:
            y_axis_title = "Normalised counts"
        elif "intensity" in y_ordinates[0]:
            y_axis_title = "Intensity (arb. units)"
        else:
            y_axis_title = "Counts"

        wavelength = parse_cif.get_from_cif(cifpat, "wavelength")
        x_axis_title, y_axis_title = _scale_xy_title(_x_axis_title(x_ordinate, wavelength), y_axis_title, axis_scale)

        if x_ordinate in {"d", "_pd_proc_d_spacing"}:
            plt.gca().invert_xaxis()

        ax.set_xlabel(x_axis_title)
        ax.set_ylabel(y_axis_title)
        plt.title(pattern, loc="left")

        # https://stackoverflow.com/a/30506077/36061
        if plot_cchi2:
            ax.set_zorder(ax2.get_zorder() + 1)
            ax.patch.set_visible(False)

        return fig

    def plot_hkls(self, plot_below: bool, cifpat: dict, x_ordinate: str, x, ys,
                  axis_scale: dict, y_min: float, y_max: float, hkl_y_offset: float,
                  single_plot: bool,
                  dpi: int, single_height_px: int, ax: ma.Axes):

        def interp(_hkl_x, _x, _y):
            return np.interp(_hkl_x, _x, _y, left=float("nan"), right=float("nan"))

        hovertexts = []
        hkl_artists = []
        y_range = y_max - y_min
        hkl_markersize_pt = 6
        hkl_markersize_px = hkl_markersize_pt * 72 / dpi
        num_hkl_rows = len(cifpat["str"].keys())
        hkl_tick_vertical_spacing = (((y_range / (single_height_px - hkl_markersize_px * num_hkl_rows)) * single_height_px) - y_range) / num_hkl_rows

        hkl_x_ordinate = PlotCIF.hkl_x_ordinate_mapping[x_ordinate]
        for i, phase in enumerate(cifpat["str"].keys()):
            if hkl_x_ordinate not in cifpat["str"][phase]:
                print(f"Couldn't find {hkl_x_ordinate} in {phase=}.")
                continue
            hkl_x = _scale_x_ordinate(cifpat["str"][phase][hkl_x_ordinate], axis_scale)
            if plot_below:
                if single_plot:
                    hkl_y = np.array([y_min - 4 * (i + 1) * hkl_tick_vertical_spacing] * len(hkl_x))
                else:
                    hkl_y = np.array([min(ys[0])] * len(hkl_x))
                markerstyle = 3
                scalar = 1.0
            else:  # plot above
                markerstyle = 7  # a pointing-down triangle with the down tip being the point described by th x,y coordinate
                scalar = 1.04
                yobs = ys[0]  # ys is already scaled to the y-axis scale
                ycalc = ys[1]
                if yobs is None:
                    hkl_y = interp(hkl_x, x, ycalc)
                elif ycalc is None:
                    hkl_y = interp(hkl_x, x, yobs)
                else:
                    hkl_y = np.maximum(interp(hkl_x, x, ycalc), interp(hkl_x, x, yobs))

            hkl_y = hkl_y * scalar + hkl_y_offset
            idx = i % len(TABLEAU_COLOR_VALUES)
            phasename = cifpat["str"][phase]["_pd_phase_name"] if "_pd_phase_name" in cifpat["str"][phase] else phase
            hkl_tick, = ax.plot(hkl_x, hkl_y, label=" " + phasename, marker=markerstyle, linestyle="none", markersize=hkl_markersize_pt,
                                color=TABLEAU_COLOR_VALUES[idx])
            hkl_artists.append(hkl_tick)
            if "refln_hovertext" in cifpat["str"][phase]:
                phasename = cifpat["str"][phase]["_pd_phase_name"] if "_pd_phase_name" in cifpat["str"][phase] else phase
                hovertext = [f'{phasename}: {hkls}' for hkls in cifpat["str"][phase]["refln_hovertext"]]
                hovertexts.append(hovertext)
            else:
                hovertexts.append([phase] * len(hkl_x))

        return hovertexts, hkl_artists

    def add_hovertext_to_hkls(self, hkl_artists, hovertexts):
        # https://stackoverflow.com/a/58350037/36061
        hkl_hover_dict = dict(zip(hkl_artists, hovertexts))
        mplcursors.cursor(hkl_artists, hover=mplcursors.HoverMode.Transient).connect(
            "add", lambda sel: sel.annotation.set_text(hkl_hover_dict[sel.artist][sel.index]))

    def plot_norm_int_to_err(self, cifpat: dict, x, norm_int_to_err_y_ordinate: str, axis_scale: dict, ax: ma.Axes) -> None:
        y = cifpat[norm_int_to_err_y_ordinate]
        if "_pd_proc_ls_weight" in cifpat:
            y_norm = y ** 2 * cifpat["_pd_proc_ls_weight"]
        else:
            y_norm = (y / cifpat[norm_int_to_err_y_ordinate + "_err"]) ** 2
        y_norm = _scale_y_ordinate(y_norm, axis_scale)

        ax.plot(x, y_norm, label=" Norm. int. to errors",
                color=self.single_y_style["norm_int"]["color"], marker=self.single_y_style["norm_int"]["marker"],
                linestyle=self.single_y_style["norm_int"]["linestyle"], linewidth=self.single_y_style["norm_int"]["linewidth"],
                markersize=float(self.single_y_style["norm_int"]["linewidth"]) * 3
                )

    def single_plot_cchi2(self, cifpat: dict, x, cchi2_y_ordinates: List[str], axis_scale: dict, cchi2_zero: float, ax1: ma.Axes) -> ma.Axes:
        # https://stackoverflow.com/a/10482477/36061
        def align_cchi2(ax_1, v1, ax_2):
            """adjust cchi2 ylimits so that 0 in cchi2 axis is aligned to v1 in main axis"""
            miny1, maxy1 = ax_1.get_ylim()
            rangey1 = maxy1 - miny1
            f = (v1 - miny1) / rangey1
            _, maxy2 = ax_2.get_ylim()
            miny2 = (f / (f - 1)) * maxy2
            ax_2.set_ylim(miny2, maxy2)

        cchi2 = _scale_y_ordinate(parse_cif.calc_cumchi2(cifpat, cchi2_y_ordinates[0], cchi2_y_ordinates[1]), axis_scale)
        rwp = parse_cif.calc_rwp(cifpat, cchi2_y_ordinates[0], cchi2_y_ordinates[1])
        ax2 = ax1.twinx()
        ax2.plot(x, cchi2, label=f" c\u03C7\u00b2 - (Rwp = {rwp * 100:.2f}%)",
                 color=self.single_y_style["cchi2"]["color"], marker=self.single_y_style["cchi2"]["marker"],
                 linestyle=self.single_y_style["cchi2"]["linestyle"], linewidth=self.single_y_style["cchi2"]["linewidth"],
                 markersize=float(self.single_y_style["cchi2"]["linewidth"]) * 3
                 )
        ax2.set_yticklabels([])
        ax2.set_yticks([])
        ax2.margins(x=0)
        ax2.set_ylabel("c\u03C7\u00b2")
        align_cchi2(ax1, cchi2_zero, ax2)

        # organise legends:
        # https://stackoverflow.com/a/10129461/36061
        # ask matplotlib for the plotted objects and their labels
        lines, labels = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax2.legend(lines + lines2, labels + labels2, loc='upper right', frameon=False)

        return ax2

    def stack_update_plot(self,
                          x_ordinate: str, y_ordinate: str, offset: float,
                          plot_hkls: dict, plot_norm_int:dict,
                          axis_scale: dict,
                          fig: mf.Figure) -> mf.Figure:
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

        if plot_norm_int["norm_int"]:
            print(f'{plot_norm_int["y_ordinate_for_norm"]=}')
            y_norms = self.get_xy_ynorm_data(x_ordinate, plot_norm_int["y_ordinate_for_norm"])
        else:
            y_norms = [np.ones(len(xi)) for xi in xs]

        # compile all the patterns' data
        # need to loop backwards so that the data comes out in the correct order for plotting

        for j in range(len(plot_list) - 1, -1, -1):
            pattern = plot_list[j]
            x, y = xs[j], ys[j]*y_norms[j]
            x, y = _scale_xy_ordinates(x, y, axis_scale)
            label = pattern if not plot_norm_int["norm_int"] else f"{pattern} (norm.)"
            ax.plot(x, y + j * offset, label=label)  # do I want to fill white behind each plot?


        # https://mplcursors.readthedocs.io/en/stable/examples/artist_labels.html
        stack_artists = ax.get_children()
        mplcursors.cursor(stack_artists, hover=mplcursors.HoverMode.Transient).connect("add", lambda sel: sel.annotation.set_text(sel.artist.get_label()))

        if plot_hkls["above"] or plot_hkls["below"]:
            stack_hovertexts = []
            stack_hkl_artists = []
            for j in range(len(plot_list) - 1, -1, -1):
                cifpat = self.cif[plot_list[j]]
                hkl_y_offset = j * offset
                x, y = xs[j], ys[j]*y_norms[j]
                x, y = _scale_xy_ordinates(x, y, axis_scale)
                if "str" not in cifpat:
                    continue
                tmp_hovertexts, tmp_hkl_artists = self.plot_hkls(plot_hkls["below"], cifpat, x_ordinate, x, [y, None],\
                               axis_scale, 0, 0, hkl_y_offset, False, dpi, -1, ax)
                stack_hovertexts.extend(tmp_hovertexts)
                stack_hkl_artists.extend(tmp_hkl_artists)

            self.add_hovertext_to_hkls(stack_hkl_artists, stack_hovertexts)
        # end hkl if

        if x_ordinate in {"d", "_pd_proc_d_spacing"}:
            plt.gca().invert_xaxis()

        if plot_norm_int["norm_int"]:
            y_axis_title = "Normalised counts"
        elif "intensity" in y_ordinate:
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
                            plot_hkls: bool, plot_norm_int:dict,
                            axis_scale: dict,
                            fig: mf.Figure) -> mf.Figure:
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
            znorm = self.surface_plot_data["z_norm"]
            plot_list = self.surface_plot_data["plot_list"]
        else:
            xx, yy, zz, znorm, plot_list = self.get_all_xyz_znorm_data(x_ordinate, y_ordinate, z_ordinate, plot_norm_int["z_ordinate_for_norm"])
            # update the surface_plot_data information, so I don't need to do those recalculations everytime if I don't have to.
            self.surface_plot_data["x_ordinate"] = x_ordinate
            self.surface_plot_data["y_ordinate"] = y_ordinate
            self.surface_plot_data["z_ordinate"] = z_ordinate
            self.surface_plot_data["x_data"] = xx
            self.surface_plot_data["y_data"] = yy
            self.surface_plot_data["z_data"] = zz
            self.surface_plot_data["z_norm"] = znorm
            self.surface_plot_data["plot_list"] = plot_list
        # end of if

        if plot_norm_int["norm_int"]:
            xx, yy, zz = _scale_xyz_ordinates(xx, yy, zz*znorm, axis_scale)
        else:
            xx, yy, zz = _scale_xyz_ordinates(xx, yy, zz, axis_scale)

        plt.pcolormesh(xx, yy, zz, shading='nearest', cmap=self.surface_z_color)

        if x_ordinate in {"d", "_pd_proc_d_spacing"}:
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
                    if hkl_x_ordinate not in cifpat["str"][phase]:
                        continue

                    hkl_x = _scale_x_ordinate(cifpat["str"][phase][hkl_x_ordinate], axis_scale)
                    hkl_y = _scale_y_ordinate([y] * len(hkl_x), axis_scale)
                    idx = i % len(TABLEAU_COLOR_VALUES)
                    hkl_tick, = ax.plot(hkl_x, hkl_y, label=" " + phase, marker="|", linestyle="none", markersize=hkl_markersize_pt, color=TABLEAU_COLOR_VALUES[idx])
                    surface_hkl_artists.append(hkl_tick)
                    if "refln_hovertext" in cifpat["str"][phase]:
                        phasename = cifpat["str"][phase]["_pd_phase_name"] if "_pd_phase_name" in cifpat["str"][phase] else phase
                        hovertext = [f'{phasename}: {hkls}' for hkls in cifpat["str"][phase]["refln_hovertext"]]
                        surface_hovertexts.append(hovertext)
                    else:
                        surface_hovertexts.append([phase] * len(hkl_x))

            # https://stackoverflow.com/a/58350037/36061
            surface_hkl_hover_dict = dict(zip(surface_hkl_artists, surface_hovertexts))
            mplcursors.cursor(surface_hkl_artists, hover=mplcursors.HoverMode.Transient).connect(
                "add", lambda sel: sel.annotation.set_text(surface_hkl_hover_dict[sel.artist][sel.index]))
        # end hkl if

        # check that the wavelength for all patterns is the same
        wavelength = parse_cif.get_from_cif(self.cif[plot_list[0]], "wavelength")
        for pattern in plot_list:
            if wavelength != parse_cif.get_from_cif(self.cif[pattern], "wavelength"):
                wavelength = None
                break

        if plot_norm_int["norm_int"]:
            z_axis_title = "Normalised counts"
        elif "intensity" in z_ordinate:
            z_axis_title = "Intensity (arb. units)"
        else:
            z_axis_title = "Counts"
        x_axis_title, y_axis_title, z_axis_title = _scale_xyz_title(_x_axis_title(x_ordinate, wavelength), "Pattern number", z_axis_title, axis_scale)

        plt.xlabel(x_axis_title)
        plt.ylabel(y_axis_title)
        plt.colorbar(label=z_axis_title)

        return fig

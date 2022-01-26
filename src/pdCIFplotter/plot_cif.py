from pdCIFplotter import parse_cif
import numpy as np
import math
from matplotlib.figure import Figure
from matplotlib.axes import Axes

import matplotlib.colors as mc  # a lot of colour choices in here to use
# from timeit import default_timer as timer  # use as start = timer() ...  end = timer()
import mplcursors
from typing import List, Tuple, Any

DEBUG = False


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


def add_hovertext_to_each_point(artists, hovertexts):
    # https://stackoverflow.com/a/58350037/36061
    hover_dict = dict(zip(artists, hovertexts))
    mplcursors.cursor(artists, hover=mplcursors.HoverMode.Transient).connect(
        "add", lambda sel: sel.annotation.set_text(hover_dict[sel.artist][sel.index]))


# mplcursors.cursor(stack_artists, hover=mplcursors.HoverMode.Transient).connect("add", lambda sel: sel.annotation.set_text(sel.artist.get_label()))

# https://stackoverflow.com/a/30734735/36061
def array_strictly_increasing_or_equal(a):
    return np.all(a[1:] >= a[:-1])


def array_strictly_decreasing_or_equal(a):
    return np.all(a[1:] <= a[:-1])


def rescale_val(val: float, old_scale: dict, new_scale: dict, ordinate: str):
    if old_scale[ordinate] == "log":
        val = math.copysign(1, val) * 10 ** abs(val)
    elif old_scale[ordinate] == "sqrt":
        val = math.copysign(1, val) * val ** 2
    return _scale_ordinate(new_scale, val, ordinate)


def get_first_different_kv_pair(old_dict: dict, new_dict: dict):
    for k, v in old_dict.items():
        if new_dict[k] != v:
            return k, v


def get_zoomed_data_min_max(ax, x_lim: Tuple, y_lim: Tuple):
    xmin = x_lim[0]
    xmax = x_lim[1]
    ymin = y_lim[0]
    ymax = y_lim[1]
    xs = []
    ys = []

    if xmin > xmax:
        xmin, xmax = xmax, xmin
    for line in ax.lines:
        xa = line.get_xdata()
        ya = line.get_ydata()
        for x, y in zip(xa, ya):
            if xmin < x < xmax:
                xs.append(x)
                ys.append(y)
    xmin = min(xs)
    xmax = max(xs)
    ymin = max(ymin, min(ys))
    ymax = min(ymax, max(ys))

    return (xmin, xmax), (ymin / 1.04, ymax * 1.04)


def isclose_listlike(a, b, rel_tol=1e-09, abs_tol=0.0):
    if a is None or b is None:
        return False
    if len(a) != len(b):
        return False
    return all(
        math.isclose(av, bv, rel_tol=rel_tol, abs_tol=abs_tol)
        for av, bv in zip(a, b)
    )


def make_subtitle_string(cifpat, s="", yobs: str = "", ycalc: str = "") -> str:
    def add_string(add_me, s, brackets=False):
        if s and brackets:
            return f"{s} ({add_me})"
        elif s:
            return f"{s}; {add_me}"
        else:
            return add_me

    print_Rfactor = ((yobs and ycalc) and (yobs != "None" and ycalc != "None")) or ("_pd_proc_ls_prof_wr_factor" in cifpat or "_refine_ls_goodness_of_fit_all" in cifpat)

    if "_pd_meas_datetime_initiated" in cifpat:
        s = add_string(cifpat['_pd_meas_datetime_initiated'], s)
    if "_diffrn_ambient_temperature" in cifpat:
        s = add_string(f"{cifpat['_diffrn_ambient_temperature']} K", s)
    if "_diffrn_ambient_pressure" in cifpat:
        s = add_string(f"{cifpat['_diffrn_ambient_pressure']} kPa", s)
    if print_Rfactor:
        s = add_string("GoF = ", s)
    if "_refine_ls_goodness_of_fit_all" in cifpat:
        s += f"{cifpat['_refine_ls_goodness_of_fit_all']:.3f}"
    if (yobs and ycalc) and (yobs != "None" and ycalc != "None"):
        gof = parse_cif.calc_gof_approx(cifpat, yobs, ycalc)
        s = add_string(f"{gof:.3f}", s, brackets=True)
    if print_Rfactor:
        s = add_string("Rwp = ", s)
    if "_pd_proc_ls_prof_wr_factor" in cifpat:
        s += f"{cifpat['_pd_proc_ls_prof_wr_factor'] * 100:.2f}%"
    if (yobs and ycalc) and (yobs != "None" and ycalc != "None"):
        rwp = parse_cif.calc_rwp(cifpat, yobs, ycalc)
        s = add_string(f"{rwp * 100:.2f}%", s, brackets=True)
    return s


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

        self.previous_single_plot_state = {"pattern": "", "change_data": False,
                                           "x_ordinate": "", "y_ordinates": ["None"],
                                           "plot_hkls": {}, "plot_diff": False, "plot_cchi2": False, "plot_norm_int": False,
                                           "axis_scale": {},
                                           "data_x_lim": None, "data_y_lim": None,
                                           "zoomed_x_lim": None, "zoomed_y_lim": None}

        self.cif: dict = cif
        self.dpi = 100

        self.qpa = self.get_all_qpa()

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

    def get_all_scaled_xy_data(self, x_ordinate: str, y_ordinate: str, axis_scale: dict) -> Tuple[List, List, List[str]]:
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

    def get_all_xyz_znorm_data(self, x_ordinate: str, y_ordinate: str, z_ordinate: str, z_norm_ordinate: str) -> Tuple[Any, Any, np.ndarray, np.ndarray, List[Any]]:
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

    def get_all_qpa(self) -> dict:
        all_phases = set()
        # get all phase names
        for pattern in self.cif:
            cifpat = self.cif[pattern]
            if "str" not in cifpat:
                continue
            for phase in cifpat["str"]:
                all_phases.add(cifpat["str"][phase]["_pd_phase_name"])
        d = {phase: [] for phase in all_phases}
        # get all phase wt%
        for i, pattern in enumerate(self.cif, start=1):
            cifpat = self.cif[pattern]
            if "str" not in cifpat:
                continue
            for phase in cifpat["str"]:
                try:
                    qpa = cifpat["str"][phase]["_pd_phase_mass_%"]
                except KeyError:
                    qpa = None
                phase_name = cifpat["str"][phase]["_pd_phase_name"]
                d[phase_name].append(qpa)
            for phase, qpa_list in d.items():
                if len(qpa_list) != i:
                    d[phase].append(np.nan)
        return d

    def single_update_plot(self, pattern: str, x_ordinate: str, y_ordinates: List[str],
                           plot_hkls: dict, plot_diff: bool, plot_cchi2: bool, plot_norm_int: bool,
                           axis_scale: dict,
                           fig: Figure, ax: Axes) -> Tuple[Figure, Axes, Tuple, Tuple]:
        # todo: look at https://stackoverflow.com/a/63152341/36061 for idea on zooming
        single_height_px = fig.get_size_inches()[1] * self.dpi if fig is not None else 382  # this is needed for the hkl position calculations
        # if single_fig is None or single_ax is None:
        zoomed_x_lim = None
        zoomed_y_lim = None
        if fig:
            zoomed_x_lim = ax.get_xlim()
            zoomed_y_lim = ax.get_ylim()
            fig.clear()
        fig = Figure(figsize=(6, 3), dpi=self.dpi)
        ax = fig.add_subplot()
        # fig.set_tight_layout(True)  # https://github.com/matplotlib/matplotlib/issues/21970 https://github.com/matplotlib/matplotlib/issues/11059
        ax.margins(x=0)

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
                    # this is to plot the 'zero' line for the diff plot
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
            single_hovertexts, single_hkl_artists = self.plot_hkls(plot_hkls["below"], cifpat,
                                                                   x_ordinate, x, ys, axis_scale,
                                                                   min_plot, max_plot, 0, True, self.dpi,
                                                                   single_height_px, ax)
            add_hovertext_to_each_point(single_hkl_artists, single_hovertexts)

        if plot_cchi2:
            flip_cchi2 = x_ordinate in {"d", "_pd_proc_d_spacing"}
            ax2 = self.single_plot_cchi2(cifpat, x, [y_ordinates[0], y_ordinates[1]], axis_scale, cchi2_zero, flip_cchi2, ax)

        if not plot_cchi2:
            ax.legend(frameon=False, loc='upper right')  # loc='best')

        if plot_norm_int:
            y_axis_title = "Normalised counts"
        elif "intensity" in y_ordinates[0]:
            y_axis_title = "Intensity (arb. units)"
        else:
            y_axis_title = "Counts"

        wavelength = parse_cif.get_from_cif(cifpat, "wavelength")
        x_axis_title, y_axis_title = _scale_xy_title(_x_axis_title(x_ordinate, wavelength), y_axis_title, axis_scale)

        ax.set_xlabel(x_axis_title)
        ax.set_ylabel(y_axis_title)
        fig.suptitle(pattern, x=fig.subplotpars.left, horizontalalignment="left")
        fig.subplots_adjust(top=0.9)

        subtitle = make_subtitle_string(cifpat, yobs=y_ordinates[0], ycalc=y_ordinates[1])
        if subtitle:
            ax.set_title(subtitle, loc="left")

        if x_ordinate in {"d", "_pd_proc_d_spacing"}:
            ax.invert_xaxis()
        # https://stackoverflow.com/a/30506077/36061
        if plot_cchi2:
            ax.set_zorder(ax2.get_zorder() + 1)
            ax.patch.set_visible(False)

        # now I need to set up all the checks to see if I want to push new views onto the home stack
        #  and how to reset the zoom.
        reset_zoomed_to_plt_x_min = False
        reset_zoomed_to_plt_x_max = False
        reset_zoomed_to_plt_y_min = False
        reset_zoomed_to_plt_y_max = False
        data_x_lim = ax.get_xlim()
        data_y_lim = ax.get_ylim()
        zoomed_x_lim = ax.get_xlim() if not zoomed_x_lim else zoomed_x_lim
        zoomed_y_lim = ax.get_ylim() if not zoomed_y_lim else zoomed_y_lim

        # here go the rules on changing zoom to match the current data
        if (
            self.previous_single_plot_state["pattern"] != pattern
            # if the zoom view of the data is the entire data, then the view of the new data is the
            #  entire view of the new data, irrespective of the limits of the previous zoom
            and isclose_listlike(self.previous_single_plot_state["data_x_lim"], zoomed_x_lim)
            and isclose_listlike(self.previous_single_plot_state["data_y_lim"], zoomed_y_lim)
        ):
            reset_zoomed_to_plt_x_min = True
            reset_zoomed_to_plt_x_max = True
            reset_zoomed_to_plt_y_min = True
            reset_zoomed_to_plt_y_max = True
        if self.previous_single_plot_state["x_ordinate"] != x_ordinate:
            reset_zoomed_to_plt_x_min = True
            reset_zoomed_to_plt_x_max = True
        if self.previous_single_plot_state["y_ordinates"] != y_ordinates:
            reset_zoomed_to_plt_y_min = True
            reset_zoomed_to_plt_y_max = True
        if self.previous_single_plot_state["plot_diff"] != plot_diff:
            reset_zoomed_to_plt_y_min = True
        if self.previous_single_plot_state["plot_hkls"] != plot_hkls:
            reset_zoomed_to_plt_y_min = True

        if self.previous_single_plot_state["plot_norm_int"] != plot_norm_int:
            # _, (ymin, ymax) = get_zoomed_data_min_max(ax, zoomed_x_lim, data_y_lim)
            # yrange = (ymax - ymin)
            # ymid = yrange / 2
            # yrange = (yrange * 1.07) / 2
            zoomed_y_lim = data_y_lim
        if self.previous_single_plot_state["axis_scale"] not in [axis_scale, {}]:
            ordinate, _ = get_first_different_kv_pair(self.previous_single_plot_state["axis_scale"], axis_scale)
            if ordinate == "x":
                zoomed_xmin = rescale_val(zoomed_x_lim[0], self.previous_single_plot_state["axis_scale"], axis_scale, ordinate)
                zoomed_xmax = rescale_val(zoomed_x_lim[1], self.previous_single_plot_state["axis_scale"], axis_scale, ordinate)
                zoomed_x_lim = (zoomed_xmin, zoomed_xmax)
            elif ordinate == "y":
                zoomed_ymin = rescale_val(zoomed_y_lim[0], self.previous_single_plot_state["axis_scale"], axis_scale, ordinate)
                zoomed_ymax = rescale_val(zoomed_y_lim[1], self.previous_single_plot_state["axis_scale"], axis_scale, ordinate)
                zoomed_y_lim = (zoomed_ymin, zoomed_ymax)

        if reset_zoomed_to_plt_x_min:
            zoomed_x_lim = (data_x_lim[0], zoomed_x_lim[1])
        if reset_zoomed_to_plt_x_max:
            zoomed_x_lim = (zoomed_x_lim[0], data_x_lim[1])
        if reset_zoomed_to_plt_y_min:
            zoomed_y_lim = (data_y_lim[0], zoomed_y_lim[1])
        if reset_zoomed_to_plt_y_max:
            zoomed_y_lim = (zoomed_y_lim[0], data_y_lim[1])

        # Now it's time to set up the previous-state dictionary for the next time this function is called.
        #  Need to do it right at the end so nothing else changes
        self.previous_single_plot_state["pattern"] = pattern
        self.previous_single_plot_state["x_ordinate"] = x_ordinate
        self.previous_single_plot_state["y_ordinates"] = y_ordinates
        self.previous_single_plot_state["plot_hkls"] = plot_hkls
        self.previous_single_plot_state["plot_diff"] = plot_diff
        self.previous_single_plot_state["plot_cchi2"] = plot_cchi2
        self.previous_single_plot_state["plot_norm_int"] = plot_norm_int
        self.previous_single_plot_state["axis_scale"] = axis_scale
        self.previous_single_plot_state["data_x_lim"] = ax.get_xlim()
        self.previous_single_plot_state["data_y_lim"] = ax.get_ylim()
        self.previous_single_plot_state["zoomed_x_lim"] = zoomed_x_lim
        self.previous_single_plot_state["zoomed_y_lim"] = zoomed_y_lim

        return fig, ax, zoomed_x_lim, zoomed_y_lim

    def plot_hkls(self, plot_below: bool, cifpat: dict, x_ordinate: str, x, ys,
                  axis_scale: dict, y_min: float, y_max: float, hkl_y_offset: float,
                  single_plot: bool,
                  dpi: int, single_height_px: int, ax: Axes):

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
        for i, phase in enumerate(cifpat["str"]):
            if hkl_x_ordinate not in cifpat["str"][phase]:
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

            phase_wt_pct = f'– {cifpat["str"][phase]["_pd_phase_mass_%"]} wt%' if "_pd_phase_mass_%" in cifpat["str"][phase] else ""

            hkl_y = hkl_y * scalar + hkl_y_offset
            idx = i % len(TABLEAU_COLOR_VALUES)
            phasename = cifpat["str"][phase]["_pd_phase_name"] if "_pd_phase_name" in cifpat["str"][phase] else phase
            hkl_tick, = ax.plot(hkl_x, hkl_y, label=f" {phasename} {phase_wt_pct}", marker=markerstyle, linestyle="none", markersize=hkl_markersize_pt,
                                color=TABLEAU_COLOR_VALUES[idx])
            hkl_artists.append(hkl_tick)
            if "refln_hovertext" in cifpat["str"][phase]:
                phasename = cifpat["str"][phase]["_pd_phase_name"] if "_pd_phase_name" in cifpat["str"][phase] else phase
                hovertext = [f'{phasename}: {hkls}' for hkls in cifpat["str"][phase]["refln_hovertext"]]
                hovertexts.append(hovertext)
            else:
                hovertexts.append([phase] * len(hkl_x))

        return hovertexts, hkl_artists

    def single_plot_cchi2(self, cifpat: dict, x, cchi2_y_ordinates: List[str], axis_scale: dict, cchi2_zero: float, flip_cchi2: bool,
                          ax1: Axes) -> Axes:
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

        if array_strictly_increasing_or_equal(x) != array_strictly_increasing_or_equal(cchi2):
            flip_cchi2 = True
        else:
            pass

        if flip_cchi2:
            # this keeps the differences between datapoints, but inverts their sign, so
            #  the list ends up changing from increasing to decreasing, or vice versa.
            #  This is done to counteract an inverted plotting axis so I can keep the
            #  cchi2 plot increasing from left to right
            ylag = np.diff(cchi2, prepend=cchi2[0])
            ynew = np.zeros(len(cchi2))
            ynew[0] = cchi2[-1]
            for i in range(1, len(ynew)):
                ynew[i] = ynew[i - 1] - ylag[i]
            cchi2 = ynew

        ax2 = ax1.twinx()

        ax2.plot(x, cchi2, label=f" c\u03C7\u00b2",
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
                          plot_hkls: dict, plot_norm_int: dict,
                          axis_scale: dict,
                          fig: Figure) -> Figure:

        if fig:
            fig.clear()
        fig = Figure(figsize=(6, 3), dpi=self.dpi)
        ax = fig.add_subplot()
        fig.set_tight_layout(True)  # https://github.com/matplotlib/matplotlib/issues/21970 https://github.com/matplotlib/matplotlib/issues/11059
        ax.margins(x=0)

        # xs and ys hold unscaled values
        xs, ys, plot_list = self.get_all_xy_data(x_ordinate, y_ordinate)
        offset = _scale_y_ordinate(offset, axis_scale)

        if plot_norm_int["norm_int"]:
            y_norms = self.get_xy_ynorm_data(x_ordinate, plot_norm_int["y_ordinate_for_norm"])
        else:
            y_norms = [np.ones(len(xi)) for xi in xs]

        # compile all the patterns' data
        # need to loop backwards so that the data comes out in the correct order for plotting
        hover_texts = []
        for j in range(len(plot_list) - 1, -1, -1):
            pattern = plot_list[j]
            x, y = xs[j], ys[j] * y_norms[j]
            x, y = _scale_xy_ordinates(x, y, axis_scale)
            label = pattern if not plot_norm_int["norm_int"] else f"{pattern} (norm.)"
            ax.plot(x, y + j * offset, label=label)
            label = make_subtitle_string(self.cif[pattern], label)
            hover_texts.append(label)

        # https://mplcursors.readthedocs.io/en/stable/examples/artist_labels.html
        stack_artists = ax.get_children()
        mplcursors.cursor(stack_artists,
                          hover=mplcursors.HoverMode.Transient).connect("add", lambda sel: sel.annotation.set_text(hover_texts[stack_artists.index(sel.artist)]))

        if plot_hkls["above"] or plot_hkls["below"]:
            stack_hovertexts = []
            stack_hkl_artists = []
            for j in range(len(plot_list) - 1, -1, -1):
                cifpat = self.cif[plot_list[j]]
                hkl_y_offset = j * offset
                x, y = xs[j], ys[j] * y_norms[j]
                x, y = _scale_xy_ordinates(x, y, axis_scale)
                if "str" not in cifpat:
                    continue
                tmp_hovertexts, tmp_hkl_artists = self.plot_hkls(plot_hkls["below"], cifpat, x_ordinate, x, [y, None],
                                                                 axis_scale, 0, 0, hkl_y_offset, False, self.dpi, -1, ax)
                stack_hovertexts.extend(tmp_hovertexts)
                stack_hkl_artists.extend(tmp_hkl_artists)

            add_hovertext_to_each_point(stack_hkl_artists, stack_hovertexts)
        # end hkl if

        if x_ordinate in {"d", "_pd_proc_d_spacing"}:
            ax.invert_xaxis()

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
                            plot_hkls: bool, plot_norm_int: dict, plot_metadata: str,
                            axis_scale: dict,
                            fig: Figure) -> Figure:
        if fig:
            fig.clear()
        fig = Figure(figsize=(6, 3), dpi=self.dpi)
        if plot_metadata:
            ax, ax1 = fig.subplots(1, 2, gridspec_kw={'width_ratios': [2, 1]}, sharey=True)
        else:
            ax = fig.subplots(1, 1)
        fig.set_tight_layout(True)  # https://github.com/matplotlib/matplotlib/issues/21970 https://github.com/matplotlib/matplotlib/issues/11059
        ax.margins(x=0)

        # am I plotting the data I already have? If all the ordinates are the same, then I don't need to regrab all of the data
        #  and I can just use what I already have.
        if (
            self.surface_plot_data["x_ordinate"] == x_ordinate and
            self.surface_plot_data["y_ordinate"] == y_ordinate and
            self.surface_plot_data["z_ordinate"] == z_ordinate
        ):
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
            xx, yy, zz = _scale_xyz_ordinates(xx, yy, zz * znorm, axis_scale)
        else:
            xx, yy, zz = _scale_xyz_ordinates(xx, yy, zz, axis_scale)

        pcm = ax.pcolormesh(xx, yy, zz, shading='nearest', cmap=self.surface_z_color)

        if x_ordinate in {"d", "_pd_proc_d_spacing"}:
            ax.invert_xaxis()

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

        ax.set_xlabel(x_axis_title)
        ax.set_ylabel(y_axis_title)

        # make second subplot here
        if plot_metadata:  # string == "temp", "pres", "qpa"
            y = [_scale_y_ordinate(i + 1, axis_scale) for i in range(len(self.cif))]
            if plot_metadata != "qpa":
                second_plot = []
                for pattern in self.cif:
                    cifpat = self.cif[pattern]
                    if plot_metadata == "temp":
                        try:
                            second_plot.append(cifpat["_diffrn_ambient_temperature"])
                        except KeyError:
                            second_plot.append(None)
                        ax1.set_xlabel("Temperature (K)")
                    elif plot_metadata == "pres":
                        try:
                            second_plot.append(cifpat["_diffrn_ambient_pressure"])
                        except KeyError:
                            second_plot.append(None)
                        ax1.set_xlabel("Pressure (kPa)")
                    elif plot_metadata == "rwp":
                        try:
                            second_plot.append(cifpat["_pd_proc_ls_prof_wr_factor"] * 100)
                        except KeyError:
                            second_plot.append(None)
                        ax1.set_xlabel("Rwp (%)")
                    elif plot_metadata == "gof":
                        try:
                            second_plot.append(cifpat["_refine_ls_goodness_of_fit_all"])
                        except KeyError:
                            second_plot.append(None)
                        ax1.set_xlabel("GoF")
                ax1.plot(second_plot, y, marker="o")
            else:
                amor_qpa = 100 * np.ones(len(y))
                for phase in self.qpa:
                    ax1.plot(self.qpa[phase], y, label=phase)
                    amor_qpa = np.subtract(amor_qpa, np.nan_to_num(self.qpa[phase]))
                if np.any(amor_qpa > 0.5):
                    ax1.plot(amor_qpa, y, label="Unknown", color="black", linestyle='dashed')
                surface_qpa_artists = ax1.get_children()
                mplcursors.cursor(surface_qpa_artists, hover=mplcursors.HoverMode.Transient).connect("add", lambda sel: sel.annotation.set_text(sel.artist.get_label()))
                ax1.set_xlabel("Weight percent (wt%)")
                ax1.legend()
            ax1.grid(True, color='lightgrey')
            fig.colorbar(pcm, ax=ax1, label=z_axis_title)  # this is the code that adds the colour bar.
        else:
            fig.colorbar(pcm, ax=ax, label=z_axis_title)

        return fig

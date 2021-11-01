from glob import glob
import numpy as np
import CifFile
#import plotly.graph_objects as go

X_AXIS_KEYS = ["_pd_meas_2theta_scan", "_pd_proc_2theta_corrected", "_pd_meas_time_of_flight",
               "_pd_meas_position", "_pd_proc_energy_incident", "_pd_proc_wavelength",
               "_pd_proc_d_spacing", "_pd_proc_recip_len_Q"]

Y_AXIS_KEYS = ["_pd_meas_counts_total", "_pd_meas_intensity_total",
               "_pd_proc_intensity_total", "_pd_proc_intensity_net",
               "_pd_calc_intensity_total", "_pd_calc_intensity_net",
               "_pd_meas_counts_background", "_pd_meas_counts_container", "_pd_meas_intensity_background",
               "_pd_meas_intensity_container", "_pd_proc_intensity_bkg_fix", "_pd_proc_intensity_bkg_calc",
               "_pd_proc_ls_weight"]

TICK_MARKS = ["_refln_d_spacing", "_refln_index_h", "_refln_index_k", "_refln_index_l"]

WAVELENGTH = ["_diffrn_radiation_wavelength", "_refln_intensity_calc", "_cell_measurement_wavelength",
              "_diffrn_radiation_wavelength_id", "_diffrn_radiation_wavelength_wt"]

PHASE_NAME = ["_pd_phase_name", "_chemical_name_common", "_chemical_name_mineral",
              "_pd_phase_id", "_pd_block_id", "_pd_phase_block_id"]


class Node:
    def __init__(self, cifdict, parent=None, patterns=None, structures=None, siblings=None):
        self.cifdict = cifdict
        self.parent = parent
        self.patterns = patterns
        self.structures = structures
        self.siblings = siblings

        # need to call it directly, as I need to guarrentee that it is the one belonging to this data block
        self.id = self.cifdict["_pd_block_id"]
        self.wavelength = self.get_wavelength()
        self.name = None
        self.hkl_tooltip = self.generate_hkl_tooltip_text()

        # converting all the string lists into numpy arrays so I can actually plot them
        for key in X_AXIS_KEYS:
            if key in self.cifdict:
                self.cifdict[key] = cifstrlist_to_nparray_noerrs(self.cifdict[key])

        for key in Y_AXIS_KEYS:
            if key in self.cifdict:
                self.cifdict[key] = cifstrlist_to_nparray_errs(self.cifdict[key])

        if "_refln_d_spacing" in self.cifdict:
            self.cifdict["_refln_d_spacing"] = cifstrlist_to_nparray_noerrs(self.cifdict["_refln_d_spacing"])

        self.generate_pd_meas_2theta_scan()
        self.generate_pd_proc_2theta_corrected()
        self.generate_pd_proc_intensity_net()
        self.generate_pd_calc_intensity_net()
        self.generate_pd_proc_recip_len_Q()
        self.generate_pd_proc_d_spacing()

        for key in PHASE_NAME:
            if key in self.cifdict:
                self.name = self.cifdict[key]
                break

    def get_wavelength(self):
        """
        Get the value of the wavelength from information in the datablock, or if it isn't there, it goes through oll
        of it's siblings, and finally its parent. If it doesn't find it, return None
        :return: the wavelength in angstrom, or None
        """
        try:
            return self.find_value("_diffrn_radiation_wavelength")
        except KeyError:
            try:
                return self.find_value("_cell_measurement_wavelength")
            except KeyError:
                return None

    def key_exists(self, key):
        """
        Searches the self.cifdict for a key, and if not found, the siblings, and finally parent.
        Returns True if found at least once, otherwise False
        :param key: string representing a cif dict key
        :return: boolean represent the presence of the key in the data structure.
        """
        if key in self.cifdict:
            return True
        else:
            for pattern in self.patterns:
                if key in pattern.cifdict:
                    return True
            for structure in self.structures:
                if key in structure.cifdict:
                    return True
        return key in self.parent.cifdict

    def find_value(self, key):
        """
        Given a key, find the associated value in the Node, or if not there, ask each sibling, and if not
        there, ask the parent. If not found, thrown a KeyError
        :param key: a string denoting a key in a cif dictionary
        :return: the string value associated with the given key
        :except: KeyError if key is not found
        """
        if key in self.cifdict:  # checks if the key is there before asking for the value
            return self.cifdict[key]
        else:
            for pattern in self.patterns:
                if key in pattern.cifdict:
                    return pattern.cifdict[key]
            for structure in self.structures:
                if key in structure.cifdict:
                    return structure.cifdict[key]
        return self.parent.cifdict[key]  # doesn't check, and so will throw a KeyError if it isn't there.

    def generate_pd_meas_2theta_scan(self):
        """
        If the keys "_pd_meas_2theta_range_min", "_pd_meas_2theta_range_max", "_pd_meas_2theta_range_inc"
        are present in a data block, and "_pd_meas_2theta_scan" is not defined, calculate the individual
        2Th values from the start, step, stop values, and add a numpy array to the dictionary
        :return: None
        """

        if all(key in self.cifdict for key in ("_pd_meas_2theta_range_min", "_pd_meas_2theta_range_max",
                                               "_pd_meas_2theta_range_inc")) and \
                "_pd_meas_2theta_scan" not in self.cifdict:
            start = float(self.cifdict["_pd_meas_2theta_range_min"])
            step = float(self.cifdict["_pd_meas_2theta_range_inc"])
            stop = float(self.cifdict["_pd_meas_2theta_range_max"])
            n = round(1 + (stop - start) / step)
            array = np.linspace(start, stop, num=n)
            self.cifdict["_pd_meas_2theta_scan"] = array

    def generate_pd_proc_2theta_corrected(self):
        """
        If the keys "_pd_proc_2theta_range_min", "_pd_proc_2theta_range_max", "_pd_proc_2theta_range_inc"
        are present in a data block, and "_pd_proc_2theta_corrected" is not defined, calculate the individual
        2Th values from the start, step, stop values, and add a numpy array to the dictionary
        :return: None
        """

        if all(key in self.cifdict for key in ("_pd_proc_2theta_range_min", "_pd_proc_2theta_range_max",
                                               "_pd_proc_2theta_range_inc")) and \
                "_pd_proc_2theta_corrected" not in self.cifdict:
            start = float(self.cifdict["_pd_proc_2theta_range_min"])
            step = float(self.cifdict["_pd_proc_2theta_range_inc"])
            stop = float(self.cifdict["_pd_proc_2theta_range_max"])
            n = round(1 + (stop - start) / step)
            array = np.linspace(start, stop, num=n)
            self.cifdict["_pd_proc_2theta_corrected"] = array

    def generate_pd_proc_intensity_net(self):
        """
        If the keys "_pd_proc_intensity_total", and "_pd_proc_intensity_bkg_calc" are present in a data block,
        and "_pd_proc_intensity_net" is not defined, calculate the bkg-corrected intensities, and add a numpy
        array to the dictionary
        :return: None
        """
        if all(key in self.cifdict for key in ("_pd_proc_intensity_total", "_pd_proc_intensity_bkg_calc")) and \
                "_pd_proc_intensity_net" not in self.cifdict:
            array = self.cifdict["_pd_proc_intensity_total"] - self.cifdict["_pd_proc_intensity_bkg_calc"]
            self.cifdict["_pd_proc_intensity_net"] = array

    def generate_pd_calc_intensity_net(self):
        """
        If the keys "_pd_calc_intensity_total", and "_pd_proc_intensity_bkg_calc" are present in a data block,
        and "_pd_calc_intensity_net" is not defined, calculate the bkg-corrected intensities, and add a numpy
        array to the dictionary
        :return: None
        """
        if all(key in self.cifdict for key in ("_pd_calc_intensity_total", "_pd_proc_intensity_bkg_calc")) and \
                "_pd_calc_intensity_net" not in self.cifdict:
            print(type(self.cifdict["_pd_calc_intensity_total"]))
            array = np.subtract(self.cifdict["_pd_calc_intensity_total"], self.cifdict["_pd_proc_intensity_bkg_calc"])
            self.cifdict["_pd_calc_intensity_net"] = array

    def generate_pd_proc_d_spacing(self):
        """
        If the keys "_pd_meas_2theta_scan", or "_pd_proc_2theta_corrected" are present in a data block,
        and "_pd_proc_d_spacing" is not defined, calculate the individual
        d values from the proc values, or if not present, the meas values, and add a numpy array to the dictionary
        :return: None
        """
        if any(key in self.cifdict for key in ("_pd_meas_2theta_scan", "_pd_proc_2theta_corrected")) and \
                "_pd_proc_d_spacing" not in self.cifdict:
            if "_pd_proc_2theta_corrected" in self.cifdict:
                self.cifdict["_pd_proc_d_spacing"] = convert_2theta_to_d(
                    cifstrlist_to_nparray_noerrs(self.cifdict["_pd_proc_2theta_corrected"]), self.wavelength)
            else:  # using meas
                self.cifdict["_pd_proc_d_spacing"] = convert_2theta_to_d(
                    cifstrlist_to_nparray_noerrs(self.cifdict["_pd_meas_2theta_scan"]), self.wavelength)

    def generate_pd_proc_recip_len_Q(self):
        """
        If the keys "_pd_meas_2theta_scan", or "_pd_proc_2theta_corrected" are present in a data block,
        and "_pd_proc_recip_len_Q" is not defined, calculate the individual
        q values from the proc values, or if not present, the meas values, and add a numpy array to the dictionary
        :return: None
        """
        if any(key in self.cifdict for key in ("_pd_meas_2theta_scan", "_pd_proc_2theta_corrected")) and \
                "_pd_proc_recip_len_Q" not in self.cifdict:
            if "_pd_proc_2theta_corrected" in self.cifdict:
                self.cifdict["_pd_proc_recip_len_Q"] = convert_2theta_to_q(
                    cifstrlist_to_nparray_noerrs(self.cifdict["_pd_proc_2theta_corrected"]), self.wavelength)
            else:  # using meas
                self.cifdict["_pd_proc_recip_len_Q"] = convert_2theta_to_q(
                    cifstrlist_to_nparray_noerrs(self.cifdict["_pd_meas_2theta_scan"]), self.wavelength)

    def generate_hkl_tooltip_text(self):
        if all(key in self.cifdict for key in TICK_MARKS):
            return [f"{h} {k} {l} d={d} \u212B" for h, k, l, d in
                    zip(self.cifdict["_refln_index_h"],
                        self.cifdict["_refln_index_k"],
                        self.cifdict["_refln_index_l"],
                        self.cifdict["_refln_d_spacing"])]


def make_cif_tree(cif_file):
    pass


def cifstr_to_double(s):
    """
    Converts a cif string to a double.
    Silently drops any error term. Returns 0 if the string is "." or "?"
    :param s: the cif string
    :return: double representation
    """
    if s == "." or s == "?":
        return 0.0

    bracket_val = s.find("(")
    if bracket_val == -1:  # there is no bracket
        return float(s)
    else:  # there is a bracket
        return float(s[0:bracket_val])


def cifstr_to_double_tuple(s):
    """
    Converts a cif string to a tuple containing a double value and a double error
    Returns (0,0) if the string is "." or "?"
    :param s: the cif string
    :return: (val, err) or (val,0) or Returns (0,0) if the string is "." or "?"
    """
    if s == "." or s == "?":
        return (0.0, 0.0)

    # now there are no missing or unknown values
    first_bracket = s.find("(")

    if first_bracket == -1:  # there is no bracket
        return (float(s), 0.0)

    # now the value has an error
    second_bracket = s.find(")")
    val_s = s[0:first_bracket]
    err_s = s[first_bracket + 1:second_bracket]

    # find the power of ten by which I need to change the err_s in order to give it the
    #  correct value when disassociated from the value - ie give it the right number of
    #  decimal places
    if "." not in val_s:
        val_s += "."  # ie 10 == 10., but now the string calculations below actually work
    dps = len(val_s) - val_s.find(".") - 1
    power_of_ten = dps - len(err_s)

    if power_of_ten >= 0:
        err_s = "0." + ("0" * power_of_ten) + err_s
    else:
        power_of_ten = -power_of_ten
        err_s = err_s[:power_of_ten] + "." + err_s[power_of_ten:]

    return (float(val_s), float(err_s))


def cifstrlist_to_nparray_errs(sl):
    """
    converts a list of strings representing floats into a numpy array iwth two columns.
    The first column contains the values. The second column contains the errors.
    If no error is given, then the value 0 is returned.

    Can be used as: val, err = cifstrlist_to_nparray(sl)

    :param sl: list of strings containing numeric values
    :return: np.array of
    """
    return np.array([cifstr_to_double_tuple(d) for d in sl]).transpose()


def cifstrlist_to_nparray_noerrs(sl):
    """
    converts a list of strings representing floats into a numpy array.
    Any given errors are silently dropped

    Can be used as: val = cifstrlist_to_nparray_noerrs(sl)

    :param sl: list of strings containing numeric values
    :return: np.array of doubles
    """
    return np.array([cifstr_to_double(d) for d in sl])


def convert_2theta_to_q(nparray, lam):
    """
    Take a numpy array of 2theta values in degrees, and a wavelength, and return a numpy array of q-values, where
    q = 4 Pi Sin(Th) / lam
    :param nparray: numpy array of 2Th values in degrees
    :param lam: wavelength in Angstroms
    :return: array of q values in inv angstrom.
    """
    sin_arg = np.multiply(nparray, np.pi / 360.0)
    return_me = np.multiply(4.0 * np.pi / lam, np.sin(sin_arg))
    return return_me


def convert_2theta_to_d(nparray, lam):
    """
    Take a numpy array of 2theta values in degrees, and a wavelength, and return a numpy array of d-spacings, where
    d = lam / (2 Sin(Th))
    :param nparray: numpy array of 2Th values in degrees
    :param lam: wavelength in Angstroms
    :return: array of d spacings in angstroms.
    """
    sin_arg = np.multiply(nparray, np.pi / 360.0)
    bottom = np.multiply(2.0, np.sin(sin_arg))
    return_me = np.multiply(lam, np.reciprocal(bottom))
    return return_me


def convert_d_to_2theta(nparray, lam):
    """
    Take a numpy array of d-spacing values in angstomrs, and a wavelength, and return a numpy array of 2theta deg, where
    2Th = 2 arcsin(lam/(2d))
    :param nparray: numpy array of d-spacing values in angstroms
    :param lam: wavelength in Angstroms
    :return: array of 2theta values in degrees
    """
    scale = 2 * 180.0 / np.pi
    scale_arr = np.multiply(2, nparray)
    arg = np.multiply(lam, np.reciprocal(scale_arr))
    angle = np.arcsin(arg)
    return_me = np.multiply(scale, angle)
    return return_me


# these keys are important for getting other information about the experiment
#  Idea: use _refln_intensity_calc to display phase ID results.
OTHER_KEYS = ["_refln_intensity_calc", "_pd_meas_number_of_points", "_pd_proc_number_of_points"]

import cProfile, pstats

def main():
    # a shortcut to reference the correct column in a numpy array that contains values and errors
    VAL = 0
    ERR = 1

    print("Reading cif")
    ciffile = "../../data/ideal.cif"
    #profiler = cProfile.Profile()
    #profiler.enable()

    # scantype="flex" uses C library for some of the parsing. A lot faster than pure python, but can't do CIF2.
    cif = CifFile.ReadCif(ciffile, scantype="flex", grammar="1.1", scoping="dictionary", permissive=False)
    #cif = CifFile.ReadCif(ciffile, grammar="1.1", scoping="dictionary", permissive=False)

    #profiler.disable()
    #stats = pstats.Stats(profiler).sort_stats('cumtime')
    #stats.print_stats()


    # A = open("diff_data.txt", "w")
    # B = open("hkl_data.txt", "w")
    # Ca = open("phase_overlay.txt", "w")
    # Cb = open("pattern_overlay.txt", "w")
    #
    # A.write(f"_pd_block_id\t_pd_meas_2theta_scan\t_pd_meas_intensity_total\t"
    #         f"_pd_proc_ls_weight\t_pd_calc_intensity_total\t_pd_proc_intensity_bkg_calc\t_diffrn_radiation_wavelength\n")
    # B.write(f"_pd_block_id\t_refln_index_h\t_refln_index_k\t"
    #         f"_refln_index_l\t_pd_refln_phase_id\t_refln_d_spacing\t_diffrn_radiation_wavelength\n")
    # Ca.write(f"_pd_block_id\t_pd_phase_id\t_pd_phase_block_id\t_pd_phase_mass_%\n")
    # Cb.write(f"_pd_block_id\t_diffrn_radiation_wavelength\t_diffrn_ambient_temperature\n")
    #
    # wavelength = 0.0
    # temperature = 0.0
    # for key in cif.keys():
    #     if "_diffrn_radiation_wavelength" in cif[key]:
    #         wavelength = cif[key]["_diffrn_radiation_wavelength"]
    #     if "_diffrn_ambient_temperature" in cif[key]:
    #         temperature = cif[key]["_diffrn_ambient_temperature"]
    #     if "_pd_meas_2theta_scan" not in cif[key]:
    #         continue
    #
    #     print(f"doing {key}")
    #     pattern = cif[key]
    #     pd_block_id = pattern["_pd_block_id"]
    #
    #     # First, do things with the diffraction pattern
    #     pattern_data = zip(pattern["_pd_meas_2theta_scan"],
    #                        pattern["_pd_meas_intensity_total"],
    #                        pattern["_pd_proc_ls_weight"],
    #                        pattern["_pd_calc_intensity_total"],
    #                        pattern["_pd_proc_intensity_bkg_calc"])
    #     for a, b, c, d, e in pattern_data:
    #         A.write(f'{pd_block_id}\t{a}\t{b}\t{c}\t{d}\t{e}\t{wavelength}\n')
    #
    #     # Second, do the HKL tick mark information
    #     hkl_data = zip(pattern["_refln_index_h"],
    #                    pattern["_refln_index_k"],
    #                    pattern["_refln_index_l"],
    #                    pattern["_pd_refln_phase_id"],
    #                    pattern["_refln_d_spacing"])
    #     for a, b, c, d, e in hkl_data:
    #         B.write(f'{pd_block_id}\t{a}\t{b}\t{c}\t{d}\t{e}\t{wavelength}\n')
    #
    #     # Third, do the wt% values
    #     wtf_data = zip(pattern["_pd_phase_id"],
    #                    pattern["_pd_phase_block_id"],
    #                    pattern["_pd_phase_mass_%"])
    #     for a, b, c in wtf_data:
    #         Ca.write(f'{pd_block_id}\t{a}\t{b}\t{c}\n')
    #
    #     # Fourth, do the temperature (and pressure, and collection time...)
    #     Cb.write(f'{pd_block_id}\t{wavelength}\t{temperature}\n')
    #
    # A.close()
    # B.close()
    # Ca.close()
    # Cb.close()

    # node = Node(cif["alumina_publ"])

    # for key, item in node.cifdict.items():
    # print(f"{key} : {item}")

    # print(node.wavelength)
    #
    # x = node.cifdict["_pd_meas_2theta_scan"]
    # yobs = node.cifdict["_pd_meas_intensity_total"][VAL]
    # ycalc = node.cifdict["_pd_calc_intensity_total"][VAL]
    # bkg = node.cifdict["_pd_proc_intensity_bkg_calc"][VAL]
    # diff = np.subtract(yobs, ycalc)
    # diff -= max(diff)
    # hkl = convert_d_to_2theta(node.cifdict["_refln_d_spacing"], float(node.wavelength))
    #
    # fig = go.Figure()
    # fig.add_trace(go.Scatter(x=x, y=yobs, name="_pd_meas_intensity_total",
    #                          mode='markers', marker=dict(color='Blue', symbol="cross")))
    # fig.add_trace(go.Scatter(x=x, y=ycalc, name="_pd_calc_intensity_total",
    #                          mode='lines', line=dict(color='Red')))
    # fig.add_trace(go.Scatter(x=x, y=bkg, name="_pd_proc_intensity_bkg_calc",
    #                          mode='lines', line=dict(color='Grey', width=1)))
    # fig.add_trace(go.Scatter(x=x, y=diff, name="Difference",
    #                          mode='lines', line=dict(color='Grey')))
    # fig.add_trace(go.Scatter(x=hkl, y=-1000*np.ones(hkl.size), name="hkl",
    #                          text=node.hkl_tooltip, hovertemplate="%{text}",
    #                          mode='markers', marker=dict(line_color='Green', symbol="line-ns", line_width=2)))
    #
    # fig.update_layout(title=node.id,
    #                   xaxis_title=f'\u00B0 2\u03F4 (\u03BB = {node.wavelength} \u212B)',
    #                   yaxis_title='Intensity',
    #                   legend=dict(
    #                       orientation="h",
    #                       yanchor="bottom",
    #                       y=-0.15,
    #                       xanchor="left"
    #                   )
    #                   )
    # fig.show()


if __name__ == '__main__':
    main()

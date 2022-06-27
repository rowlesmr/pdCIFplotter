import numpy as np
import re
import math
import copy
# from timeit import default_timer as timer   # use as start = timer() ...  end = timer()
from CifFile import CifFile, ReadCif, StarFile, CifBlock
from typing import List, Tuple, Union, Any

DEBUG = False


def pretty(d, indent=0, print_values=True):
    for key, value in d.items():
        print('|  ' * indent + "|--" + str(key))
        if isinstance(value, dict) or isinstance(value, CifFile) or isinstance(value, StarFile.StarBlock):
            pretty(value, indent + 1, print_values=print_values)
        elif print_values:
            print('|  ' * (indent + 1) + "|--" + str(value))


def debug(*args):
    if DEBUG:
        print(*args)


def convert_cif_to_dict(cif: CifFile) -> dict:
    """
    Converts a PyCIFRW CifFile into a normal Python dictionary
    :param cif:
    :return: cif as a dictionary
    """
    key_list = cif.block_input_order
    cif_dict = cif.__dict__["dictionary"]
    # i need to iterate, rather than just copying, as the dictionary order in the PyCIFRW object isn't
    # necessarily the same order as in the original file, and I want to keep the file order, as it
    # probably has some semantic meaning.
    for key in key_list:  # Python >=3.7 keeps dictionary keys in insertion order: https://mail.python.org/pipermail/python-dev/2017-December/151283.html
        cif_dict[key] = cif[key].__dict__["block"]
        for sub_key in cif_dict[key].keys():
            cif_dict[key][sub_key] = cif_dict[key][sub_key][0]
    return cif_dict


def blockname_lookupdict_from_blockid(cif: Union[dict, CifFile]) -> dict:
    """
    To get information from a CIF, you need to know the name of the block (data_'blocknamegoeshere'), but when linking
    between blocks, a block id is used. This function creates a dictionary, which, when given a blockid, returns a
    block name. This means you can get the block corresponding to a blockid
    :param cif:
    :return: dictionary with blockids as keys and blocknames as values.
    """
    keys = cif.keys() if isinstance(cif, dict) else cif.block_input_order
    return {cif[blockname]["_pd_block_id"]: blockname for blockname in keys if "_pd_block_id" in cif[blockname]}


def get_blockname_from_block_id(lookup_dict: dict, block_id: str) -> str:
    """
    Pycifrw makes datablock names all lower case. When I make up a pd_block_id from a dataname, sometimes the user has a
    case-dependent reference somewhere in their CIF, and so I can't find the datablock. This looks in my lookup dictionary
    two ways to see if it can be found.
    :param lookup_dict: the dictionary mapping block_id to datablock
    :param block_id: the block id I want to match
    :return: the matching datablock name
    """
    try:
        return lookup_dict[block_id]
    except KeyError:
        return lookup_dict[block_id.lower()]


def grouped_blocknames(cif: Union[CifFile, dict]) -> dict:
    """
    Looks at all the datablocks in a cif and categorieses them into those that have diffraction pattern information,
    those with crystal structure information, and the others.
    :param cif: a PyCIFRW readcif object
    :return: a dictionary containing lists of datablock names corresponding to "patterns", "structures", and "others". They are order according to appearance in the file
    """
    pattern_datanames = []
    structure_datanames = []
    other_datanames = []

    keys = cif.keys() if isinstance(cif, dict) else cif.block_input_order

    for datablock in keys:
        if any(x in cif[datablock] for x in ParseCIF.COMPLETE_X_LIST):
            pattern_datanames.append(datablock)  # this can include datablocks that have both pattern and structure info
        elif "_cell_length_a" in cif[datablock]:
            structure_datanames.append(datablock)  # This only has structures that have no pattern information
        else:
            other_datanames.append(datablock)
    return {"patterns": pattern_datanames, "structures": structure_datanames, "others": other_datanames}


def get_from_cif(cif: Union[dict, CifFile], itemname: str, default: Any = None):
    """
    Given a cif and a itemname, return the value associated with that blockname if it exists.
    If not, return None.
    :param cif: cif as dictionary or PyCIFRW
    :param itemname: string representing blockname
    :param default: what to return if the itemname doesn't exist in the cif
    :return: whatever is in the blockname, or None if it doesn't exist.
    """
    return cif[itemname] if itemname in cif else default


def get_hkld_ids(structure: Union[dict, CifFile]) -> dict:
    """
    Given a cif block representing a structure, get the h,k,l, and d values of the reflections
    and return them in a dictionary. or returns None if '_refln_d_spacing' doesn't exist

    :param structure: a cif dictionary or PyCIFRW
    :return: a dictionary containing hkld values, or None is '_refln_d_spacing' doesn't exist
    """
    h_local = get_from_cif(structure, '_refln_index_h')
    k_local = get_from_cif(structure, '_refln_index_k')
    l_local = get_from_cif(structure, '_refln_index_l')
    d_local = get_from_cif(structure, '_refln_d_spacing')
    id_local = get_from_cif(structure, '_pd_refln_phase_id')

    if d_local is None:
        return {}
    d_len = len(d_local)
    # h,k,l, and d must be of the same length
    if h_local is None or len(h_local) != d_len:
        h_local = ["."] * d_len
    if k_local is None or len(k_local) != d_len:
        k_local = ["."] * d_len
    if l_local is None or len(l_local) != d_len:
        l_local = ["."] * d_len
    if id_local is None or len(id_local) != d_len:
        id_local = ["."] * d_len

    return {"h": h_local, "k": k_local, "l": l_local, "d": d_local, "id": id_local}


def get_dataname_into_pattern(cif: Union[dict, CifFile], pattern: str, dataname: str, structures: List[str], others) -> None:
    """
    Search the given structures and others in the cif for a given dataname
    and copy it into the given pattern. Priority is given to the structures
    over the others. This alters the cif[pattern] in-place
    :param cif: cif dictionary or PyCIFRW
    :param pattern: string representing the datablock into which the values are to be copied
    :param dataname: the dataname being searched for
    :param structures: the structures to be searched
    :param others: the others to be searched.
    :return: None. Alters the pattern in-place
    """
    cifpat = cif[pattern]
    for structure in structures:
        cifstr = cif[structure]
        if dataname in cifstr:
            cifpat[dataname] = cifstr[dataname]
            break  # only want to get one value
    else:  # if I don't find in the linked structures, look for it in the other blocks
        for other in others:
            cifother = cif[other]
            if dataname in cifother:
                cifpat[dataname] = cifother[dataname]
                break  # only want to get one value


def get_hkld_from_matching_id(hkld_ids: dict) -> dict:
    """
    given a list of h,k,l, or d values from a place where the list contains values from multiple phases,
    return only those values corresponding to the given phase id
    :param hkld_ids: dictionary of h,k,l,d,id values
    :return: a list containing the corresponding hkld values, or None, if none match.
    """
    if not hkld_ids:
        return {}
    unique_ids = set(hkld_ids["id"])
    return {idv: {"h": [h for h, idval in zip(hkld_ids["h"], hkld_ids["id"]) if idval == idv],
                  "k": [k for k, idval in zip(hkld_ids["k"], hkld_ids["id"]) if idval == idv],
                  "l": [l for l, idval in zip(hkld_ids["l"], hkld_ids["id"]) if idval == idv],
                  "d": [d for d, idval in zip(hkld_ids["d"], hkld_ids["id"]) if idval == idv]}
            for idv in unique_ids}


def _split_val_err(ve: str, default_error: str = "zero") -> Tuple[float, Union[float, None]]:
    """
    Takes a string representing a number with an error in brackets
    such as 12.34(4), and splits off the value and error terms,
    returning a tuple of floats as (val, err)

    eg
    1.234(5) -> (1.234, 0.005)
    12(3) -> (12.0, 3.0)
    13 -> (13.0, 0.0)
    1.2(34) -> (1.2, 3.4)

    :param default_error: if there is no error present, what do you want it to be? "zero" == 0, "sqrt" == sqrt(val)
    :param ve: a string representing a number with/without an error eg '12.34(5)' or '10'
    :return: a tuple of floats (val, err)
    """
    if "(" not in ve:  # then there is no error
        if ve in {".", "?"}:
            val = float("nan")
            err = float("nan")
            return val, err
        else:
            val = float(ve)
        if default_error == "sqrt":
            err = math.sqrt(math.fabs(val))
        elif default_error == "zero":
            err = 0.0
        else:
            err = None
        return val, err

    val, err = re.search("([0-9.]+)\(([0-9]*)\)", ve).groups()
    if "." not in val:  # it makes it much easier if there is a decimal place to count
        val += "."
    pow10 = len(val) - val.find(".") - 1
    return float(val), float(err) / 10 ** pow10


def split_val_err(value: Union[str, List[str]], default_error: str = "none") -> Union[Tuple[float, float], Tuple[List[float], List[float]]]:
    """
    Takes a list of strings representing values with/without errors and gives back a tuple
    of two lists of floats. The first is the values, the second is the errors
    :param default_error: if there is no error present, what do you want it to be? "zero" == 0, "sqrt" == sqrt(val)
    :param value: string or list of strings representing floats
    :return: tuple of lists of floats containing valus and errors.
    """
    isList = True
    if isinstance(value, str):
        value = [value]
        isList = False

    vals = []
    errs = []
    for entry in value:
        v, e = _split_val_err(entry, default_error=default_error)
        vals.append(v)
        errs.append(e)

    if isList:
        return vals, errs
    else:
        return vals[0], errs[0]


def calc_cumchi2(cifpat: dict, yobs_dataname: str, ycalc_dataname: str, yobs_dataname_err: str = None, ymod_dataname: str = None):
    """
    Calculate the cumulative chi-squared statistic using the given yobs, ycalc, uncertinaty, and y_modifier.
    This is an indication of the value of chi2 taking into account only the data with the x-ordinate <= the current
    x-ordinate. It shows where there are large deviations contributing to the overall chi2
    see eqn 8 - David, W.I. 2004. "Powder Diffraction: Least-Squares and Beyond." Journal of Research of the National Institute of Standards and Technology 109 (1): 107-23.
    https://doi.org/10.6028/jres.008.

    chi^2 = (Rwp / Rexp)^2 = gof^2

    :param cifpat: dictionary representation of the cif pattern you want
    :param yobs_dataname: dataname of the yobs value
    :param ycalc_dataname: dataname of the ycalc value
    :param yobs_dataname_err: defaults to the '_pd_proc_ls_weight'. If this isn't present, it goes for the "_err" column
    :param ymod_dataname: this currently does nothing.
    :return: a numpy array with values of cumchi2. It has the same length as yobs
    """
    yobs = cifpat[yobs_dataname]
    ycalc = cifpat[ycalc_dataname]
    N = len(cifpat[yobs_dataname])

    if ymod_dataname is not None:  # I don't know what ymod means yet...
        return [-1] * len(yobs)
    if yobs_dataname_err is None and "_pd_proc_ls_weight" in cifpat:
        yweight = cifpat["_pd_proc_ls_weight"]
    else:
        yobs_dataname_err = yobs_dataname + "_err"
        yweight = 1 / (cifpat[yobs_dataname_err] ** 2)
    return np.nancumsum(yweight * ((yobs - ycalc) ** 2)) / N  # treats nan as 0


def calc_rwp(cifpat: dict, yobs_dataname: str, ycalc_dataname: str, yobs_dataname_err: str = None, ymod_dataname: str = None) -> float:
    """
    Calculate the Rwp statistic using the given yobs, ycalc, uncertinaty, and y_modifier.
    See Table 1.3 in "The Rietveld Method" by RA Young
    :param cifpat: dictionary representation of the cif pattern you want
    :param yobs_dataname: dataname of the yobs value
    :param ycalc_dataname: dataname of the ycalc value
    :param yobs_dataname_err: defaults to the '_pd_proc_ls_weight'. If this isn't present, it goes for the "_err" column
    :param ymod_dataname: this currently does nothing.
    :return: a float with value of Rwp.
    """
    yobs = cifpat[yobs_dataname]
    ycalc = cifpat[ycalc_dataname]

    if ymod_dataname is not None:  # I don't know what ymod means yet...
        return -1
    if yobs_dataname_err is None and "_pd_proc_ls_weight" in cifpat:
        yweight = cifpat["_pd_proc_ls_weight"]
    else:
        yobs_dataname_err = yobs_dataname + "_err"
        yweight = 1 / (cifpat[yobs_dataname_err] ** 2)

    top = np.nansum(yweight * ((yobs - ycalc) ** 2))
    bottom = np.nansum(yweight * (yobs ** 2))
    return np.sqrt(top / bottom)


def calc_rexp_approx(cifpat: dict, yobs_dataname: str, yobs_dataname_err: str = "", ymod_dataname: str = "") -> float:
    """
    Calculate the Rexp statistic using the given yobs, uncertinaty, and y_modifier.
    See Table 1.3 in "The Rietveld Method" by RA Young

    I am approximating N-P with N, as there should be many more datapoints than parameters.

    :param cifpat: dictionary representation of the cif pattern you want
    :param yobs_dataname: dataname of the yobs value
    :param yobs_dataname_err: defaults to the '_pd_proc_ls_weight'. If this isn't present, it goes for the "_err" column
    :param ymod_dataname: this currently does nothing.
    :return: a float with value of Rexp.
    """
    yobs = cifpat[yobs_dataname]
    N = len(cifpat[yobs_dataname])  # should strictly be N-P

    if ymod_dataname:  # I don't know what ymod means yet...
        return -1

    if not yobs_dataname_err and "_pd_proc_ls_weight" in cifpat:
        yweight = cifpat["_pd_proc_ls_weight"]
    else:
        yobs_dataname_err = yobs_dataname + "_err"
        yweight = 1 / (cifpat[yobs_dataname_err] ** 2)
    bottom = np.nansum(yweight * (yobs ** 2))
    return np.sqrt(N / bottom)


def calc_gof_approx(cifpat: dict, yobs_dataname: str, ycalc_dataname: str, yobs_dataname_err: str = None, ymod_dataname: str = None):
    """
    Calculate the goodness-of-fit statistic using the given yobs, ycalc, uncertinaty, and y_modifier.
    See Table 1.3 in "The Rietveld Method" by RA Young

    Should be using N-P, but there should be many more datapoints than parameters, so it should be pretty good.

    :param cifpat: dictionary representation of the cif pattern you want
    :param yobs_dataname: dataname of the yobs value
    :param ycalc_dataname: dataname of the ycalc value
    :param yobs_dataname_err: defaults to the '_pd_proc_ls_weight'. If this isn't present, it goes for the "_err" column
    :param ymod_dataname: this currently does nothing.
    :return: a float with values of gof.
    """
    rwp = calc_rwp(cifpat, yobs_dataname, ycalc_dataname, yobs_dataname_err, ymod_dataname)
    rexp = calc_rexp_approx(cifpat, yobs_dataname, yobs_dataname_err, ymod_dataname)
    return rwp / rexp


def theta2_from_min_max_inc(start: float, step: float, stop: float) -> List[str]:
    num_points = int(round((stop - start) / step, 5)) + 1
    return [str(v) for v in np.linspace(start, stop, num_points)]


def theta2_min_max_inc_expand(cifpat: CifBlock, val: str = "meas") -> None:
    MEAS_COL = ["_pd_meas_counts_total", "_pd_meas_intensity_total"]
    PROC_COL = ["_pd_proc_intensity_total", "_pd_proc_intensity_net"]
    MEAS_VALS = ["_pd_meas_2theta_range_min", "_pd_meas_2theta_scan", "_pd_meas_2theta_range_min", "_pd_meas_2theta_range_inc", "_pd_meas_2theta_range_max"]
    PROC_VALS = ["_pd_proc_2theta_range_min", "_pd_proc_2theta_corrected", "_pd_proc_2theta_range_min", "_pd_proc_2theta_range_inc", "_pd_proc_2theta_range_max"]

    if val == "meas":
        mincheck, x_ordinate, minval, incval, maxval = MEAS_VALS
        test_cols = MEAS_COL + PROC_COL
    else:  # if val == "proc":
        mincheck, x_ordinate, minval, incval, maxval = PROC_VALS
        test_cols = PROC_COL + MEAS_COL

    if mincheck in cifpat and x_ordinate not in cifpat:
        th2_scan = theta2_from_min_max_inc(float(cifpat[minval]),
                                           float(cifpat[incval]),
                                           float(cifpat[maxval]))
        # chooses the best place to put it. The list I'm checking against
        #  is in order of preference
        for y in test_cols:
            if y not in cifpat:
                continue
            cifpat.AddToLoop(y, {x_ordinate: th2_scan})
            break  # only do it to the first that matches
    cifpat.RemoveItem(minval)
    cifpat.RemoveItem(incval)
    cifpat.RemoveItem(maxval)


def get_linked_structures_and_phase_ids(cifpat: CifFile, blockname_dict: dict) -> Tuple[List[str], List[str]]:
    pd_phase_ids = []
    structures = []
    if "_pd_phase_block_id" in cifpat:  # then it is linked to other structures
        phase_block_ids = cifpat["_pd_phase_block_id"] if not isinstance(cifpat["_pd_phase_block_id"], str) else [cifpat["_pd_phase_block_id"]]
        structures = [get_blockname_from_block_id(blockname_dict, phase_id) for phase_id in phase_block_ids]
        if "_pd_phase_id" not in cifpat:
            pd_phase_ids = [str(i) for i in list(range(1, len(structures) + 1))]  # keep it as a string, just like pycifrw does
            cifpat["_pd_phase_id"] = pd_phase_ids
        else:
            pd_phase_ids = cifpat["_pd_phase_id"]
    return structures, pd_phase_ids


def calc_dq_from_qd(dq):
    return 2. * np.pi / dq


def calc_d_from_2theta(lam: float, th2):
    return lam / (2. * np.sin(th2 * np.pi / 360.))


def calc_q_from_2theta(lam: float, th2):
    return 4. * np.pi * np.sin(th2 * np.pi / 360.) / lam


def calc_2theta_from_d(lam: float, d):
    return 2. * np.arcsin(lam / (2. * d)) * 180. / np.pi


def add_hklds_to_cifpatstr(cifpatstr: dict, hkld_dict: dict) -> None:
    """
    adds hkld information to a phase in the "str" section of a cif dictionary
    :param cifpatstr:  a dictionary of the form: cifpat["str"][phase_id]
    :param hkld_dict: an hkl dictionary of the form hkld_dict or hklds[phase_id]
    :return: None - changes in-place
    """
    for refln, idx in zip(['_refln_index_h', '_refln_index_k', '_refln_index_l', '_refln_d_spacing'], ["h", "k", "l", "d"]):
        cifpatstr[refln] = hkld_dict[idx]


def calc_dataname_and_err(cifpat: dict, dataname: str, default_error: str = "zero") -> None:
    """
    gets a single value-as-string or list of values-as-strings and correctly turns them in to a float or lists of floats
    with an error term, if applicable
    :param cifpat: the pattern from which you are getting the data
    :param dataname: the name of the dataitem you want to obtain
    :param default_error: how to treat the presence (or otherwiase) of errors. "sqrt" - if no error, use the sqrt. "zero" - if no error, return 0.0. "none" - if no error, then don't do anything about it.
    :return:
    """
    val, err = split_val_err(cifpat[dataname], default_error=default_error)

    do_errors = True
    if isinstance(err, list):
        if all(e is None for e in err):
            do_errors = False
    elif err is None:
        do_errors = False

    cifpat[dataname] = np.asarray(val, dtype=float)
    if default_error in {"sqrt", "zero"} or do_errors:
        cifpat[dataname + "_err"] = np.asarray(err, dtype=float)


class ParseCIF:
    # these are all the values that could be an x-ordinate. I added the last two to be place-holders
    # for d and/or q calculated from Th2, q, or d, where it is possible from the data in the pattern.
    COMPLETE_X_LIST = ["_pd_meas_2theta_scan", "_pd_proc_2theta_corrected", "_pd_meas_time_of_flight",
                       "_pd_meas_position", "_pd_proc_energy_incident",
                       "_pd_proc_d_spacing", "_pd_proc_recip_len_Q",
                       "_pd_meas_2theta_range_inc", "_pd_proc_2theta_range_inc",  # these are here to capture blocks with start step stop values
                       "d", "q"]  # "_pd_proc_wavelength",

    # These are datanames that fit corresspond to the data you are modelling
    # these are also the only ones that could have an error
    OBSERVED_Y_LIST = ["_pd_meas_counts_total", "_pd_meas_intensity_total",
                       "_pd_proc_intensity_total", "_pd_proc_intensity_net"]

    # These are all the different kinds of background data you could have.
    BACKGROUND_Y_LIST = ["_pd_meas_counts_background", "_pd_meas_counts_container",
                         "_pd_meas_intensity_background", "_pd_meas_intensity_container",
                         "_pd_proc_intensity_bkg_calc", "_pd_proc_intensity_bkg_fix"]

    # These are the things that could modify the intensities
    MODIFIER_Y_LIST = ["_pd_meas_step_count_time", "_pd_meas_counts_monitor",
                       "_pd_meas_intensity_monitor", "_pd_proc_intensity_norm",
                       "_pd_proc_intensity_incident", "_pd_proc_ls_weight"]

    # These are the intensities calculated in the modelling
    CALCULATED_Y_LIST = ["_pd_calc_intensity_total", "_pd_calc_intensity_net"]

    COMPLETE_Y_LIST = OBSERVED_Y_LIST + BACKGROUND_Y_LIST + CALCULATED_Y_LIST

    NICE_TO_HAVE_DATANAMES = ["_diffrn_radiation_wavelength", "_cell_measurement_wavelength",
                              "_diffrn_ambient_temperature", "_cell_measurement_temperature",
                              "_diffrn_ambient_pressure", "_cell_measurement_pressure",
                              "_refine_ls_goodness_of_fit_all", "_pd_proc_ls_prof_wr_factor",
                              "_pd_proc_ls_prof_wr_expected", "_pd_meas_datetime_initiated"]

    DATANAMES_THAT_SHOULD_BE_NUMERIC = ["_pd_phase_mass_%", "_refln_d_spacing"] + \
                                       COMPLETE_X_LIST + COMPLETE_Y_LIST + MODIFIER_Y_LIST + \
                                       NICE_TO_HAVE_DATANAMES[:-1]

    def __init__(self, ciffilename, scantype="flex", grammar="1.1", scoping="dictionary", permissive=False):
        print(f"Now reading {ciffilename}. This may take a while.")
        self.ciffile: CifFile = ReadCif(ciffilename, scantype=scantype, grammar=grammar, scoping=scoping, permissive=permissive)
        self.ncif: dict = {}  # this will be the cif file with pattern information only
        self.cif: dict = {}


        if self.ciffile is None:
            raise ValueError("CIF file is empty.")

        self._remove_empty_items()
        self._make_up_block_id()
        self._expand_2theta_min_max_inc()
        self._expand_multiple_dataloops()
        self._get_hkl_ticks()
        self._get_nice_to_have_information()
        self._make_just_patterns_cif()
        self._make_cif_numeric()
        self._calc_extra_data()
        self._put_phase_mass_pct_in_strs()
        self._rename_datablock_from_blockid()

    def _remove_empty_items(self) -> None:
        """
        Checks every item in each block and if all the values are '?' or '.', it removes them from the cif
        :return: none. alters in place
        """
        for block in self.ciffile.block_input_order:
            cifblk = self.ciffile[block]
            dataitems = copy.deepcopy(cifblk.keys())
            for item in dataitems:
                value = cifblk[item]
                if isinstance(value, list):
                    for v in value:
                        v = v.strip()  # need to strip whitespace, as sometimes it hangs around
                        if v not in [".", "?"]:
                            break  # if any of the entries isn't blank, then I want to keep the whole item
                    else:  # we only get there if all of the values inthe list are . or ?
                        cifblk.RemoveItem(item)
                elif isinstance(value, str):
                    value = value.strip()
                    if value in [".", "?"]:
                        cifblk.RemoveItem(item)
                else:
                    print("How did we even get here?")

    def _make_up_block_id(self) -> None:
        """
        Some people confuse the _pd_block_id and the data_ blockname.
        This goes and adds a _pd_block_id to every block that doesn't have an id such that _pd_block_id == blockname
        :return: none. alters in place
        """
        for block in self.ciffile.block_input_order:
            cifblk = self.ciffile[block]
            cifblk["_pd_block_id"] = block if "_pd_block_id" not in cifblk else cifblk["_pd_block_id"]

    def _expand_2theta_min_max_inc(self) -> None:
        """
        Expand _pd_meas_2theta_range_min/max/inc into explicit values of _pd_meas_2theta_scan, and
        _pd_proc_2theta_range_min/max/inc into _pd_proc_2theta_corrected. The min/max/inc dataitems are
        then deleted from the CIF.
        :return: None. do it in-place
        """
        patterns = grouped_blocknames(self.ciffile)["patterns"]
        for pattern in patterns:
            cifpat = self.ciffile[pattern]
            theta2_min_max_inc_expand(cifpat, "meas")
            theta2_min_max_inc_expand(cifpat, "proc")

    def _expand_multiple_dataloops(self) -> None:
        """
        This looks for patterns which have multiple loops containing diffraction data
        This clones the block as many times as there are loops, with each clone containing
        only one diffraction data loop. All other information is the same
        :return: nothing. alters ciffile in place
        """
        patterns = grouped_blocknames(self.ciffile)["patterns"]

        for pattern in patterns:
            cifpat = self.ciffile[pattern]
            # get all loops in this data block
            loops = copy.deepcopy(cifpat.loops)  # this needs to be a deepcopy or it updates itself on RemoveItem !
            keys_of_loops = []
            for key in loops.keys():
                looped_datanames = loops[key]
                if any(x in looped_datanames for x in ParseCIF.COMPLETE_X_LIST):
                    keys_of_loops.append(key)
            if len(keys_of_loops) == 1:
                continue  # because there is only one data loop in this pattern
            # we only get to here if there are many data loops in the cif. We need to unroll them

            # deepcopy the pattern so I can clone it
            dcopy = copy.deepcopy(self.ciffile[pattern])
            # rename the current pattern and remove the required dataloops.
            for i, key in enumerate(keys_of_loops):
                if i == 0:
                    continue  # don't delete the first one
                remove_these = loops[key]
                for dataname in remove_these:
                    cifpat.RemoveItem(dataname)
            # update the block_id so you know it's been unrolled
            cifpat["_pd_block_id"] = "L0_|" + get_from_cif(cifpat, "_pd_block_id", pattern)

            # repeat the previous step as needed to copy in all the dataloops
            for i in range(1, len(keys_of_loops)):
                insert_me = copy.deepcopy(dcopy)
                for j, key in enumerate(keys_of_loops):
                    if j == i:
                        continue  # ie don't delete the dataloop that this one is supposed to keep
                    remove_these = loops[key]
                    for dataname in remove_these:
                        insert_me.RemoveItem(dataname)
                new_block_prefix = f"L{i}_|"
                new_pattern_name = new_block_prefix + pattern
                self.ciffile.NewBlock(new_pattern_name, insert_me)
                self.ciffile[new_pattern_name]["_pd_block_id"] = new_block_prefix + get_from_cif(self.ciffile[new_pattern_name], "_pd_block_id", new_pattern_name)

    def _get_hkl_ticks(self) -> None:
        """
        Go through a pattern and look for linked structures. Get hkld information from either the linked structures
        or from the in reflection listing in the pattern block if there is a _pd_refln_phase_id data name
        :return:
        """
        blocknames = grouped_blocknames(self.ciffile)
        patterns = blocknames["patterns"]
        blockname_of = blockname_lookupdict_from_blockid(self.ciffile)
        self.cif = convert_cif_to_dict(self.ciffile)

        # update each pattern's information
        for pattern in patterns:
            cifpat = self.cif[pattern]
            if "_pd_phase_block_id" in cifpat:  # then it is linked to other structures
                structures, pd_phase_ids = get_linked_structures_and_phase_ids(cifpat, blockname_of)
                # now we know there are linked structures, and a phase id block, I can
                # make places to put pertinant information in the cif
                if "str" not in cifpat:
                    cifpat["str"] = {}
                for pd_phase_id in pd_phase_ids:
                    cifpat["str"][pd_phase_id] = {}
                # look for phase names
                for phase_id, structure in zip(pd_phase_ids, structures):
                    cifstr = self.cif[structure]
                    phase_name = cifstr["_pd_phase_name"] if "_pd_phase_name" in cifstr else phase_id
                    cifpat["str"][phase_id]["_pd_phase_name"] = phase_name
                # look for hkld values
                if '_refln_d_spacing' not in cifpat:  # then it is OK to look for them in other places
                    for phase_id, structure in zip(pd_phase_ids, structures):
                        cifstr = self.cif[structure]
                        hkld_dict = get_hkld_ids(cifstr)
                        if not hkld_dict:
                            continue
                        add_hklds_to_cifpatstr(cifpat["str"][phase_id], hkld_dict)
                elif "_pd_refln_phase_id" in cifpat:
                    # these contain all the hkls from all the phases
                    hklds = get_hkld_from_matching_id(get_hkld_ids(cifpat))
                    for phase_id in pd_phase_ids:
                        try:
                            add_hklds_to_cifpatstr(cifpat["str"][phase_id], hklds[phase_id])
                        except KeyError as e:
                            print(e)
                            print(f"No hkls found for phase {phase_id}.")
            elif "_refln_d_spacing" in cifpat:  # there is no phase_block_id and so only a single phase's worth of tick marks
                hkld_dict = get_hkld_ids(cifpat)
                if not hkld_dict:
                    continue
                cifpat["str"] = {"1": {}}
                add_hklds_to_cifpatstr(cifpat["str"]["1"], hkld_dict)
                cifpat["str"]["1"]["_pd_phase_name"] = get_from_cif(cifpat, "_pd_phase_name", default="1")

    def _get_nice_to_have_information(self) -> None:
        """
        This traverses the linked structures, and then the "other" blocks, to look for information that is nice to have with
        the pattern
        :return:
        """
        blocknames = grouped_blocknames(self.cif)
        blockname_of = blockname_lookupdict_from_blockid(self.cif)
        patterns = blocknames["patterns"]
        others = blocknames["others"]

        for pattern in patterns:
            cifpat = self.cif[pattern]
            structures, _ = get_linked_structures_and_phase_ids(cifpat, blockname_of)
            # look for other datanames that it would be nice to have in the pattern
            for dataname in ParseCIF.NICE_TO_HAVE_DATANAMES:
                if dataname not in cifpat or cifpat[dataname] in [".", "?"]:  # then need to look for it in different places
                    get_dataname_into_pattern(self.cif, pattern, dataname, structures, others)

    def _make_just_patterns_cif(self) -> None:
        """
        Goes through all of the blocks in the cif dictionary and only copies out the onces which contain diffraction patterns.
        All the other necessary information should already be in the "str" entry.
        :return:
        """
        blocknames = grouped_blocknames(self.cif)
        patterns = blocknames["patterns"]
        for pattern in patterns:
            self.ncif[pattern] = self.cif[pattern]

    def _make_cif_numeric(self):
        for pattern in self.ncif:
            cifpat = self.ncif[pattern]
            for dataname in ParseCIF.DATANAMES_THAT_SHOULD_BE_NUMERIC:
                if dataname not in cifpat:
                    continue
                if dataname in self.OBSERVED_Y_LIST:
                    calc_dataname_and_err(cifpat, dataname, default_error="sqrt")
                elif dataname in ("_pd_phase_mass_%"):
                    calc_dataname_and_err(cifpat, dataname, default_error="zero")  # for single phase, so there is no error on the wt%
                else:
                    calc_dataname_and_err(cifpat, dataname, default_error="none")

    def _calc_extra_data(self) -> None:
        for pattern in self.ncif:
            cifpat = self.ncif[pattern]
            if "_pd_proc_d_spacing" not in cifpat and "_pd_proc_recip_len_Q" in cifpat:
                cifpat["d"] = calc_dq_from_qd(cifpat["_pd_proc_recip_len_Q"])
            if "_pd_proc_recip_len_Q" not in cifpat and "_pd_proc_d_spacing" in cifpat:
                cifpat["q"] = calc_dq_from_qd(cifpat["_pd_proc_d_spacing"])

            lam = None
            if '_diffrn_radiation_wavelength' in cifpat or "_cell_measurement_wavelength" in cifpat:
                lam = cifpat["_diffrn_radiation_wavelength"] if '_diffrn_radiation_wavelength' in cifpat else cifpat["_cell_measurement_wavelength"]
                cifpat["wavelength"] = lam
                if "_pd_proc_d_spacing" not in cifpat and "d" not in cifpat:
                    for th2 in ["_pd_proc_2theta_corrected", "_pd_meas_2theta_scan"]:
                        if th2 in cifpat:
                            cifpat["d"] = calc_d_from_2theta(lam, cifpat[th2])
                            break  # only want to do a single d-from-2th calculation
                if "_pd_proc_recip_len_Q" not in cifpat and "q" not in cifpat:
                    for th2 in ["_pd_proc_2theta_corrected", "_pd_meas_2theta_scan"]:
                        if th2 in cifpat:
                            cifpat["q"] = calc_q_from_2theta(lam, cifpat[th2])
                            break  # only want to do a single q-from-2th calculation

            if "str" in cifpat:
                for phase in cifpat["str"]:
                    if "_refln_d_spacing" in cifpat["str"][phase]:
                        cifstr = cifpat["str"][phase]
                        cifstr["_refln_d_spacing"] = np.asarray(cifstr["_refln_d_spacing"], dtype=float)
                        cifstr["refln_q"] = calc_dq_from_qd(cifstr["_refln_d_spacing"])
                        if lam:
                            cifstr["refln_2theta"] = calc_2theta_from_d(lam, cifstr["_refln_d_spacing"])
                        cifstr["refln_hovertext"] = [f"{h} {k} {l}" for h, k, l in
                                                     zip(cifstr['_refln_index_h'], cifstr['_refln_index_k'], cifstr["_refln_index_l"])]

    def _put_phase_mass_pct_in_strs(self) -> None:
        for pattern in self.ncif:
            cifpat = self.ncif[pattern]
            if "_pd_phase_mass_%" not in cifpat or "str" not in cifpat:
                continue
            phase_ids = cifpat["_pd_phase_id"]
            qpas = cifpat["_pd_phase_mass_%"]
            qpa_errs = cifpat["_pd_phase_mass_%_err"]
            for phase, qpa, err in zip(phase_ids, qpas, qpa_errs):
                cifpat["str"][phase]["_pd_phase_mass_%"] = qpa
                cifpat["str"][phase]["_pd_phase_mass_%_err"] = err

    def _rename_datablock_from_blockid(self) -> None:
        """
        A lot of the pdCIF revolves around block_id, and not the dataname.
        This renames the dataname as the block_id to enable easier lookups.
        This needs to be done as a dictionary, and not a PyCifRW, as PyCIFRW
        forces datablock names to be lowercase.
        :return:
        """
        for pattern in self.ncif:
            cifpat = self.ncif[pattern]
            if "_pd_block_id" not in cifpat:
                cifpat["_pd_block_id"] = pattern
        self.ncif = {self.ncif[k]["_pd_block_id"]: v for k, v in self.ncif.items()}

    def get_processed_cif(self):
        return self.ncif


# end of class


if __name__ == "__main__":
    filename = r"c:\data\La2Ti2O7-n-883C-mono.cif"
    cf = ParseCIF(filename)
    cifd = cf.get_processed_cif()
    print("This is the end of the file:")
    pretty(cifd, print_values=True)

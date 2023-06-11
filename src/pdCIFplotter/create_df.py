from CifFile import CifFile, ReadCif, StarFile, CifBlock
import pandas as pd
import numpy as np
import re
import math
import copy
# from timeit import default_timer as timer   # use as start = timer() ...  end = timer()
from typing import List, Tuple, Union, Any, Dict


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


def convert_cif_to_dict(cif: CifFile) -> Dict:
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


def blockname_lookupdict_from_blockid(cif: Union[Dict, CifFile]) -> Dict:
    """
    To get information from a CIF, you need to know the name of the block (data_'blocknamegoeshere'), but when linking
    between blocks, a block id is used. This function creates a dictionary, which, when given a blockid, returns a
    block name. This means you can get the block corresponding to a blockid
    :param cif:
    :return: dictionary with blockids as keys and blocknames as values.
    """
    keys = cif.keys() if isinstance(cif, dict) else cif.block_input_order
    return {cif[blockname]["_pd_block_id"]: blockname for blockname in keys if "_pd_block_id" in cif[blockname]}


def grouped_blocknames(cif: Union[CifFile, Dict]) -> Dict:
    """
    Looks at all the datablocks in a cif and categorises them into those that have diffraction pattern information,
    those with crystal structure information, and the others.
    :param cif: a PyCIFRW readcif object or normal dictionary
    :return: a dictionary containing lists of datablock names corresponding to "patterns", "structures", and "others". They are order according to appearance in the file
    """
    pattern_datanames = []
    structure_datanames = []
    other_datanames = []

    keys = cif.keys() if isinstance(cif, dict) else cif.block_input_order

    for datablock in keys:
        if any(x in cif[datablock] for x in COMPLETE_X_LIST):
            pattern_datanames.append(datablock)  # this can include datablocks that have both pattern and structure info
        elif "_cell_length_a" in cif[datablock]:
            structure_datanames.append(datablock)  # This only has structures that have no pattern information
        else:
            other_datanames.append(datablock)
    return {"patterns": pattern_datanames, "structures": structure_datanames, "others": other_datanames}


def get_blockname_from_block_id(lookup_dict: Dict, block_id: str) -> str:
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


def get_linked_structures_and_phase_ids(cifpat: CifFile, blockname_dict: Dict) -> Tuple[List[str], List[str]]:
    if "_pd_phase_block_id" not in cifpat:  # then it is not linked to other structures
        return [], []

    phase_block_ids = cifpat["_pd_phase_block_id"] if isinstance(cifpat["_pd_phase_block_id"], list) else [cifpat["_pd_phase_block_id"]]
    structures = [get_blockname_from_block_id(blockname_dict, phase_id) for phase_id in phase_block_ids]

    if "_pd_phase_id" in cifpat:
        pd_phase_ids = cifpat["_pd_phase_id"]
    else:
        pd_phase_ids = [str(i) for i in list(range(1, len(structures) + 1))]  # keep it as a string, just like pycifrw does
        cifpat["_pd_phase_id"] = pd_phase_ids

    return structures, pd_phase_ids


def get_dataname_into_pattern(cif: Union[Dict, CifFile], pattern: str, dataname: str, structures: List[str], others) -> None:
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


def remove_empty_items(cif: CifFile) -> None:
    """
    Checks every item in each block and if all the values are '?' or '.', it removes them from the cif
    :return: none. alters in place
    """
    for block in cif.block_input_order:
        cifblk = cif[block]
        dataitems = copy.deepcopy(cifblk.keys())
        for item in dataitems:
            value = cifblk[item]
            if isinstance(value, list):
                for v in value:
                    if v.strip() not in [".", "?"]:
                        break  # if any of the entries isn't blank, then I want to keep the whole item
                else:  # we only get there if all of the values inthe list are . or ?
                    cifblk.RemoveItem(item)
            elif isinstance(value, str):
                if value.strip() in [".", "?"]:
                    cifblk.RemoveItem(item)
            else:
                print("How did we even get here?")


def make_up_block_id(cif: CifFile) -> None:
    """
    Some people confuse the _pd_block_id and the data_ blockname.
    This goes and adds a _pd_block_id to every block that doesn't have an id such that _pd_block_id == blockname
    :return: none. alters in place
    """
    for block in cif.block_input_order:
        cifblk = cif[block]
        cifblk["_pd_block_id"] = block if "_pd_block_id" not in cifblk else cifblk["_pd_block_id"]


def expand_2theta_min_max_inc(cif: CifFile) -> None:
    """
    Expand _pd_meas_2theta_range_min/max/inc into explicit values of _pd_meas_2theta_scan, and
    _pd_proc_2theta_range_min/max/inc into _pd_proc_2theta_corrected. The min/max/inc dataitems are
    then deleted from the CIF.
    :return: None. do it in-place
    """
    patterns = grouped_blocknames(cif)["patterns"]
    for pattern in patterns:
        cifpat = cif[pattern]
        theta2_min_max_inc_expand(cifpat, "meas")
        theta2_min_max_inc_expand(cifpat, "proc")


def theta2_min_max_inc_expand(cifpat: CifBlock, val: str = "meas") -> None:
    MEAS_COL = ["_pd_meas_counts_total", "_pd_meas_intensity_total"]
    PROC_COL = ["_pd_proc_intensity_total", "_pd_proc_intensity_net"]
    MEAS_VALS = ["_pd_meas_2theta_range_min", "_pd_meas_2theta_scan", "_pd_meas_2theta_range_min", "_pd_meas_2theta_range_inc", "_pd_meas_2theta_range_max"]
    PROC_VALS = ["_pd_proc_2theta_range_min", "_pd_proc_2theta_corrected", "_pd_proc_2theta_range_min", "_pd_proc_2theta_range_inc", "_pd_proc_2theta_range_max"]

    test_cols = MEAS_COL + PROC_COL
    if val == "meas":
        mincheck, x_ordinate, minval, incval, maxval = MEAS_VALS
    else:  # if val == "proc":
        mincheck, x_ordinate, minval, incval, maxval = PROC_VALS

    if mincheck in cifpat and x_ordinate not in cifpat:
        th2_scan = theta2_from_min_max_inc(float(cifpat[minval]),
                                           float(cifpat[incval]),
                                           float(cifpat[maxval]))
        # chooses the best place to put it. The list I'm checking against is in order of preference
        for y in test_cols:
            if y not in cifpat:
                continue
            cifpat.AddToLoop(y, {x_ordinate: th2_scan})
            break  # only do it to the first that matches
    cifpat.RemoveItem(minval)
    cifpat.RemoveItem(incval)
    cifpat.RemoveItem(maxval)


def theta2_from_min_max_inc(start: float, step: float, stop: float) -> List[str]:
    num_points = int(round((stop - start) / step, 5)) + 1
    return [str(v) for v in np.linspace(start, stop, num_points)]


def expand_multiple_dataloops(cif: CifFile) -> None:
    """
    This looks for patterns which have multiple loops containing diffraction data
    This clones the block as many times as there are loops, with each clone containing
    only one diffraction data loop. All other information is the same
    :return: nothing. alters ciffile in place
    """
    patterns = grouped_blocknames(cif)["patterns"]

    for pattern in patterns:
        cifpat = cif[pattern]
        # get all loops in this data block
        loops = copy.deepcopy(cifpat.loops)  # this needs to be a deepcopy or it updates itself on RemoveItem !
        keys_of_loops = []
        for key in loops.keys():
            looped_datanames = loops[key]
            if any(x in looped_datanames for x in COMPLETE_X_LIST):
                keys_of_loops.append(key)
        if len(keys_of_loops) == 1:
            continue  # because there is only one data loop in this pattern
        # we only get to here if there are many data loops in the cif. We need to unroll them

        # deepcopy the pattern so I can clone it
        dcopy = copy.deepcopy(cif[pattern])
        # rename the current pattern and remove the required dataloops.
        for i, key in enumerate(keys_of_loops):
            if i == 0:
                continue  # don't delete the first one
            remove_these = loops[key]
            for dataname in remove_these:
                cifpat.RemoveItem(dataname)
        # update the block_id so you know it's been unrolled
        cifpat["_pd_block_id"] = f'L0_|{cifpat.get("_pd_block_id", pattern)}'

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
            cif.NewBlock(new_pattern_name, insert_me)
            cif[new_pattern_name]["_pd_block_id"] = new_block_prefix + cif[new_pattern_name].get("_pd_block_id", new_pattern_name)


def get_hkl_ticks(cif: Dict) -> None:
    """
    Go through a pattern and look for linked structures. Get hkld information from either the linked structures
    or from the in reflection listing in the pattern block if there is a _pd_refln_phase_id data name
    :return:
    """
    blocknames = grouped_blocknames(cif)
    patterns = blocknames["patterns"]
    blockname_of = blockname_lookupdict_from_blockid(cif)

    # update each pattern's information
    for pattern in patterns:
        cifpat = cif[pattern]
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
                cifstr = cif[structure]
                phase = cifpat["str"][phase_id]
                phase["_pd_phase_name"] = cifstr.get("_pd_phase_name", phase_id)
                phase["_pd_block_id"] = cifstr.get("_pd_block_id", structure)
            # look for hkld values
            if '_refln_d_spacing' not in cifpat:  # then it is OK to look for them in other places
                for phase_id, structure in zip(pd_phase_ids, structures):
                    cifstr = cif[structure]
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
            cifpat["str"]["1"]["_pd_phase_name"] = cifpat.get("_pd_phase_name", "1")
            cifpat["str"]["1"]["_pd_block_id"] = cifpat.get("_pd_block_id", pattern)


def get_hkld_ids(structure: Union[Dict, CifFile]) -> Dict:
    """
    Given a cif block representing a structure, get the h,k,l, and d values of the reflections
    and return them in a dictionary. or returns None if '_refln_d_spacing' doesn't exist

    :param structure: a cif dictionary or PyCIFRW
    :return: a dictionary containing hkld values, or None is '_refln_d_spacing' doesn't exist
    """
    h_local = structure.get('_refln_index_h')
    k_local = structure.get('_refln_index_k')
    l_local = structure.get('_refln_index_l')
    d_local = structure.get('_refln_d_spacing')
    id_local = structure.get('_pd_refln_phase_id')

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


def get_hkld_from_matching_id(hkld_ids: Dict) -> Dict:
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


def add_hklds_to_cifpatstr(cifpatstr: Dict, hkld_dict: Dict) -> None:
    """
    adds hkld information to a phase in the "str" section of a cif dictionary
    :param cifpatstr:  a dictionary of the form: cifpat["str"][phase_id]
    :param hkld_dict: an hkl dictionary of the form hkld_dict or hklds[phase_id]
    :return: None - changes in-place
    """
    for refln, idx in zip(['_refln_index_h', '_refln_index_k', '_refln_index_l', '_refln_d_spacing'], ["h", "k", "l", "d"]):
        cifpatstr[refln] = hkld_dict[idx]


def get_nice_to_have_information(cif: Dict) -> None:
    """
    This traverses the linked structures, and then the "other" blocks, to look for information that is nice to have with
    the pattern
    :return:
    """
    blocknames = grouped_blocknames(cif)
    blockname_of = blockname_lookupdict_from_blockid(cif)
    patterns = blocknames["patterns"]
    others = blocknames["others"]

    for pattern in patterns:
        cifpat = cif[pattern]
        structures, _ = get_linked_structures_and_phase_ids(cifpat, blockname_of)
        # look for other datanames that it would be nice to have in the pattern
        for dataname in NICE_TO_HAVE_DATANAMES:
            if dataname not in cifpat or cifpat[dataname] in [".", "?"]:  # then need to look for it in different places
                get_dataname_into_pattern(cif, pattern, dataname, structures, others)






class UberCIFdict:
    def __init__(self):
        self.patterns = None
        self.structures = None
        self.others = None



def process_cif(cif: CifFile):
    # done on pycifrw cif
    remove_empty_items(cif)
    make_up_block_id(cif)
    expand_2theta_min_max_inc(cif)
    expand_multiple_dataloops(cif)

    # done on a normal dict
    cifd = convert_cif_to_dict(cif)

    get_hkl_ticks(cifd)
    get_nice_to_have_information(cifd)
    make_just_patterns_cif(cifd)
    make_cif_numeric(cifd)
    calc_extra_data(cifd)
    put_phase_mass_pct_in_strs(cifd)
    rename_datablock_from_blockid(cifd)
    replace_dots_in_names(cifd)


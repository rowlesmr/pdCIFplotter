import numpy as np
import re
import math
import copy
# from timeit import default_timer as timer   # use as start = timer() ...  end = timer()
import CifFile


def pretty(d, indent=0, print_values=True):
    for key, value in d.items():
        print('|  ' * indent + "|--" + str(key))
        if isinstance(value, dict):
            pretty(value, indent + 1, print_values=print_values)
        else:
            if print_values:
                print('|  ' * (indent + 1) + "|--" + str(value))


def convert_cif_to_dict(cif):
    """
    Converts a PyCIFRW CifFile into a normal Python dictionary
    :param cif:
    :return: cif as a dictionary
    """
    key_list = cif.block_input_order
    cif_dict = cif.__dict__["dictionary"]
    for key in key_list:  # Python >=3.7 keeps dictionary keys in insertion order: https://mail.python.org/pipermail/python-dev/2017-December/151283.html
        cif_dict[key] = cif[key].__dict__["block"]
        for sub_key in cif_dict[key].keys():
            cif_dict[key][sub_key] = cif_dict[key][sub_key][0]
    return cif_dict


def blockname_lookupdict_from_blockid(cif):
    """
    To get information from a CIF, you need to know the name of the block (data_'blocknamegoeshere'), but when linking
    between blocks, a block id is used. This function creates a dictionary, which, when given a blockid, returns a
    block name. This means you can get the block corresponding to a blockid
    :param cif:
    :return: dictionary with blockids as keys and blocknames as values.
    """
    # lookup_dict = {}
    # for blockname in cif.block_input_order:
    #     if "_pd_block_id" in cif[blockname]:
    #         lookup_dict[cif[blockname]["_pd_block_id"]] = blockname
    # return lookup_dict
    return {cif[blockname]["_pd_block_id"]: blockname for blockname in cif.block_input_order if "_pd_block_id" in cif[blockname]}


def grouped_blocknames(cif):
    """
    Looks at all the datablocks in a cif and categorieses them into those that have diffraction pattern information,
    those with crystal structure information, and the others.
    :param cif: a PyCIFRW readcif object
    :return: a dictionary containing lists of datablock names corresponding to "patterns", "structures", and "others". They are order according to appearance in the file
    """
    pattern_datanames = []
    structure_datanames = []
    other_datanames = []

    for datablock in cif.block_input_order:
        if any(x in cif[datablock] for x in ParseCIF.COMPLETE_X_LIST):
            pattern_datanames.append(datablock)  # this can include datablocks that have both pattern and structure info
        elif "_cell_length_a" in cif[datablock]:
            structure_datanames.append(datablock)  # This only has structures that have no pattern information
        else:
            other_datanames.append(datablock)
    return {"patterns": pattern_datanames, "structures": structure_datanames, "others": other_datanames}


def get_from_cif(cif, itemname):
    """
    Given a cif and a itemname, return the value associated with that blockname if it exists.
    If not, return None.
    :param cif: cif as dictionary or PyCIFRW
    :param itemname: string representing blockname
    :return: whatever is in the blockname, or None if it doesn't exist.
    """
    if itemname in cif:
        return cif[itemname]
    else:
        return None


def get_hklds(structure):
    """
    Given a cif block representing aa structure, get the h,k,l, and d values of the reflections
    and return them in a dictionary. or returns None if '_refln_d_spacing' doesn't exist

    :param structure: a cif dictionary or PyCIFRW
    :return: a dictionary containing hkld values, or None is '_refln_d_spacing' doesn't exist
    """
    h_local = get_from_cif(structure, '_refln_index_h')
    k_local = get_from_cif(structure, '_refln_index_k')
    l_local = get_from_cif(structure, '_refln_index_l')
    d_local = get_from_cif(structure, '_refln_d_spacing')

    if d_local is None:
        return None
    d_len = len(d_local)
    # h,k,l, and d must be of the same length
    if h_local is None or len(h_local) != d_len:
        h_local = ["."] * d_len
    if k_local is None or len(k_local) != d_len:
        k_local = ["."] * d_len
    if l_local is None or len(l_local) != d_len:
        l_local = ["."] * d_len

    return {"h": h_local, "k": k_local, "l": l_local, "d": d_local}


def get_dataname_into_pattern(cif, pattern, dataname, structures, others):
    """
    Search the given structures and others in the cif for a given dataname
    and copy it into the given pattern. Priority is given to the structures
    over the others. This alters the cif[pattern] in-place
    :param cif: cif dictionary of PyCIFRW
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


def get_hkld_from_matching_id(hklds, phase_id, phase_ids):
    """
    given a list of h,k,l, or d values from a place where the list contains values from multiple phases,
    return only those values corresponding to the given phase id
    :param hklds: a list containing h,k,l, or d values from multiple phases
    :param phase_id: the _pd_phase_id value you want to match
    :param phase_ids: the _pd_refln_phase_id values of each hkld value.
    :return: a list containing the corresponding hkld values, or None, if none match.
    """
    if hklds is None:
        return None
    else:
        hkld = []
        for hkldval, idval in zip(hklds, phase_ids):
            if idval == phase_id:
                hkld += [hkldval]
        return hkld


def split_val_err(ve, default_error="zero"):
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
        if default_error == "sqrt":
            return (float(ve), math.sqrt(math.fabs(float(ve))))
        else:
            if ve == "." or ve == "?":
                ve = 'nan'
            return (float(ve), 0.0)
    value, error = re.search("([0-9.]+)\(([0-9]*)\)", ve).groups()
    if "." not in value:  # it makes it much easier if there is a decimal place to count
        value += "."
    pow10 = len(value) - value.find(".") - 1
    return (float(value), float(error) / 10 ** pow10)


def split_val_err_list(inlist, default_error="zero"):
    """
    Takes a list of strings representing values with/without errors and gives back a tuple
    of two lists of floats. The first is the values, the second is the errors
    :param default_error: if there is no error present, what do you want it to be? "zero" == 0, "sqrt" == sqrt(val)
    :param inlist: list of strings representing floats
    :return: tuple of lists of floats containing valus and errors.
    """
    vals = []
    errs = []
    for entry in inlist:
        v, e = split_val_err(entry, default_error=default_error)
        vals.append(v)
        errs.append(e)
    return (vals, errs)


def calc_cumchi2(cifpat, yobs_dataname, ycalc_dataname, yobs_dataname_err=None, ymod_dataname=None):
    """
    Calculate the cumulative Rwp statistic using the given yobs, ycalc, uncertinaty, and y_modifier.
    This is the value of Rwp taking into account only the data with the x-ordinate <= the current
    x-ordinate. It shows where there are large deviations contributing to the overall Rwp
    see eqn 8 - David, W.I. 2004. "Powder Diffraction: Least-Squares and Beyond." Journal of Research of the National Institute of Standards and Technology 109 (1): 107-23. https://doi.org/10.6028/jres.008.
    :param cifpat: dictionary representation of the cif pattern you want
    :param yobs_dataname: dataname of the yobs value
    :param ycalc_dataname: dataname of the ycalc value
    :param yobs_dataname_err: defaults to the '_pd_proc_ls_weight'. If this isn't present, it goes for the "_err" column
    :param ymod_dataname: this currently does nothing.
    :return: a numpy array with values of Rwp. It has the same length as yobs
    """
    yobs = cifpat[yobs_dataname]
    ycalc = cifpat[ycalc_dataname]

    if ymod_dataname is not None:  # I don't know what ymod means yet...
        return [-1] * len(yobs)
    if yobs_dataname_err is None:
        if "_pd_proc_ls_weight" in cifpat:
            yweight = cifpat["_pd_proc_ls_weight"]
        else:
            yobs_dataname_err = yobs_dataname + "_err"
            yweight = 1 / (cifpat[yobs_dataname_err] ** 2)
    else:
        yobs_dataname_err = yobs_dataname + "_err"
        yweight = 1 / (cifpat[yobs_dataname_err] ** 2)

    return np.nancumsum(yweight * (yobs - ycalc) ** 2) #treats nan as 0





class ParseCIF:
    # these are all the values that could be an x-ordinate. I added the last two to be place-holders
    # for d and/or q calculated from Th2, q, or d, where it is possible from the data in the pattern.
    COMPLETE_X_LIST = ["_pd_meas_2theta_scan", "_pd_proc_2theta_corrected", "_pd_meas_time_of_flight",
                       "_pd_meas_position", "_pd_proc_energy_incident",
                       "_pd_proc_d_spacing", "_pd_proc_recip_len_Q", "d", "q"]  # "_pd_proc_wavelength",

    # These are datanames that fit correspond to the data you are modelling
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

    NICE_TO_HAVE_DATANAMES = ['_diffrn_radiation_wavelength', "_cell_measurement_wavelength",
                              "_diffrn_ambient_temperature", "_cell_measurement_temperature",
                              "_diffrn_ambient_pressure", "_cell_measurement_pressure",
                              "_pd_meas_datetime_initiated"]

    DATANAMES_THAT_SHOULD_BE_NUMERIC = ["_pd_phase_mass_%", "_refln_d_spacing"] + \
                                       COMPLETE_X_LIST + COMPLETE_Y_LIST + MODIFIER_Y_LIST + \
                                       NICE_TO_HAVE_DATANAMES[:-1]

    def __init__(self, ciffilename, scantype="flex", grammar="1.1", scoping="dictionary", permissive=False):
        #print(f"Now reading {ciffilename}. This may take a while.")
        self.ciffile = CifFile.ReadCif(ciffilename, scantype=scantype, grammar=grammar, scoping=scoping, permissive=permissive)
        self.ncif = {}  # this will be the cif file with pattern information only
        self.cif = {}

        self._remove_empty_items()
        self._expand_multiple_dataloops()
        self._process()

    def _remove_empty_items(self):
        """
        Checks every item in each block and if all the values are '?' or '.', it removes them from the cif
        :return: nother. alters in place
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
                    if value == "." or value == "?":
                        cifblk.RemoveItem(item)
                else:
                    print("How did we even get here?")

    def _expand_multiple_dataloops(self):
        """
        This looks for patterns which have multiple loops containing diffraction data
        This clones the block as many times as there are loops, with each clone containing
        only one diffraction data loop. All other information is the same
        :return: nothing. alters ciffile in place
        """
        patterns = grouped_blocknames(self.ciffile)["patterns"]

        for pattern in patterns:
            cifpat = self.ciffile[pattern]
            loops = copy.deepcopy(cifpat.loops)  # this needs to be a deepcopy or it updates itself on RemoveItem !
            keys_of_loops = []
            for key in loops.keys():
                looped_datanames = loops[key]
                if any(x in looped_datanames for x in ParseCIF.COMPLETE_X_LIST):
                    keys_of_loops.append(key)

            if len(keys_of_loops) == 1:
                continue  # because there is only one data loop in this pattern

            # we only get to here if there are many data loops in the cif
            # deepcopy the pattern so I can clone it
            dcopy = copy.deepcopy(self.ciffile[pattern])
            # rename the current pattern and remove the required dataloops.
            for i, key in enumerate(keys_of_loops):
                if i == 0:
                    continue
                remove_these = loops[key]
                for dataname in remove_these:
                    cifpat.RemoveItem(dataname)
            self.ciffile.rename(pattern, pattern + "_loop0")

            # add a deepcopy of dcopy into the ciffile and remove the required dataloops. Will
            #  need to alter ciffile.block_input_order in order to keep things aligned?
            # ciffile.NewBlock(self, blockname, blockcontents=None, fix=True, parent=None)
            # repeat the previous step as needed to copy in all the dataloops
            for i in range(1, len(keys_of_loops)):
                insert_me = copy.deepcopy(dcopy)
                for j, key in enumerate(keys_of_loops):
                    if j == i:
                        continue  # ie don't delete the dataloop that this one is supposed to keep
                    remove_these = loops[key]
                    for dataname in remove_these:
                        insert_me.RemoveItem(dataname)
                self.ciffile.NewBlock(pattern + "_loop" + str(i), insert_me)

        patterns = grouped_blocknames(self.ciffile)["patterns"]
        for pattern in patterns:
            cifpat = self.ciffile[pattern]
            # this bit looks at the x ordinate and if they are part of this list, I remove any link to structures
            can_no_do_d = ["_pd_meas_time_of_flight", "_pd_meas_position", ]  # "_pd_proc_wavelength",
            can_do_d = ["_pd_meas_2theta_scan", "_pd_proc_2theta_corrected", "_pd_proc_energy_incident",
                        "_pd_proc_d_spacing", "_pd_proc_recip_len_Q"]
            if any(x in cifpat for x in can_no_do_d) and not any(x in cifpat for x in can_do_d):
                cifpat.RemoveItem("_pd_phase_id")
                cifpat.RemoveItem("_pd_phase_block_id")

            # This bit removes the wavelength if the x-ordinate is "_pd_meas_time_of_flight"
            if "_pd_meas_time_of_flight" in cifpat:
                cifpat.RemoveItem("_diffrn_radiation_wavelength")
                cifpat.RemoveItem("_cell_measurement_wavelength")

    def _process(self):
        """
        only run this on cifs that have been unrolled so that they contain only one
        dataloop of diffraction information.
        :return:
        """
        lookup_blockid = blockname_lookupdict_from_blockid(self.ciffile)  # a dictionary with block_id keys and dataname values
        blocknames = grouped_blocknames(self.ciffile)  # blocknames corresponding to patterns, structures, and others.

        # get all patterns and others. Don't get structures here, as I only want to get structures linked to each pattern.
        patterns = blocknames["patterns"]
        others = blocknames["others"]

        self.cif = convert_cif_to_dict(self.ciffile)
        # update each pattern's information
        for pattern in patterns:
            #print(f"Now doing {pattern}")
            cifpat = self.cif[pattern]
            structures = []  # assume there are no linked structures unless it gets updated just below

            if "_pd_phase_block_id" in cifpat:  # then it is linked to other structures
                # check if the x-ordinate is capable of being converted into d-spacing

                # do I need to check that the structure linked to by the pattern also links back to the pattern?
                # get the block_ids and the structures linked to this particular pattern
                phase_block_ids = cifpat["_pd_phase_block_id"]
                if isinstance(phase_block_ids, str): # it needs to be as a list for later
                    phase_block_ids = [phase_block_ids]
                structures = [lookup_blockid[block_id] for block_id in phase_block_ids if block_id in lookup_blockid.keys()]

                # setup the phase_ids in the cif so I can get the correct phaseid for each structure I call
                if "_pd_phase_id" not in cifpat:
                    pd_phase_ids = [str(i) for i in list(range(1, len(phase_block_ids) + 1))]  # keep it as a string, just like pycifrw does
                    # cifpat.AddToLoop("_pd_phase_block_id", {"_pd_phase_id": pd_phase_ids})
                    cifpat["_pd_phase_id"] = pd_phase_ids

                # now we know there are linked structures, and a phase id block, I can
                # make places to put all of the structural information in the cif
                if "str" not in cifpat:
                    cifpat["str"] = {}
                for pd_phase_id in cifpat["_pd_phase_id"]:
                    cifpat["str"][pd_phase_id] = {}

                # look for hkld values
                if '_refln_d_spacing' not in cifpat:  # then it is OK to look for them in other places
                    for i, structure in enumerate(structures):
                        cifstr = self.cif[structure]
                        pd_phase_id = cifpat["_pd_phase_id"][i]
                        hkld_dict = get_hklds(cifstr)
                        if hkld_dict is None:
                            continue

                        # add the data to the pattern datablock and make a loop of it
                        cifpat["str"][pd_phase_id]['_refln_index_h'] = hkld_dict["h"]
                        cifpat["str"][pd_phase_id]['_refln_index_k'] = hkld_dict["k"]
                        cifpat["str"][pd_phase_id]['_refln_index_l'] = hkld_dict["l"]
                        cifpat["str"][pd_phase_id]['_refln_d_spacing'] = hkld_dict["d"]
                else:  # refl_d_spacing is in the cifpat, and I need to check for multiple phases and
                    #  disperse the results accordingly
                    if "_pd_refln_phase_id" in cifpat:
                        # these contain all the hkls from all the phases
                        hs = get_from_cif(cifpat, '_refln_index_h')
                        ks = get_from_cif(cifpat, '_refln_index_k')
                        ls = get_from_cif(cifpat, '_refln_index_l')
                        ds = get_from_cif(cifpat, '_refln_d_spacing')
                        ids = get_from_cif(cifpat, '_pd_refln_phase_id')

                        for phase_id in cifpat["_pd_phase_id"]: # this used to be _pd_refln_phase_id
                            h = get_hkld_from_matching_id(hs, phase_id, ids)
                            k = get_hkld_from_matching_id(ks, phase_id, ids)
                            l = get_hkld_from_matching_id(ls, phase_id, ids)
                            d = get_hkld_from_matching_id(ds, phase_id, ids)
                            if h is not None:
                                cifpat["str"][phase_id]['_refln_index_h'] = h
                            if k is not None:
                                cifpat["str"][phase_id]['_refln_index_k'] = k
                            if l is not None:
                                cifpat["str"][phase_id]['_refln_index_l'] = l
                            if d is not None:
                                cifpat["str"][phase_id]['_refln_d_spacing'] = d
            # end of if

            # look for other datanames that it would be nice to have in the pattern
            for dataname in ParseCIF.NICE_TO_HAVE_DATANAMES:
                if dataname not in cifpat:  # then need to look for it in different places
                    get_dataname_into_pattern(self.cif, pattern, dataname, structures, others)

                # if it does exist, and it is single-valued, and is not known, then look for it as well
                if dataname in cifpat and (cifpat[dataname] == "." or cifpat[dataname] == "?"):
                    get_dataname_into_pattern(self.cif, pattern, dataname, structures, others)

            self.ncif[pattern] = self.cif[pattern]
        # end of for loop

        # convert everything that should be a float into a float.
        for pattern in self.ncif.keys():
            cifpat = self.ncif[pattern]
            for dataname in ParseCIF.DATANAMES_THAT_SHOULD_BE_NUMERIC:
                if dataname not in cifpat:
                    continue
                if isinstance(cifpat[dataname], list):
                    # should the dataname have an associated uncertainty?
                    # the observed_Y ones should (must?) have. If one isn't explicitiy
                    # given, I take the sqrt of the value
                    if dataname in self.OBSERVED_Y_LIST:
                        val, err = split_val_err_list(cifpat[dataname], default_error="sqrt")
                        cifpat[dataname] = np.asarray(val, dtype=float)
                        cifpat[dataname + "_err"] = np.asarray(err, dtype=float)
                    else:
                        try:
                            cifpat[dataname] = np.asarray(cifpat[dataname], dtype=float)
                        except ValueError:  # probably because numpy got given a thing with an error
                            val, err = split_val_err_list(cifpat[dataname])
                            cifpat[dataname] = np.asarray(val, dtype=float)
                            cifpat[dataname + "_err"] = np.asarray(err, dtype=float)
                elif isinstance(cifpat[dataname], str):
                    if not (cifpat[dataname] == "." or cifpat[dataname] == "?"):
                        try:
                            cifpat[dataname] = float(cifpat[dataname])
                        except ValueError:
                            val, err = split_val_err(cifpat[dataname])
                            cifpat[dataname] = val
                            cifpat[dataname + "_err"] = err

            # now that I've gotten floats, I can do the additional data conversions to give me more
            #  x-axis values and other nice things
            if "_pd_proc_d_spacing" not in cifpat:
                if "_pd_proc_recip_len_Q" in cifpat:
                    cifpat["d"] = 2. * np.pi / cifpat["_pd_proc_recip_len_Q"]
            if "_pd_proc_recip_len_Q" not in cifpat:
                if "_pd_proc_d_spacing" in cifpat:
                    cifpat["q"] = 2. * np.pi / cifpat["_pd_proc_d_spacing"]

            lam = None
            if '_diffrn_radiation_wavelength' in cifpat or "_cell_measurement_wavelength" in cifpat:
                if '_diffrn_radiation_wavelength' in cifpat:
                    lam = cifpat["_diffrn_radiation_wavelength"]
                else:
                    lam = cifpat["_cell_measurement_wavelength"]
                cifpat["wavelength"] = lam

                if "_pd_proc_d_spacing" not in cifpat and "__d" not in cifpat:
                    if "_pd_meas_2theta_scan" in cifpat:
                        cifpat["d"] = lam / (2. * np.sin(cifpat["_pd_meas_2theta_scan"] * np.pi / 360.))
                    elif "_pd_proc_2theta_corrected" in cifpat:
                        cifpat["d"] = lam / (2. * np.sin(cifpat["_pd_proc_2theta_corrected"] * np.pi / 360.))

                if "_pd_proc_recip_len_Q" not in cifpat and "__q" not in cifpat:
                    if "_pd_meas_2theta_scan" in cifpat:
                        cifpat["q"] = 4. * np.pi * np.sin(cifpat["_pd_meas_2theta_scan"] * np.pi / 360.) / lam
                    elif "_pd_proc_2theta_corrected" in cifpat:
                        cifpat["q"] = 4. * np.pi * np.sin(cifpat["_pd_proc_2theta_corrected"] * np.pi / 360.) / lam

            if "str" in cifpat:
                for structure in cifpat["str"].keys():
                    if "_refln_d_spacing" in cifpat["str"][structure]:
                        cifsubstr = cifpat["str"][structure]
                        cifsubstr["_refln_d_spacing"] = np.asarray(cifsubstr["_refln_d_spacing"], dtype=float)
                        cifsubstr["refln_q"] = 2. * np.pi / cifsubstr["_refln_d_spacing"]
                        if lam is not None:
                            cifsubstr["refln_2theta"] = 2. * np.arcsin(lam / (2. * cifsubstr["_refln_d_spacing"])) * 180. / np.pi
                        cifsubstr["refln_hovertext"] = [h + " " + k + " " + l for h, k, l in
                                                        zip(cifsubstr['_refln_index_h'], cifsubstr['_refln_index_k'], cifsubstr["_refln_index_l"])]

        # end of pattern loop

    def get_processed_cif(self):
        return self.ncif

    def get_raw_cif(self):
        return self.ciffile

    def cumrwp(self, pattern, yobs_dataname, ycalc_dataname, yobs_dataname_err=None, ymod_dataname=None):
        """
        Calculate the cumulative Rwp statistic using the given yobs, ycalc, uncertinaty, and y_modifier.
        This is the value of Rwp taking into account only the data with the x-ordinate <= the current
        x-ordinate. It shows where there are large deviations contributing to the overall Rwp
        :param pattern: blockname of the pattern you want
        :param yobs_dataname: dataname of the yobs value
        :param ycalc_dataname: dataname of the ycalc value
        :param yobs_dataname_err: defaults to the "_err" column o the yobs name. If you want '_pd_proc_ls_weight', you need to say so
        :param ymod_dataname: this currently does nothing.
        :return: a numpy array with values of Rwp. It has the same length as yobs
        """
        yobs = self.ncif[pattern][yobs_dataname]
        ycalc = self.ncif[pattern][ycalc_dataname]

        if ymod_dataname is not None:  # I don't know what this means yet...
            return [-1] * len(yobs)
        if yobs_dataname_err is None:
            yobs_dataname_err = yobs_dataname + "_err"
        if yobs_dataname_err == "_pd_proc_ls_weight":
            yweight = self.ncif[pattern][yobs_dataname_err]
        else:
            yweight = 1 / (self.ncif[pattern][yobs_dataname_err] ** 2)
        rwp = np.sqrt(np.cumsum(yweight * (yobs - ycalc) ** 2) / np.cumsum(yweight * yobs ** 2))
        return rwp


# end of class


if __name__ == "__main__":

    #these files failed parsecif parsing
    files =['C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/ya6147Isup2.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/bs0018IIIsup4.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/wf5122ZE0sup2.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/wf5122ZE5_monosup12.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/wf5122ZE5_tetrsup11.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/yb5011TrigonalIn2S3sup4.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/wf5122ZE4_monosup10.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/wf5122ZE3_monosup8.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/wf5122ZE2_monosup6.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/wf5122ZE1_monosup4.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/wf5122ZE4_tetrsup9.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/wf5122ZE3_tetrsup7.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/wf5122ZE2_tetrsup5.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/wf5122ZE1_tetrsup3.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/yb5011TetragonalIn2S3sup2.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/yb5011CubicIn2S3sup3.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/av5015sup2.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/bk0130Isup2.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/hr0041isup4.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/ru2074Rb2W3SeO123sup9.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/iz1029X-raysup2.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/ks0109sup2.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/ru2074Cs2W3SeO122sup8.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/ru2074NH42W3SeO121sup7.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/hw5019Isup2.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/ty1006LTsup3.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/ya6107Isup2.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/br1310IIsup3.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/og5034PY213sup2.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/br1286Isup2.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/br1305IIsup3.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/sk1513Isup2.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/ya6064Isup2.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/br1310Isup2.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/ya6063Isup2.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/hw0101IIsup3.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/sk1513IIsup3.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/og5036PY183alphasup2.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/br1357Isup3.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/kd50322sup3.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/kd50323sup4.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/kd50321sup2.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/kd50324sup5.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/kd50325sup6.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/kd5024115Ksup8.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/kd50327sup8.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/kd50326sup7.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/yh5011phase_Sm2Ti2O7-x-25Csup28.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/bi3053IMsup2.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/yh5011phase_La2Ti2O7-n-25C-monosup13.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/yh5011phase_Nd2Ti2O7-n-25C-monosup20.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/yh5011phase_Pr2Ti2O7-n-25C-monosup24.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/yh5011phase_La2Ti2O7-n-883C-monosup14.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/yh5011phase_La2Ti2O7-n-883C-orthosup15.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/yh5011phase_Nd2Ti2O7-n-1138C-monosup19.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/yh5011phase_Pr2Ti2O7-n-1138C-monosup23.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/cu3043Msup2.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/cu3043Osup3.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/lg3133Isup2.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/cf6258Isup2.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/bi5031ACM-PAMsup5.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/hw5008PST_0.40GPasup4.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/hw5008PST_0.13GPasup3.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/hw5008PST_0.00GPasup2.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/bi5031ACM-PPZsup6.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/hw5008PST-Ba_0.17GPasup14.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/hw5008PST-Ba_0.00GPasup13.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/hw5008PST-Ba_2.75GPasup17.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/hw5008PST-Ba_0.59GPasup15.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/ru2074K2W3SeO124sup10.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/ws5063GeD4_5Ksup2.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/hw5008PST-Ba_0.98GPasup16.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/ws5063SnD4_5Ksup3.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/hw5008PST_1.84GPasup7.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/hw5008PST_5.10GPasup10.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/hw5008PST_7.35GPasup12.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/hw5008PST_2.63GPasup8.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/cv2721Isup2.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/kd5008LiNCSsup2.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/sk1538Isup2.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/hw5008PST_5.48GPasup11.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/lh5832Isup2.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/xu2006Isup2.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/hw5008PST_1.51GPasup6.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/hw5008PST_3.58GPasup9.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/hw5008PST_1.09GPasup5.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/bp5070IIsup4.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/hw5008PST-Ba_3.52GPasup18.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/hw5008PST-Ba_6.87GPasup19.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/wn6225Isup2.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/kc5021Li10.35Si1.35P1.65S12_at_17Ksup2.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/kc5021Li9.81Sn0.81P2.19S12_at_12Ksup5.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/kc5021Li10.35Si1.35P1.65S12_at_300Ksup3.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/kc5021Li9.81Sn0.81P2.19S12_at_300Ksup6.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/kc5021Li9.81Sn0.81P2.19S12_at_800Ksup7.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/kc5021Li10.35Si1.35P1.65S12_at_800Ksup4.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/ws5045sup2.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/wm2094Isup2.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/os0078gesnmesup3.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/iz1043Isup2.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/sn5110bi10mo3o24_3d_phasesup3.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/sn5110bi10mo3o24_ssp_phasesup5.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/lh2648Isup2.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/br1236sup2.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/sn5110bi14mo5o36_3d_phasesup7.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/lh2866Isup2.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/vn2088Isup2.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/sn5110bi14mo5o36_ssp_phasesup9.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/br1336IIsup3.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/qd0006Isup2.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/sf3190IIsup2.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/bi3053ITsup3.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/ed5011ACMNAMIsup4.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/ed5011ACMVLMsup6.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/ed5011ACMPABAsup5.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/ed5011ACMNAMHsup3.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/sn5110bi8mo3o21_3d_phasesup15.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/os0078sisnmesup2.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/lh5126Isup2.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/sn5110bi8mo3o21_ssp_phasesup17.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/er2073Isup2.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/og5036PY191betasup4.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/kd5008CuL2sup3.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/iz1026Isup2.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/sn5110bi6mo2o15_3d_phasesup11.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/ed5011ACM2HPsup2.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/ya2118Isup2.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/lh2329IIsup2.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/cu3037Isup3.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/sn5110bi6mo2o15_ssp_phasesup13.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/he0320IIIsup6.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/ks0107sup2.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/bi50027-Csup5.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/sf3190IVsup3.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/ya2062Isup2.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/lh5082Isup2.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/ks0107sup3.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/bi5002D-1-Asup6.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/og5036PY191alphasup3.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/bi50025-Asup2.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/bi50025-Dsup3.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/bi5002rac-1sup7.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/bi50025-Esup4.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/he0320Isup2.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/sn0029Isup2.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/he0320IIsup4.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/yh5011phase_Yb2Ti2O7-x-25Csup6.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/yh5011phase_Yb2Ti2O7-x-1550Csup5.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/yh5011phase_Y2Ti2O7-x-1685Csup3.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/yh5011phase_Y2Ti2O7-x-25Csup4.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/yh5011phase_Sm2Ti2O7-x-1674Csup27.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/yh5011phase_Dy2Ti2O7-x-25Csup8.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/yh5011phase_Er2Ti2O7-x-1545Csup9.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/yh5011phase_Er2Ti2O7-x-25Csup10.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/yh5011phase_Dy2Ti2O7-x-1516Csup7.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/ya6211Isup2.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/bi5031ACM-CPRsup4.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/yh5011phase_Gd2Ti2O7-x-25Csup12.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/yh5011phase_Gd2Ti2O7-x-1534Csup11.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/wm5581Isup2.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/yh5011phase_La2Ti2O7-x-25C-monosup16.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/yh5011phase_Pr2Ti2O7-x-25C-monosup26.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/yh5011phase_La2Ti2O7-x-855C-monosup17.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/yh5011phase_La2Ti2O7-x-898C-orthosup18.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/yh5011phase_Pr2Ti2O7-x-1345C-monosup25.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/og5067IIsup3.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/fa3079Isup2.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/wm2726Isup2.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/wm2324Isup2.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/wm5021Isup2.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/wm2244Isup2.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/lg3071Isup3.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/yh5011phase_Nd2Ti2O7-x-25C-monosup22.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/yh5011phase_Nd2Ti2O7-x-1456C-monosup21.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/gt3018Isup3.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/fa3396Isup2.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/sk3362IIsup3.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/og5013Isup2.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/yo30461asup2.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/sq3214Isup2.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/dq5022IIsup3.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/dq5022Isup2.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/tu5005Tl2LiYCl6_cubic_537Ksup3.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/dq5022VIsup7.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/dq5022Vsup6.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/dq5022VIIsup8.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/na0125Isup2.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/kd5029sup3.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/kc5042TCL_ABsup2.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/dq5022IIIsup4.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/yo30462asup3.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/og5067Isup2.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/yh5008CAS-850Ksup2.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/yh5008SAS-850Ksup4.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/wm6101IIsup2.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/wm6100Isup2.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/vn2075Isup2.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/yh5008SAS-850Ksup5.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/yh5008CAS-850Ksup3.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/br1322Isup2.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/iz1021Isup2.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/br1322IIsup3.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/zb5005betastrontiumdiformate540Ksup4.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/zb5005betastrontiumdiformate334Ksup3.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/zb5005alphastrontiumdiformate293Ksup2.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/zb5005deltastrontiumdiformate605Ksup5.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/zb5005betastrontiumfumarate105Ksup7.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/zb5005alphastrontiumfumarate293Ksup6.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/yh5008SAS-1100Ksup6.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/ws5037sup2.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/bk5091Ca8Pb12Si12O42Cl3.8O0.1sup9.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/bk5091Pb15Ge9O33sup3.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/ks5226sup2.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/sn5110bi10mo3o24_3d_phasesup2.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/sn5110bi10mo3o24_ssp_phasesup4.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/sn5110bi14mo5o36_3d_phasesup6.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/sn5110bi8mo3o21_3d_phasesup14.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/sn5110bi14mo5o36_ssp_phasesup8.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/sn5110bi8mo3o21_ssp_phasesup16.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/sn5110bi6mo2o15_3d_phasesup10.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/sn5110bi6mo2o15_ssp_phasesup12.rtv.combined.cif', 'C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/ra5050Isup2.rtv.combined.cif']


    # # filename = r"..\..\data\forJames_before.cif"
    # filename = r"..\..\data\ideal_condensed.cif"
    # filename = r"..\..\data\ideal_strsWithHKLs_condensed.cif"
    # filename = r"..\..\data\nisi.cif"
    # filename = r"..\..\data\ideal_5patterns.cif"
    # filename = r"..\..\data\pam\ws5072ibuprofen_all.cif"
    # filename = r"..\..\data\pam\mag_cif_testfile_modified.cif"
    #
    # _diffrn_wavelength = two values for ka1 ka2

    import os
    # #18
    # filename = files[189]
    filename = r"C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/rw5065LSCT10_NPDsup4.rtv.combined.cif"
    # os.system("start " + filename)
    cf = ParseCIF(filename)
    cif_dict = cf.get_processed_cif()
    pretty(cif_dict, print_values=True)
    chi2 = calc_cumchi2(cif_dict["npd"], "_pd_proc_intensity_net","_pd_calc_intensity_net")
    print(chi2)
    # print(filename)
    # print(files[18])
    #18 could not convert string to float: 'YES' C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/hr0041isup4.rtv.combined.cif

#
    # for i in range(len(files)):
    #     filename = files[i]
    #     try:
    #         cf = ParseCIF(filename)
    #         # print(i)
    #     except Exception as e:
    #         print(f"{i}\t{e}\t{filename}")
    #         continue





    # print(cf.rwp("pattern_0", "_pd_meas_intensity_total", "_pd_calc_intensity_total", "_pd_proc_ls_weight"))

    # print(type(cf))

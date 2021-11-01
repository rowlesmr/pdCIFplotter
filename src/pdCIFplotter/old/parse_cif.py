import math
import numpy as np
import CifFile


def pretty(d, indent=0, print_values=True):
    for key, value in d.items():
        print('\t' * indent + str(key))
        if isinstance(value, dict):
            pretty(value, indent + 1)
        else:
            if print_values:
                print('\t' * (indent + 1) + str(value))


def convert_cif_to_dict(cif):
    key_list = cif.block_input_order
    cif_dict = cif.__dict__["dictionary"]
    for key in key_list:  # Python >=3.7 keeps dictionary keys in insertion order: https://mail.python.org/pipermail/python-dev/2017-December/151283.html
        cif_dict[key] = cif[key].__dict__["block"]
        for sub_key in cif_dict[key].keys():
            cif_dict[key][sub_key] = cif_dict[key][sub_key][0]
    return cif_dict


def blockname_lookupdict_from_blockid(cif):
    lookup_dict = {}
    for blockname in cif.block_input_order:
        if "_pd_block_id" in cif[blockname]:
            lookup_dict[cif[blockname]["_pd_block_id"]] = blockname
    return lookup_dict


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


def get_from_cif(cif, blockname):
    if blockname in cif:
        return cif[blockname]
    else:
        return None


def get_hklds(structure):
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


from timeit import default_timer as timer


class ParseCIF:
    COMPLETE_X_LIST = ["_pd_meas_2theta_scan", "_pd_proc_2theta_corrected", "_pd_meas_time_of_flight",
                       "_pd_meas_position", "_pd_proc_energy_incident", "_pd_proc_wavelength",
                       "_pd_proc_d_spacing", "_pd_proc_recip_len_Q", "__d", "__q"]

    COMPLETE_Y_LIST = ["_pd_meas_counts_total", "_pd_meas_intensity_total", "_pd_proc_intensity_total",
                       "_pd_proc_intensity_net", "_pd_calc_intensity_net", "_pd_calc_intensity_total",
                       "_pd_meas_counts_background", "_pd_meas_counts_container", "_pd_meas_intensity_background",
                       "_pd_meas_intensity_container", "_pd_proc_intensity_bkg_calc", "_pd_proc_intensity_bkg_fix"]

    NICE_TO_HAVE_DATANAMES = ['_diffrn_radiation_wavelength', "_cell_measurement_wavelength",
                              "_diffrn_ambient_temperature", "_cell_measurement_temperature",
                              "_diffrn_ambient_pressure", "_cell_measurement_pressure",
                              "_pd_meas_datetime_initiated"]

    DATANAMES_THAT_SHOULD_BE_NUMERIC = ["_pd_phase_mass_%", "_refln_d_spacing"] + \
                                       COMPLETE_X_LIST + COMPLETE_Y_LIST + NICE_TO_HAVE_DATANAMES[:-1]

    def __init__(self, filename, scantype="flex", grammar="1.1", scoping="dictionary", permissive=False):

        start = timer()
        self.cif = CifFile.ReadCif(filename, scantype=scantype, grammar=grammar, scoping=scoping, permissive=permissive)
        self.ncif = CifFile.CifFile()  # this will be the cif file with pattern information only
        self.cif_dict = {} # this is what will be passed out to be used
        end_read = timer()

        lookup_blockid = blockname_lookupdict_from_blockid(self.cif)  # a dictionary with block_id keys and dataname values
        blocknames = grouped_blocknames(self.cif)  # blocknames corresponding to patterns, structures, and others.

        # get all patterns and others. Don't get structures here, as I only want to get structures linked to each pattern.
        patterns = blocknames["patterns"]
        others = blocknames["others"]

        # update each pattern's information
        for pattern in patterns:
            cifpat = self.cif[pattern]
            structures = []  # assume there are no linked structures unless it gets updated just below
            if "_pd_phase_block_id" in cifpat:  # then it is linked to other structures
                # get the block_ids and the structures linked to this particular pattern
                phase_block_ids = cifpat["_pd_phase_block_id"]
                structures = [lookup_blockid[block_id] for block_id in phase_block_ids]

                # setup the phase_ids in the cif so I can get the correct phaseid for each structure I call
                if "_pd_phase_id" not in pattern:
                    pd_phase_ids = [str(i) for i in list(range(1, len(phase_block_ids) + 1))]  # keep it as a string, just like pycifrw does
                    cifpat.AddToLoop("_pd_phase_block_id", {"_pd_phase_id": pd_phase_ids})

                # these are for the pattern
                h = []
                k = []
                l = []
                d = []
                n = []  # to hold the phase num

                # look for hkld values
                if '_refln_d_spacing' not in cifpat:  # then it is OK to look for them in other places
                    for structure in structures:
                        cifstr = self.cif[structure]
                        pd_phase_id = getattr(cifpat.GetLoop("_pd_phase_block_id").GetKeyedPacket("_pd_phase_block_id", cifstr["_pd_block_id"]), "_pd_phase_id")
                        hkld_dict = get_hklds(cifstr)
                        if hkld_dict is None:
                            continue
                        h += hkld_dict["h"]
                        k += hkld_dict["k"]
                        l += hkld_dict["l"]
                        d += hkld_dict["d"]
                        n += [pd_phase_id] * len(hkld_dict["d"])

                        # add the data to the pattern datablock and make a loop of it
                        cifpat['_refln_index_h'] = h
                        cifpat['_refln_index_k'] = k
                        cifpat['_refln_index_l'] = l
                        cifpat['_refln_d_spacing'] = d
                        cifpat['_pd_refln_phase_id'] = n
                        cifpat.CreateLoop(['_refln_index_h', '_refln_index_k', '_refln_index_l', '_refln_d_spacing', "_pd_refln_phase_id"])

            # look for other datanames that it would be nice to have in the pattern
            for dataname in ParseCIF.NICE_TO_HAVE_DATANAMES:
                if dataname not in cifpat:  # then need to look for it in other places
                    get_dataname_into_pattern(self.cif, pattern, dataname, structures, others)
        # end of for loop

        # now that the pattern is full of all the info, I can just grab the pattern info and do things
        #  with the patterns and make things numeric, and the like
        for pattern in patterns:
            self.ncif[pattern] = self.cif[pattern]

        self.cif_dict = convert_cif_to_dict(self.ncif)

        # convert everything that should be a float into a float.
        for pattern in self.cif_dict.keys():
            cifpat = self.cif_dict[pattern]
            for dataname in ParseCIF.DATANAMES_THAT_SHOULD_BE_NUMERIC:
                if dataname not in cifpat:
                    continue
                if isinstance(cifpat[dataname], list):
                    cifpat[dataname] = np.asarray(cifpat[dataname], dtype=float)
                elif isinstance(cifpat[dataname], str):
                    cifpat[dataname] = float(cifpat[dataname])

            # now that I've gotten floats, I can do the additional data conversions to give me more
            #  x-axis values and other nice things
            if "_pd_proc_d_spacing" not in cifpat:
                if "_pd_proc_recip_len_Q" in cifpat:
                    cifpat["d"] = 2. * np.pi / cifpat["_pd_proc_recip_len_Q"]
            if "_pd_proc_recip_len_Q" not in cifpat:
                if "_pd_proc_d_spacing" in cifpat:
                    cifpat["q"] = 2. * np.pi / cifpat["_pd_proc_d_spacing"]

            if '_diffrn_radiation_wavelength' in cifpat or "_cell_measurement_wavelength" in cifpat:
                if '_diffrn_radiation_wavelength' in cifpat:
                    lam = cifpat["_diffrn_radiation_wavelength"]
                else:
                    lam = cifpat["_cell_measurement_wavelength"]

                if "_pd_proc_d_spacing" not in cifpat and "__d" not in cifpat:
                    if "_pd_meas_2theta_scan" in cifpat:
                        cifpat["d"] = lam / (2. * np.sin(cifpat["_pd_meas_2theta_scan"] * np.pi / 360.))
                    elif "_pd_proc_2theta_corrected" in cifpat:
                        cifpat["d"] = lam / (2. * np.sin(cifpat["_pd_proc_2theta_corrected"] * np.pi / 360.))

                if "_pd_proc_recip_len_Q" not in cifpat and "__q" not in cifpat:
                    if "_pd_meas_2theta_scan" in cifpat:
                        cifpat["q"] = 4. * np.pi * np.sin(cifpat["_pd_meas_2theta_scan"] * np.pi / 360.) / lam
                    elif "_pd_proc_2theta_corrected" in cifpat:
                        cifpat["q"] = 4. * np.pi * np.sin(cifpat["_pd_meas_2theta_scan"] * np.pi / 360.) / lam

                if "_refln_d_spacing" in cifpat:
                    cifpat["refln_q"] = 2. * np.pi / cifpat["_refln_d_spacing"]
                    cifpat["refln_2theta"] = 2. * np.arcsin(lam / (2. * cifpat["_refln_d_spacing"])) * 180. / np.pi
                    cifpat["refln_hovertext"] = [h + " " + k + " " + l for h, k, l in zip(cifpat['_refln_index_h'], cifpat['_refln_index_k'], cifpat["_refln_index_l"])]
        # end of pattern loop

        # end_init = timer()
        #
        # print(f"Read time is {end_read - start} s.")
        # print(f"Proc time is {end_init - end_read} s.")


# end of class


# ciffile = r"data\forJames_before.cif"
# ciffile = r"data\ideal_condensed.cif"
# ciffile = r"data\ideal_strsWithHKLs_condensed.cif"
# ciffile = r"data\ideal_strsWithHKLs_condensed.cif"
ciffile = r"data\ideal.cif"

cf = ParseCIF(ciffile).ncif

# print(cif)

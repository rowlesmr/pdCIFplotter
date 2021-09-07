from glob import glob
import numpy as np
import CifFile
import plotly.graph_objects as go

class Node:
    def __init__(self, value, parent=None, patterns=None, structures=None, siblings=None):
        self.value = value
        self.parent = parent
        self.patterns = patterns
        self.structures = structures
        self.siblings = siblings

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
    if bracket_val == -1: # there is no bracket
        return float(s)
    else: # there is a bracket
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
    second_bracket = s.find(")")

    if first_bracket == -1: # there is no bracket
        return (float(s), 0.0)

    # now the value has an error
    val_s = s[0:first_bracket]
    err_s = s[first_bracket+1:second_bracket]

    # find the power of ten by which I need to change the err_s in order to give it the
    #  correct value when disassociated from the value - ie give it the right number of
    #  decimal places
    if "." not in val_s:
        val_s += "."  # ie 10 == 10., but now the string calculations below actually work
    dps = len(val_s) - val_s.find(".") - 1
    power_of_ten = dps - len(err_s)

    if power_of_ten >= 0:
        err_s = "0." + ("0"*power_of_ten) + err_s
    else:
        power_of_ten = -power_of_ten
        err_s = err_s[:power_of_ten] + "." + err_s[power_of_ten:]

    return (float(val_s), float(err_s))


def cifstrlist_to_nparray(sl):
    """
    converts a list of strings representing floats into a numpy array iwth two columns.
    The first column contains the values. The second column contains the errors.
    If no error is given, then the value 0 is returned.

    Can be used as: val, err = cifstrlist_to_nparray(sl)

    :param sl: list of strings containing numeric values
    :return: np.array of
    """
    return np.array([cifstr_to_double_tuple(d) for d in sl]).transpose()


def main():
    # a shortcut to reference the correct column in a numpy array that contains values and errors
    VAL = 0
    ERR = 1

    ciffile = "../data/ALUMINA.cif"
    cif = CifFile.ReadCif(ciffile)

    for key, _ in cif["alumina_publ"].items():
        print(key)

    print(cifstrlist_to_nparray(cif["alumina_publ"]["_pd_meas_intensity_total"]))

    lst = [cifstrlist_to_nparray(d) for d in cif["alumina_publ"]["_pd_meas_intensity_total"]]
    print(lst)
    print(lst[VAL])
    print(lst[ERR])


if __name__ == '__main__':
    main()
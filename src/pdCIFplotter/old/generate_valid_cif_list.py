import CifFile
import parse_cif_better as pc
import os
import sys
sys.tracebacklimit = 0

path = "C:/Users/184277j/Documents/GitHub/pdCIFplotter/data/simon/cifs/"



files = [path+f for f in os.listdir(path) if os.path.isfile(path+f) and f.endswith(".cif")]



files = sorted( files, key =  lambda x: os.stat(os.path.join(".", x)).st_size)



print(f"There are {len(files)} CIF files in the current directory.")

good_files=[]
bad_files =[]
parseCIF_bad=[]
for i, file in enumerate(files):
    try:
        CifFile.ReadCif(file)
    except:
        bad_files.append(file)
        continue
    finally:
        good_files.append(file)

    try:
        pc.ParseCIF(file)
        print(".")
    except:
        print(f"{i} ParseCIF can't handle {file}.")
        parseCIF_bad.append(file)

print(parseCIF_bad)
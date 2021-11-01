import CifFile
import cProfile, pstats

def main():

    print("Reading cif")
    ciffile = "../../data/ideal.cif"
    profiler = cProfile.Profile()
    profiler.enable()

    # scantype="flex" uses C library for some of the parsing. A lot faster than pure python, but can't do CIF2.
    cif = CifFile.ReadCif(ciffile, scantype="flex", grammar="1.1", scoping="dictionary", permissive=False)
    #cif = CifFile.ReadCif(ciffile, grammar="1.1", scoping="dictionary", permissive=False)

    profiler.disable()
    stats = pstats.Stats(profiler).sort_stats('cumtime')
    stats.print_stats()




if __name__ == '__main__':
    main()

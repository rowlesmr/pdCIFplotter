
import re
import datetime
from typing import Union

import numpy as np

def parse_datetime(dt: str) -> [datetime, None]:
    dtre = re.compile(r"(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})(:(\d{2})(\.(\d+))?)?(Z|(([+-])(\d{2}):(\d{2})))?")
    match = dtre.fullmatch(dt)

    if match is None:
        raise ValueError(f"{dt} is not a parsable datetime value.")

    groups = match.groups()

    #datetime values
    year = int(groups[0])
    month = int(groups[1])
    day = int(groups[2])
    hour = int(groups[3]) if groups[3] is not None else 0
    minute = int(groups[4]) if groups[4] is not None else 0
    second = int(groups[6]) if groups[6] is not None else 0
    microsecond = int(round(float(groups[7]) * 1000000, 0)) if groups[7] is not None else 0

    # timezone values
    if groups[9] in ["Z", "+00:00"]:
        tz_sign = 1
        tz_hour = 0
        tz_min = 0
        tz_name = "UTC"
    else:
        tz_sign = 0
        if groups[11] is not None:
            tz_sign = -1 if groups[11] == "-" else 1
        tz_hour = int(groups[12]) if groups[12] is not None else 0
        tz_min = int(groups[13]) if groups[13] is not None else 0
        tz_name = groups[9] if groups[9] is not None else "unk"

    tz_min = tz_sign * (tz_min + 60 * tz_hour)

    offset = datetime.timedelta(minutes=tz_min)
    tzinfo = datetime.timezone(offset, name=tz_name)

    return datetime.datetime(
        year,
        month,
        day,
        hour=hour,
        minute=minute,
        second=second,
        microsecond=microsecond,
        tzinfo=tzinfo,
    )

CENTRAL_LOOKUP = {
    "a": ["_cell_length_a", "_cell.length_a"],
    "b": ["_cell_length_b", "_cell.length_b"],
    "c": ["_cell_length_c", "_cell.length_c"],
    "al": ["_cell_angle_alpha", "_cell.angle_alpha"],
    "be": ["_cell_angle_beta" , "_cell.angle_beta" ],
    "ga": ["_cell_angle_gamma", "_cell.angle_gamma"],

}


def dt_to_string(dt: datetime) -> str:
    return str(dt).replace(" ", "T")


def float_from_cif_string(s: Union[str, float]) -> float:
    if isinstance(s, (float, int)):
        return s
    bracket = s.find("(")
    return float(s) if bracket == -1 else float(s[:bracket])


def none_or(val, parent):
    return val if parent is not None else None

class CellParameters:
    def __init__(self, a, b, c, al=90.0, be=90.0, ga=90.0):
        self.a =  float_from_cif_string(a)
        self.b =  float_from_cif_string(b)
        self.c =  float_from_cif_string(c)
        self.al = float_from_cif_string(al)
        self.be = float_from_cif_string(be)
        self.ga = float_from_cif_string(ga)

    def __repr__(self):
        return f"CellParameters({self.a}, {self.b}, {self.c}, {self.al}, {self.be}, {self.ga})"

    def __str__(self):
        return f"({self.a:.6f}, {self.b:.6f}, {self.c:.6f}, {self.al:.6f}, {self.be:.6f}, {self.ga:.6f})"


class AtomPosition:
    def __init__(self, label, x, y, z, atom_type, occupancy=None, multiplicity=None, beq=None):
        self.label = label
        self.x = float_from_cif_string(x)
        self.y = float_from_cif_string(y)
        self.z = float_from_cif_string(z)
        self.atom_type = atom_type
        self.occupancy = occupancy
        self.multiplicity = multiplicity
        self.beq = beq

    def __repr__(self):
        return f"AtomPosition({self.label}, {self.x}, {self.y}, {self.z}, {self.atom_type}, {self.occupancy}, {self.multiplicity}, {self.beq})"

    def __str__(self):
        return f"({self.label}: {self.x:.6f}, {self.y:.6f}, {self.z:.6f}; {self.atom_type} {self.occupancy:.3f} {self.multiplicity}; {self.beq:.3f})"

    def __getitem__(self, item:str):
        match item:
            case "label": return self.label
            case "x": return self.x
            case "y": return self.y
            case "z": return self.z
            case "atom": return self.atom_type
            case "occ": return self.occupancy
            case "mult": return self.multiplicity
            case "B": return self.beq


class Phase:
    def __init__(self, idvalue: str, name: str=None, cell_prms: CellParameters=None, atom_posns: list[AtomPosition]=None):
        self.id = idvalue
        self.name = name
        self.cell_prms: CellParameters = cell_prms
        self.atom_posns: list[AtomPosition] = atom_posns

    def __str__(self):
        return f"{self.name} ({self.id})"

    def __getitem__(self, item:str):
        match item.lower():
            case "id": return self.id
            case "name": return self.name
            case "a": return self.cell_prms.a
            case "b": return self.cell_prms.b
            case "c": return self.cell_prms.c
            case "al": return self.cell_prms.al
            case "be": return self.cell_prms.be
            case "ga": return self.cell_prms.ga


class RFactor:
    def __init__(self, rwp, gof=None, rexp=None, rp=None):
        self.rwp = float_from_cif_string(rwp)
        self.gof = float_from_cif_string(gof)
        self.rexp = float_from_cif_string(rexp)
        self.rp = float_from_cif_string(rp)

    def __str__(self):
        return f"(rwp:{self.rwp:.4f}, gof:{self.gof:.4f}, rexp:{self.rexp:.4f}, rp:{self.rp:.4f})"


class Diffractogram:
    def __init__(self, idvalue: str, xcoords, ycoords):
        self.id: str = idvalue
        self.xcoords: dict[str, np.array] = xcoords
        self.ycoords: dict[str, np.array] = ycoords
        self.order = 0
        self.phases: list[Phase] = None
        self.qpa: list[float] = None
        self.hkls = None
        self.datetime: datetime.datetime = None
        self.wavelength: float = None
        self.rfactors = None
        self.pressure: float = None
        self.temperature: float = None

    def __getitem__(self, item:str):
        match item.lower():
            case "id": return self.id
            case "order": return self.order

            case "datetime": return self.datetime
            case "dtstr": return dt_to_string(self.datetime)
            case "wavelength" | "lambda" | "λ" | "lam": return self.wavelength
            case "pressure": return self.pressure
            case "temperature": return self.temperature

            case "rwp" | "r_wp": return none_or(self.rfactors.rwp, self.rfactors)
            case "gof": return none_or(self.rfactors.gof, self.rfactors)
            case "rexp" | "r_exp": return none_or(self.rfactors.rexp, self.rfactors)
            case "rp" | "r_p": return none_or(self.rfactors.rp, self.rfactors)

            case "2th_meas" | "2θ_meas": return self.xcoords.get("2th_meas")
            case "2th_proc" | "2θ_proc": return self.xcoords.get("2th_proc")
            case "tof": return self.xcoords.get("tof")
            case "position": return self.xcoords.get("position")
            case "energy": return self.xcoords.get("energy")
            case "d": return self.xcoords.get("d")
            case "q": return self.xcoords.get("q")

            case "meas_counts_tot": return self.ycoords.get("meas_counts_tot")
            case "meas_intensity_tot": return self.ycoords.get("meas_intensity_tot")
            case "proc_intensity_tot": return self.ycoords.get("proc_intensity_tot")
            case "proc_intensity_net": return self.ycoords.get("proc_intensity_net")
            case "calc_intensity_bkg": return self.ycoords.get("calc_intensity_bkg")
            case "calc_intensity_tot": return self.ycoords.get("calc_intensity_tot")
            case "calc_intensity_net": return self.ycoords.get("calc_intensity_net")
            case "proc_ls_weight": return self.ycoords.get("proc_ls_weight")
            case "meas_step_count_time": return self.ycoords.get("meas_step_count_time")
            case "proc_intensity_fix_bkg": return self.ycoords.get("proc_intensity_fix_bkg")
            case "meas_counts_monitor": return self.ycoords.get("meas_counts_monitor")
            case "meas_intensity_monitor": return self.ycoords.get("meas_intensity_monitor")
            case "proc_intensity_norm": return self.ycoords.get("proc_intensity_norm")
            case "proc_intensity_incident": return self.ycoords.get("proc_intensity_incident")
            case "meas_counts_bkg": return self.ycoords.get("meas_counts_bkg")
            case "meas_counts_container": return self.ycoords.get("meas_counts_container")
            case "meas_intensity_bkg": return self.ycoords.get("meas_intensity_bkg")
            case "meas_intensity_container": return self.ycoords.get("meas_intensity_container")

            case _: return None

    def add_phases(self, phases: list[Phase]):
        self.phases = phases

    def add_qpa(self, qpa: list):
        self.qpa = [float_from_cif_string(q) for q in qpa]

    def add_rfactors(self, rfactor: RFactor):
        self.rfactors = rfactor

    def add_wavelength(self, wavelength):
        self.wavelength = float_from_cif_string(wavelength)

    def add_datetime_initiated(self, dts: str):
        self.datetime = parse_datetime(dts)

    def add_order(self, order):
        self.order = float(order)

    def add_hkls(self, hkls):
        self.hkls = hkls

    def add_temperature(self, temperature):
        self.temperature = float_from_cif_string(temperature)

    def add_pressure(self, pressure):
        self.pressure = float_from_cif_string(pressure)


if __name__ == '__main__':
    cp1 = CellParameters("4.5991(2)", "9.9268(5)", "3.01059(14)")
    cp2 = CellParameters("5.0253(11)", "5.0253(11)", "13.744(5)", ga="120")

    aps1 = [
            AtomPosition("Fe1", "0.04893", "0.853657", "0.25", "Fe+3", "0.9205(8)", 4, "0.4642662"),
            AtomPosition("Al1", "0.04893", "0.853657", "0.25", "Al+3", "0.0795(8)", 4, "0.4642662"),
            AtomPosition("O1", "0.7057", "0.19914", "0.25", "O-2", "1", 4, "0.5661205"),
            AtomPosition("O2", "0.1987", "0.05298", "0.25", "O-2", "1", 4, "0.5842806")
           ]

    aps2 = [
            AtomPosition("Fe1", "0", "0", "0.35528", "Fe+3", "0.928(7)", "12", "0.35"),
            AtomPosition("Al1", "0", "0", "0.35528", "Al+3", "0.072(7)", "12", "0.35"),
            AtomPosition("O1", "0.3071", "0", "0.25", "O-2", "1", "18", "0.74")
           ]

    p1 = Phase("uuid1", "Goethite", cp1, aps1)
    p2 = Phase("uuid2", "Hematite", cp2, aps2)


    rf = RFactor(0.08219, 1.33237, 0.06168, 0.06355)

    xc = {"2th_meas": np.array([5.007880,5.023636,5.039393])}
    yc = {"meas_counts_tot": np.array([737, 791, 736]),
          "calc_intensity_tot": np.array([805.948339, 799.014950, 792.168220]),
          "calc_intensity_bkg": np.array([805.681930, 798.748050, 791.900820]),
          }

    dp1 = Diffractogram("DIFFPAT1", xc, yc)

    dp1.add_phases([p1, p2])
    dp1.add_rfactors(rf)
    dp1.add_wavelength("1.7889847")
    dp1.add_datetime_initiated("2023-06-19T21:00:34+08:00")
    dp1.add_order(1)
    dp1.add_temperature(293)
    dp1.add_pressure(101.3)

    print(f"{dp1['id']=}")
    print(f"{dp1['order']=}")
    print(f"{dp1['datetime']=}")
    print(f"{dp1['dtstr']=}")
    print(f"{dp1['wavelength']=}")
    print(f"{dp1['λ']=}")
    print(f"{dp1['pressure']=}")
    print(f"{dp1['temperature']=}")
    print(f"{dp1['rwp']=}")
    print(f"{dp1['r_exp']=}")
    print(f"{dp1['r_p']=}")
    print(f"{dp1['2th_meas']=}")
    print(f"{dp1['2θ_meas']=}")
    print(f"{dp1['2th_proc']=}")
    print(f"{dp1['meas_counts_tot']=}")
    print(f"{dp1['meas_intensity_tot']=}")
    print(f"{dp1['calc_intensity_bkg']=}")
    print(f"{dp1['calc_intensity_tot']=}")


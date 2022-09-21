#ifndef CIF_MACROS
#define CIF_MACROS
/*
Written by Matthew Rowles.

The macros to be used by the user are:
* Out_pdCIF,
* Out_pdCIF_multi, and/or potentially,
* Out_pdCIF_per_xdd.

To see their definitions, see the end of this file.

In general:

macro Out_pdCIF_per_xdd(ciffile)                     { Out_pdCIF_per_xdd(ciffile, "proc", =Get(bkg);) }
macro Out_pdCIF_per_xdd(ciffile, data_type)          { Out_pdCIF_per_xdd(ciffile, data_type, =Get(bkg);) }
macro Out_pdCIF_per_xdd(ciffile, data_type, bkq_eqn) {

Out_pdCIF_per_xdd outputs diffraction data and crystal structure information for the xdd under which it is called.

The macro takes three arguments:
ciffile: the name of the file you want to write to. The data is appended.
data_type: "meas" - data as-measured; or "proc" - data has been processed before analysis
bkg_eqn: an equation defining your background function so it can be ouput in the CIF

Two helper macros are given if you only wish to call the macro with one or two arguments. The remaining
arguments are automaticaly set as shown.

###############

macro Out_pdCIF(ciffile)                     { Out_pdCIF(ciffile, "proc", =Get(bkg);) }
macro Out_pdCIF(ciffile, data_type)          { Out_pdCIF(ciffile, data_type, =Get(bkg);) }
macro Out_pdCIF(ciffile, data_type, bkq_eqn) { Out_pdCIF(ciffile, data_type, bkq_eqn, , ) }
macro Out_pdCIF(ciffile, data_type, bkq_eqn, n, m) {

Out_pdCIF outputs diffraction data and crystal structure information for all xdds given in the macro call.
It is meant for use in situations where each xdd is independent of the other xdds.

The macro takes five arguments:
ciffile: the name of the file you want to write to. The data is appended.
data_type: "meas" - data as-measured; or "proc" - data has been processed before analysis
bkg_eqn: an equation defining your background function so it can be ouput in the CIF
n: the inclusive number of the xdd at which to start the pdCIF output
m: the inclusive number of the xdd at which to stop the pdCIF output

The macro with five arguments would be called rarely, and exits for completeness. Normally, the helper
macro with three arguments would be called; this outputs all xdds and all strs in those xdds.

Three helper macros are given if you only wish to call the macro with one, two, or three arguments. The
remaining arguments are automaticaly set as shown.

###############

macro Out_pdCIF_multi(ciffile)                     { Out_pdCIF_multi(ciffile, "proc", =Get(bkg);) }
macro Out_pdCIF_multi(ciffile, data_type)          { Out_pdCIF_multi(ciffile, data_type, =Get(bkg);) }
macro Out_pdCIF_multi(ciffile, data_type, bkg_eqn) { Out_pdCIF_multi(ciffile, data_type, bkg_eqn, 1, ) }
macro Out_pdCIF_multi(ciffile, data_type, bkg_eqn, n, m) {

Out_pdCIF_multi outputs diffraction data and crystal structure information for all xdds given in the macro call.
It is meant for use in situations where some xdds are dependent on other xdds. eg multi-bank tof refinements

The macro takes five arguments:
ciffile: the name of the file you want to write to. The data is appended.
data_type: "meas" - data as-measured; or "proc" - data has been processed before analysis
bkg_eqn: an equation defining your background function so it can be ouput in the CIF
n: the inclusive number of the xdd at which to start the pdCIF output
m: the inclusive number of the xdd at which to stop the pdCIF output

The macro with five arguments would be called in a situation where there are many groups of xdds in a
single inp file. The macro would be called as many times as there are groups, with the start and stop xdd
numbers given in each macro call. It is assumed that each group of xdds is contiguous in the inp file.
In there event of having only a single group in the inp file, the three-argument version can be used.

Three helper macros are given if you only wish to call the macro with one, two, or three arguments. The
remaining arguments are automaticaly set as shown.

###############


To get maximum benefit, copy this file to your TOPAS directory and add
the following line to your local.inc:
#include cif.inc

For updates, check http://topas.dur.ac.uk/topaswiki/doku.php?id=out_pdcif

-----------

MIT License

Copyright (c) 2022 Matthew Rowles

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
*/

'##############################################################'
'Helper macros'
macro TOF_ED_CW(tof,ed,cw) {
/*
This macro allows you to choose between three different things depending
on whether or not the data is TOF, EDXRD, or constant wavelength
*/
	if And(Obj_There(neutron), Or(Prm_There(pk_xo_exists), Obj_There(pk_xo))) { 'neutron TOF'
		tof
	} else if Obj_There(d_spacing_to_energy_in_eV_for_f1_f11) { 'energy-dispersive X-ray'
		ed
	} else { 'constant wavelength X-ray or neutron'
		cw
	}
}

macro & d_spacing_from_TOF(& t0, & t1, & t2) {
' This macro calculates d spacing from TOF'
	(-t1 + Sqrt(t1^2 - 4 t2 (t0 - X))) / (2 t2)
}

macro & d_spacing_from_EDXRD(& th2) { 'degrees'
' This macro calculates d spacing from EDXRD - th2 is the angle of the detector in degrees'
	12398.41974 / ( 2 X Sin(th2 Deg_on_2)) ' X is eV'
	'= (h c / e) / (1x10^-10) -> eV per angstrom'
}

macro n_to_m(n,m) {
	#m_ifarg n ""
		'do nothing'
	#m_else
			#m_ifarg m ""
				'do nothing'
			#m_else
				n## to ##m
			#m_endif
	#m_endif
}

'##############################################################'
' Macros common to diffraction data and crystal structures'
'##############################################################'

macro Out_CIF_newfile(ciffile) {
'Opens a file for appending to.'
	out ciffile append
}

macro Out_CIF_section_break(comment) {
'Inserts a comment in the style of a section break'
	Out_String("\n#######\t")
	Out_String(comment)
	Out_String("\t#######")
}

macro Out_CIF_datablock(blocknamebase, id) {
/*
Create the start of an entry in a CIF file. All CIF files must contain at least
one datablock. The name must be unique.

blocknamebase: a string that you want to appear in the datablock name. No spaces!
id: an identifier to be appended to the blocknamebase to ensure the
    datablock name is unique. No spaces!
*/
	Out_String("\ndata_")
	Out(blocknamebase, "%s")
	Out(id, "_%V")
}
macro Out_CIF_datablock_dataname {
	Out_String("\ndata_")
}

macro Out_unique_phase_id(id) {
	if Prm_There(CIF_PHASE_BLOCK_ID) {
		Out(CIF_PHASE_BLOCK_ID, "%s")
	} else {
		Out(Get(phase_name), "%s")
		Out(id, "_%V")
	}
}

macro Out_unique_diffractogram_id(id) {
	if Prm_There(CIF_DIFFRACTOGRAM_BLOCK_ID) {
		Out(CIF_DIFFRACTOGRAM_BLOCK_ID, "%s")
	} else {
		Out(Get(xdd_path_name), "%s")
		Out(id, "_%V")
	}
}

macro Out_pdCIF_blockid(blockidbase, id) {
/*
https://www.iucr.org/__data/iucr/cifdic_html/1/cif_pd.dic/Ipd_block_id.html
_pd_block_id
   Used to assign a unique character string to a block.
   Note that this code is not intended to be parsed; the
   concatenation of several strings is used in order to
   generate a string that can reasonably be expected to
   be unique.

Note: The pdCIF website for this dataname goes into extensive detail
as to how this block_id is to be constructed. The implementation
is this macro is extremely simplistic, and designed to be easily
automated.
*/
	Out_pdCIF_blockid_dataname
	Out(blockidbase, "%s")
	Out(id, "_%V")
}
macro Out_pdCIF_blockid_dataname {
	Out_String("\n_pd_block_id\t")
}


macro Out_CIF_wavelength {
/*
https://www.iucr.org/__data/iucr/cifdic_html/1/cif_core.dic/Idiffrn_radiation_wavelength.html
_diffrn_radiation_wavelength
   The radiation wavelength in angstroms.
*/
	Out(Lam, "\n_diffrn_radiation_wavelength\t%.9f")
}

macro Out_CIF_free_text(text) {
'Inserts a string into the CIF. Must conform to CIF standards'
	Out_String(text)
}
'##############################################################'
' Macros for diffraction data                                  '
'##############################################################'

macro Out_pdCIF_scan_method(method) {
/*
https://www.iucr.org/__data/iucr/cifdic_html/1/cif_pd.dic/Ipd_meas_scan_method.html
_pd_meas_scan_method
   Code identifying the method for scanning reciprocal space.
   The designation 'fixed' should be used for measurements where
   film, a stationary position-sensitive or area detector
   or other non-moving detection mechanism is used to
   measure diffraction intensities.

the value of "method" you pass in must be one of:-
step :	step scan
cont :	continuous scan
tof  :	time of flight
disp :	energy dispersive
fixed:	stationary detector
*/
	#m_ifarg method "" #m_else
		Out(method, "\n_pd_meas_scan_method\t%s")
	#m_endif
}

macro Out_pdCIF_instr_special_details(goniotype) {
/*
https://www.iucr.org/__data/iucr/cifdic_html/1/cif_pd.dic/index.html
_pd_instr_special_details
   A brief description of the instrument giving
   details that cannot be given in other
   _pd_instr_ entries.
*/
	Out(goniotype, "\n_pd_instr_special_details\n;%s\n;")
}

macro Out_pdCIF_datetime_initiated(datetime) {
/*
https://www.iucr.org/__data/iucr/cifdic_html/1/cif_pd.dic/Ipd_meas_datetime_initiated.html
_pd_meas_datetime_initiated
   The date and time of the data-set measurement. Entries follow
   the standard CIF format 'yyyy-mm-ddThh:mm:ss+zz'. Use
   of seconds and a time zone is optional, but use of hours
   and minutes is strongly encouraged. Where possible, give the
   time when the measurement was started rather than when
   it was completed.
*/
	Out(datetime, "\n_pd_meas_datetime_initiated\t%s")
}

macro Out_CIF_temperature(temp) {
/*
https://www.iucr.org/__data/iucr/cifdic_html/1/cif_core.dic/Idiffrn_ambient_temperature.html
_diffrn_ambient_temperature
   The mean temperature in kelvins at which the intensities
   were measured.
*/
	Out(temp, "\n_diffrn_ambient_temperature\t%V")
}

macro Out_CIF_pressure(pres) {
/*
https://www.iucr.org/__data/iucr/cifdic_html/1/cif_core.dic/Idiffrn_ambient_pressure.html
_diffrn_ambient_pressure
   The mean hydrostatic pressure in kilopascals at which the
   intensities were measured.
*/
	Out(pres, "\n_diffrn_ambient_pressure\t%V")
}

macro Out_pdCIF_2theta_fixed(th2) {
/*
https://www.iucr.org/__data/iucr/cifdic_html/1/cif_pd.dic/Ipd_meas_2theta_fixed.html
_pd_meas_2theta_fixed
   The 2\q diffraction angle in degrees for measurements
   in a white-beam fixed-angle experiment.
*/
	Out(th2, "\n_pd_meas_2theta_fixed\t%s")
}

macro Out_pdCIF_phase_block_id(phase_id, id) {
/*
https://www.iucr.org/__data/iucr/cifdic_html/1/cif_pd.dic/Ipd_phase_block_id.html
_pd_phase_block_id
   A block ID code identifying the phase contributing to
   the diffraction peak. The data block containing the
   crystallographic information for this phase will be
   identified with a _pd_block_id code matching the
   code in _pd_phase_block_id.

https://www.iucr.org/__data/iucr/cifdic_html/1/cif_pd.dic/Ipd_phase_id.html
_pd_phase_id
   A code for each crystal phase used to link with
   _pd_refln_phase_id.

_pd_phase_mass_%
   Per cent composition of the specified crystal phase
   expressed as the total mass of the component
   with respect to the total mass of the specimen.
*/
	Out_String("\nloop_")
	Out_String("\n\t_pd_phase_id")
	Out_String("\n\t_pd_phase_block_id")
	Out_String("\n\t_pd_phase_mass_%")
	for strs {
		Out_String("\n")
		Out(phase_id, "%V\t")
		Out_unique_phase_id(id)
		if Obj_There(spiked_mwp) {
			Out(Get(corrected_weight_percent), "\t%V")
		} else {
			Out(Get(weight_percent), "\t%V")

		}
	}
}

macro Out_CIF_Rfactors {
/*
https://www.iucr.org/__data/iucr/cifdic_html/1/cif_core.dic/Irefine_ls_goodness_of_fit_all.html
_refine_ls_goodness_of_fit_all
   The least-squares goodness-of-fit parameter S for all
   reflections after the final cycle of refinement.
   Ideally, account should be taken of parameters restrained
   in the least-squares refinement. See also
   _refine_ls_restrained_S_ definitions.

       {  sum { w [ Y(obs) - Y(calc) ]^2^ }  }^1/2^
   S = { ----------------------------------- }
       {            Nref - Nparam            }

https://www.iucr.org/__data/iucr/cifdic_html/1/cif_pd.dic/Ipd_proc_ls_prof_.html
_pd_proc_ls_prof_R_factor
_pd_proc_ls_prof_wR_factor
_pd_proc_ls_prof_wR_expected
   Rietveld/profile fit R factors.

   Note that the R factor computed for Rietveld refinements
   using the extracted reflection intensity values (often
   called the Rietveld or Bragg R factor, R~B~) is not properly
   a profile R factor. This R factor may be specified using
   _refine_ls_R_I_factor. (Some authors report
   _refine_ls_R_Fsqd_factor or _refine_ls_R_factor_all
   as the Rietveld or Bragg R factor. While it is appropriate
   to compute and report any or all of these R factors,
   the names "Rietveld or Bragg R factor" refer strictly to
   _refine_ls_R_I_factor.)

              _pd_proc_ls_prof_R_factor, often called R~p~, is an
    unweighted fitness metric for the agreement between the
    observed and computed diffraction patterns.
       R~p~ = sum~i~ | I~obs~(i) - I~calc~(i) |
              / sum~i~ ( I~obs~(i) )
              _pd_proc_ls_prof_wR_factor, often called R~wp~, is a
    weighted fitness metric for the agreement between the
    observed and computed diffraction patterns.
      R~wp~ = SQRT {
               sum~i~ ( w(i) [ I~obs~(i) - I~calc~(i) ]^2^ )
               / sum~i~ ( w(i) [I~obs~(i)]^2^ ) }

              _pd_proc_ls_prof_wR_expected, sometimes called the
    theoretical R~wp~ or R~exp~, is a weighted fitness metric for
    the statistical precision of the data set. For an idealized fit,
    where all deviations between the observed intensities and
    those computed from the model are due to statistical
    fluctuations, the observed R~wp~ should match the expected
    R factor. In reality, R~wp~ will always be higher than
    R~exp~.
      R~exp~ = SQRT {
                     (n - p)  / sum~i~ ( w(i) [I~obs~(i)]^2^ ) }

    Note that in the above equations,
       w(i) is the weight for the ith data point (see
            _pd_proc_ls_weight).
       I~obs~(i) is the observed intensity for the ith data
            point, sometimes referred to as y~i~(obs) or
            y~oi~. (See _pd_meas_counts_total,
            _pd_meas_intensity_total or _pd_proc_intensity_total.)
       I~calc~(i) is the computed intensity for the ith data
            point with background and other corrections
            applied to match the scale of the observed data set,
            sometimes referred to as y~i~(calc) or
            y~ci~. (See _pd_calc_intensity_total.)
       n is the total number of data points (see
            _pd_proc_number_of_points) less the number of
            data points excluded from the refinement.
       p is the total number of refined parameters.
*/
	Out(Get(gof),  "\n_refine_ls_goodness_of_fit_all\t%1.5f")
	Out(Get(r_p)/100,   "\n_pd_proc_ls_prof_R_factor\t%1.5f")
	Out(Get(r_wp)/100,  "\n_pd_proc_ls_prof_wR_factor\t%1.5f")
	Out(Get(r_exp)/100, "\n_pd_proc_ls_prof_wR_expected\t%1.5f")
}

/*
These next set of groups of three macros are for outputting constant-wavelength angle-dispersive data,
time-of-flight neutron data, and energy-dispersive X-ray data.

meas denotes intensity measurements at the measurement point
proc denotes intensity measurements that have been processed in some way at the measurement point
*/
macro Out_pdCIF_angle_dispersive_measured_data(ciffile) {
	Out_pdCIF_angle_dispersive_data(ciffile, meas, =Get(bkg);)
}
macro Out_pdCIF_angle_dispersive_processed_data(ciffile) {
	Out_pdCIF_angle_dispersive_data(ciffile, proc, =Get(bkg);)
}
macro Out_pdCIF_angle_dispersive_data(ciffile, type, bkg_eqn) {
/*
https://www.iucr.org/__data/iucr/cifdic_html/1/cif_pd.dic/Ipd_meas_2theta_scan.html
_pd_meas_2theta_scan
   2\q diffraction angle (in degrees) for intensity
   points measured in a scanning method. The scan method used
   (e.g. continuous or step scan) should be specified in
   the item _pd_meas_scan_method. For fixed 2\q (white-beam)
   experiments, use _pd_meas_2theta_fixed. In the case of
   continuous-scan data sets, the 2\q value should be the
   value at the midpoint of the counting period. Associated
   with each _pd_meas_2theta_scan value will be
   _pd_meas_counts_ items. The 2\q values should
   not be corrected for nonlinearity,
   zero offset etc. Corrected values may be specified
   using _pd_proc_2theta_corrected.

https://www.iucr.org/__data/iucr/cifdic_html/1/cif_pd.dic/Ipd_meas_intensity_.html
_pd_meas_intensity_total
   Intensity measurements at the measurement point (see
   the definition of _pd_meas_2theta_).

   Use this entry for measurements where intensity
   values are not counts (use _pd_meas_counts_ for event-counting
   measurements where the standard uncertainty is
   estimated as the square root of the number of counts).

   Corrections for background, detector dead time etc.,
   should not have been made to these values. Instead use
   _pd_proc_intensity_ for corrected diffractograms.

https://www.iucr.org/__data/iucr/cifdic_html/1/cif_pd.dic/Ipd_proc_intensity_.html
_pd_proc_intensity_total
   This contains intensity values for the
   processed diffractogram for each data point where
   background, normalization and other corrections have not
   been applied.
   Inclusion of s.u. values for these values is strongly recommended.

https://www.iucr.org/__data/iucr/cifdic_html/1/cif_pd.dic/Ipd_proc_ls_weight.html
_pd_proc_ls_weight
   Weight applied to each profile point. These values
   may be omitted if the weights are 1/u^2^, where
   u is the s.u. for the _pd_proc_intensity_net values.

   A weight value of zero is used to indicate a data
   point not used for refinement (see
   _pd_proc_info_excluded_regions).

https://www.iucr.org/__data/iucr/cifdic_html/1/cif_pd.dic/Ipd_calc_intensity_.html
_pd_calc_intensity_total
   Intensity values for a computed diffractogram at
   each angle setting. Values should be computed at the
   same locations as the processed diffractogram, and thus
   the numbers of points will be defined by
   _pd_proc_number_of_points and point positions may
   be defined using _pd_proc_2theta_range_ or
   _pd_proc_2theta_corrected.

   Use _pd_calc_intensity_net if the computed diffractogram
   does not contain background or normalization corrections
   and thus is specified on the same scale as the
   _pd_proc_intensity_net values.

   Use _pd_calc_intensity_total if the computed diffraction
   pattern includes background or normalization corrections
   (or both) and thus is specified on the same scale as the
   observed intensities (_pd_meas_counts_ or _pd_meas_intensity_).

   If an observed pattern is included, _pd_calc_intensity_
   should be looped with either _pd_proc_intensity_net,
   _pd_meas_counts_ or _pd_meas_intensity_.

https://www.iucr.org/__data/iucr/cifdic_html/1/cif_pd.dic/Ipd_proc_intensity_.html
_pd_proc_intensity_bkg_calc
   This is intended to contain the
   background intensity for every data point where the
   background function has been fitted or estimated

ciffile - string. The name of the cif file you want to write to.
bkg_eqn - topas equation. The equation you arre using for your background.
          If you are using the built in bkg, then write "=Get(bkg);" (without the "")
*/
	Out_CIF_newfile(ciffile)
	Out_String("\nloop_")
	Out_String("\n\t_pd_meas_2theta_scan")
	#if type == "meas";
		Out_String("\n\t_pd_meas_intensity_total")
	#else
		Out_String("\n\t_pd_proc_intensity_total")
	#endif
	Out_String("\n\t_pd_proc_ls_weight")
	Out_String("\n\t_pd_calc_intensity_total")
	#m_ifarg bkg_eqn ""
	xdd_out ciffile append
		load out_record out_fmt out_eqn {
			 "\n%11.6f" = X;
			 "\t%11.6f" = Yobs;
			 "\t%11.6f" = Get(weighting);
			 "\t%11.6f" = Ycalc;
		}
	#m_else
	Out_String("\n\t_pd_proc_intensity_bkg_calc")
	xdd_out ciffile append
		load out_record out_fmt out_eqn {
			 "\n%11.6f" = X;
			 "\t%11.6f" = Yobs;
			 "\t%11.6f" = Get(weighting);
			 "\t%11.6f" = Ycalc;
			 "\t%11.6f" bkg_eqn
		}
	#m_endif
}

macro Out_pdCIF_time_of_flight_measured_data(ciffile) {
	Out_pdCIF_time_of_flight_data(ciffile, meas, =Get(bkg);)
}
macro Out_pdCIF_time_of_flight_processed_data(ciffile) {
	Out_pdCIF_time_of_flight_data(ciffile, proc, =Get(bkg);)
}
macro Out_pdCIF_time_of_flight_data(ciffile, type, bkg_eqn) {
/*
https://www.iucr.org/__data/iucr/cifdic_html/1/cif_pd.dic/Ipd_meas_time_of_flight.html
_pd_meas_time_of_flight
   Measured time in microseconds for time-of-flight neutron
   measurements. Note that the flight distance may be
   specified using _pd_instr_dist_ values.

https://www.iucr.org/__data/iucr/cifdic_html/1/cif_pd.dic/Ipd_proc_d_spacing.html
_pd_proc_d_spacing
   d-spacing corresponding to an intensity point
   from Braggs law, d = \l/(2 sin\q), in units of angstroms.

https://www.iucr.org/__data/iucr/cifdic_html/1/cif_pd.dic/Ipd_meas_intensity_.html
_pd_meas_intensity_total
   Intensity measurements at the measurement point (see
   the definition of _pd_meas_2theta_).

   Use this entry for measurements where intensity
   values are not counts (use _pd_meas_counts_ for event-counting
   measurements where the standard uncertainty is
   estimated as the square root of the number of counts).

   Corrections for background, detector dead time etc.,
   should not have been made to these values. Instead use
   _pd_proc_intensity_ for corrected diffractograms.

https://www.iucr.org/__data/iucr/cifdic_html/1/cif_pd.dic/Ipd_proc_intensity_.html
_pd_proc_intensity_total
   This contains intensity values for the
   processed diffractogram for each data point where
   background, normalization and other corrections have not
   been applied.
   Inclusion of s.u. values for these values is strongly recommended.

https://www.iucr.org/__data/iucr/cifdic_html/1/cif_pd.dic/Ipd_proc_ls_weight.html
_pd_proc_ls_weight
   Weight applied to each profile point. These values
   may be omitted if the weights are 1/u^2^, where
   u is the s.u. for the _pd_proc_intensity_net values.

   A weight value of zero is used to indicate a data
   point not used for refinement (see
   _pd_proc_info_excluded_regions).

https://www.iucr.org/__data/iucr/cifdic_html/1/cif_pd.dic/Ipd_calc_intensity_.html
_pd_calc_intensity_total
   Intensity values for a computed diffractogram at
   each angle setting. Values should be computed at the
   same locations as the processed diffractogram, and thus
   the numbers of points will be defined by
   _pd_proc_number_of_points and point positions may
   be defined using _pd_proc_2theta_range_ or
   _pd_proc_2theta_corrected.

   Use _pd_calc_intensity_net if the computed diffractogram
   does not contain background or normalization corrections
   and thus is specified on the same scale as the
   _pd_proc_intensity_net values.

   Use _pd_calc_intensity_total if the computed diffraction
   pattern includes background or normalization corrections
   (or both) and thus is specified on the same scale as the
   observed intensities (_pd_meas_counts_ or _pd_meas_intensity_).

   If an observed pattern is included, _pd_calc_intensity_
   should be looped with either _pd_proc_intensity_net,
   _pd_meas_counts_ or _pd_meas_intensity_.

https://www.iucr.org/__data/iucr/cifdic_html/1/cif_pd.dic/Ipd_proc_intensity_.html
_pd_proc_intensity_bkg_calc
   This is intended to contain the
   background intensity for every data point where the
   background function has been fitted or estimated

*/
	Out_CIF_newfile(ciffile)
	Out_String("\nloop_")
	Out_String("\n\t_pd_meas_time_of_flight")
	Out_String("\n\t_pd_proc_d_spacing")
	#if type == "meas";
		Out_String("\n\t_pd_meas_intensity_total")
	#else
		Out_String("\n\t_pd_proc_intensity_total")
	#endif
	Out_String("\n\t_pd_proc_ls_weight")
	Out_String("\n\t_pd_calc_intensity_total")
	#m_ifarg bkg_eqn ""
		xdd_out ciffile append
			load out_record out_fmt out_eqn {
				 "\n%11.6f" = X;
				 "\t%11.6f" = d_spacing_from_TOF(CIF_t0, CIF_t1, CIF_t2);
				 "\t%11.6f" = Yobs;
				 "\t%11.6f" = Get(weighting);
				 "\t%11.6f" = Ycalc;
			}
	#m_else
		Out_String("\n\t_pd_proc_intensity_bkg_calc")
		xdd_out ciffile append
			load out_record out_fmt out_eqn {
				 "\n%11.6f" = X;
				 "\t%11.6f" = d_spacing_from_TOF(t0, t1, t2);
				 "\t%11.6f" = Yobs;
				 "\t%11.6f" = Get(weighting);
				 "\t%11.6f" = Ycalc;
				 "\t%11.6f" bkg_eqn
			}
	#m_endif
}


macro Out_pdCIF_energy_dispersive_measured_data {
	Out_pdCIF_energy_dispersive_data(meas, =Get(bkg);)
}
macro Out_pdCIF_energy_dispersive_processed_data {
	Out_pdCIF_energy_dispersive_data(proc, =Get(bkg);)
}
macro Out_pdCIF_energy_dispersive_data(ciffile, type, bkg_eqn) {
/*
https://www.iucr.org/__data/iucr/cifdic_html/1/cif_pd.dic/Ipd_proc_energy_.html
_pd_proc_energy_incident
   Incident energy in electronvolts of the source computed
   from secondary calibration information (time-of-flight
   and synchrotron data).

   Detection energy in electronvolts selected by the analyser,
   if not the same as the incident energy (triple-axis or
   energy-dispersive data). This may be a single value or may
   vary for each data point (triple-axis and time-of-flight data).

https://www.iucr.org/__data/iucr/cifdic_html/1/cif_pd.dic/Ipd_proc_d_spacing.html
_pd_proc_d_spacing
   d-spacing corresponding to an intensity point
   from Braggs law, d = \l/(2 sin\q), in units of angstroms.

https://www.iucr.org/__data/iucr/cifdic_html/1/cif_pd.dic/Ipd_meas_intensity_.html
_pd_meas_intensity_total
   Intensity measurements at the measurement point (see
   the definition of _pd_meas_2theta_).

   Use this entry for measurements where intensity
   values are not counts (use _pd_meas_counts_ for event-counting
   measurements where the standard uncertainty is
   estimated as the square root of the number of counts).

   Corrections for background, detector dead time etc.,
   should not have been made to these values. Instead use
   _pd_proc_intensity_ for corrected diffractograms.

https://www.iucr.org/__data/iucr/cifdic_html/1/cif_pd.dic/Ipd_proc_intensity_.html
_pd_proc_intensity_total
   This contains intensity values for the
   processed diffractogram for each data point where
   background, normalization and other corrections have not
   been applied.
   Inclusion of s.u. values for these values is strongly recommended.

https://www.iucr.org/__data/iucr/cifdic_html/1/cif_pd.dic/Ipd_proc_ls_weight.html
_pd_proc_ls_weight
   Weight applied to each profile point. These values
   may be omitted if the weights are 1/u^2^, where
   u is the s.u. for the _pd_proc_intensity_net values.

   A weight value of zero is used to indicate a data
   point not used for refinement (see
   _pd_proc_info_excluded_regions).

https://www.iucr.org/__data/iucr/cifdic_html/1/cif_pd.dic/Ipd_calc_intensity_.html
_pd_calc_intensity_total
   Intensity values for a computed diffractogram at
   each angle setting. Values should be computed at the
   same locations as the processed diffractogram, and thus
   the numbers of points will be defined by
   _pd_proc_number_of_points and point positions may
   be defined using _pd_proc_2theta_range_ or
   _pd_proc_2theta_corrected.

   Use _pd_calc_intensity_net if the computed diffractogram
   does not contain background or normalization corrections
   and thus is specified on the same scale as the
   _pd_proc_intensity_net values.

   Use _pd_calc_intensity_total if the computed diffraction
   pattern includes background or normalization corrections
   (or both) and thus is specified on the same scale as the
   observed intensities (_pd_meas_counts_ or _pd_meas_intensity_).

   If an observed pattern is included, _pd_calc_intensity_
   should be looped with either _pd_proc_intensity_net,
   _pd_meas_counts_ or _pd_meas_intensity_.

https://www.iucr.org/__data/iucr/cifdic_html/1/cif_pd.dic/Ipd_proc_intensity_.html
_pd_proc_intensity_bkg_calc
   This is intended to contain the
   background intensity for every data point where the
   background function has been fitted or estimated

*/
	Out_CIF_newfile(ciffile)
	Out_String("\nloop_")
	Out_String("\n\t_pd_proc_energy_incident")
	Out_String("\n\t_pd_proc_d_spacing")
	#if type == "meas";
		Out_String("\n\t_pd_meas_intensity_total")
	#else
		Out_String("\n\t_pd_proc_intensity_total")
	#endif
	Out_String("\n\t_pd_proc_ls_weight")
	Out_String("\n\t_pd_calc_intensity_total")
	#m_ifarg bkg_eqn ""
	xdd_out ciffile append
		load out_record out_fmt out_eqn {
			 "\n%11.6f" = X;
			 "\t%11.6f" = d_spacing_from_EDXRD(CIF_TH2_FIXED);
			 "\t%11.6f" = Yobs;
			 "\t%11.6f" = Get(weighting);
			 "\t%11.6f" = Ycalc;
		}
	#m_else
	Out_String("\n\t_pd_proc_intensity_bkg_calc")
	xdd_out ciffile append
		load out_record out_fmt out_eqn {
			 "\n%11.6f" = X;
			 "\t%11.6f" = d_spacing_from_EDXRD(CIF_TH2_FIXED);
			 "\t%11.6f" = Yobs;
			 "\t%11.6f" = Get(weighting);
			 "\t%11.6f" = Ycalc;
			 "\t%11.6f" bkg_eqn
		}
	#m_endif
}

macro Out_pdCIF_hkls_header(ciffile) {
/*
https://www.iucr.org/__data/iucr/cifdic_html/1/cif_core.dic/Irefln_index_.html
_refln_index_h
_refln_index_k
_refln_index_l
   Miller indices of the reflection. The values of the Miller
   indices in the REFLN category must correspond to the cell
   defined by the cell lengths and cell angles in the CELL category.

https://www.iucr.org/__data/iucr/cifdic_html/1/cif_core.dic/Irefln_d_spacing.html
_refln_d_spacing
   The d spacing in angstroms for this reflection. This is related
   to the (sin theta)/lambda value by the expression
        _refln_d_spacing = 2/(_refln_sint/lambda)

https://www.iucr.org/__data/iucr/cifdic_html/1/cif_core.dic/Irefln_F_squared_.html
_refln_F_squared_calc
_refln_F_squared_meas
   Calculated, measured and estimated standard uncertainty (derived
   from measurement) of the squared structure factors (in electrons
   squared for X-ray diffraction).
*/
	Out_CIF_newfile(ciffile)
	Out_String("\nloop_")
	Out_String("\n\t_refln_index_h")
	Out_String("\n\t_refln_index_k")
	Out_String("\n\t_refln_index_l")
	Out_String("\n\t_pd_refln_phase_id")
	Out_String("\n\t_refln_d_spacing")
	Out_String("\n\t_refln_F_squared_calc")
	Out_String("\n\t_refln_F_squared_meas")
}
macro Out_pdCIF_hkls(ciffile, phase_id) {
/*
https://www.iucr.org/__data/iucr/cifdic_html/1/cif_core.dic/Irefln_index_.html
_refln_index_h
_refln_index_k
_refln_index_l
   Miller indices of the reflection. The values of the Miller
   indices in the REFLN category must correspond to the cell
   defined by the cell lengths and cell angles in the CELL category.

https://www.iucr.org/__data/iucr/cifdic_html/1/cif_core.dic/Irefln_d_spacing.html
_refln_d_spacing
   The d spacing in angstroms for this reflection. This is related
   to the (sin theta)/lambda value by the expression
        _refln_d_spacing = 2/(_refln_sint/lambda)

https://www.iucr.org/__data/iucr/cifdic_html/1/cif_core.dic/Irefln_F_squared_.html
_refln_F_squared_calc
_refln_F_squared_meas
   Calculated, measured and estimated standard uncertainty (derived
   from measurement) of the squared structure factors (in electrons
   squared for X-ray diffraction).
*/
	for strs {
		Out_CIF_newfile(ciffile)
			phase_out ciffile append
					load out_record out_fmt out_eqn {
						"\n%4.0f" = H;
						"\t%4.0f" = K;
						"\t%4.0f" = L;
						"\t%V"    = phase_id;
						"\t%11.6f" = D_spacing;
						"\t%12.6f" = I_no_scale_pks;
						"\t%12.6f" = Iobs_no_scale_pks;
					}
	}
}


'############################################################## '
' Macros for crystal structures                                 '
'############################################################## '


macro Out_pdCIF_diffractogramid(diffractogramidbase, id) {
/*
https://www.iucr.org/__data/iucr/cifdic_html/1/cif_pd.dic/Ipd_block_diffractogram_id.html
_pd_block_diffractogram_id
   A block ID code (see _pd_block_id) that identifies
   diffraction data contained in a data block other
   than the current block. This will occur most frequently
   when more than one set of diffraction data
   is used for a structure determination. The data
   block containing the diffraction data will contain
   a _pd_block_id code matching the code in
   _pd_block_diffractogram_id.
*/
	Out_pdCIF_diffractogramid_dataname
	Out(diffractogramidbase, "%s")
	Out(id, "_%V")
}
macro Out_pdCIF_diffractogramid_dataname {
	Out_String("\n_pd_block_diffractogram_id\t")
}
macro Out_pdCIF_phase_name {
/*
https://www.iucr.org/__data/iucr/cifdic_html/1/cif_pd.dic/Ipd_phase_name.html
_pd_phase_name
    The name of the crystal phase.
*/
	Out(Get(phase_name), "\n_pd_phase_name\n;%s\n;")
}

macro Out_CIF_unit_cell_prms {
/*
https://www.iucr.org/__data/iucr/cifdic_html/1/cif_core.dic/Icell_length_.html
_cell_length_a
_cell_length_b
_cell_length_c
   Unit-cell lengths in angstroms corresponding to the structure
   reported. The values of _refln_index_h, *_k, *_l must
   correspond to the cell defined by these values and _cell_angle_
   values.

https://www.iucr.org/__data/iucr/cifdic_html/1/cif_core.dic/Icell_angle_.html
_cell_angle_alpha
_cell_angle_beta
_cell_angle_gamma
   Unit-cell angles of the reported structure in degrees.
   The values of _refln_index_h, *_k, *_l must correspond to the
   cell defined by these values and _cell_length_a, *_b and *_c.

https://www.iucr.org/__data/iucr/cifdic_html/1/cif_core.dic/Icell_volume.html
_cell_volume
   Cell volume V in angstroms cubed
*/
	Out(Get(a),           "\n_cell_length_a    %V")
	Out(Get(b),           "\n_cell_length_b    %V")
	Out(Get(c),           "\n_cell_length_c    %V")
	Out(Get(al),          "\n_cell_angle_alpha %V")
	Out(Get(be),          "\n_cell_angle_beta  %V")
	Out(Get(ga),          "\n_cell_angle_gamma %V")
	Out(Get(cell_volume), "\n_cell_volume      %V")
}

macro Out_CIF_Z_molecular_weight(Z) {
/*
https://www.iucr.org/__data/iucr/cifdic_html/1/cif_core.dic/Icell_formula_units_Z.html
_cell_formula_units_Z
   The number of the formula units in the unit cell as specified
   by _chemical_formula_structural, _chemical_formula_moiety or
   _chemical_formula_sum.

https://www.iucr.org/__data/iucr/cifdic_html/1/cif_core.dic/Ichemical_formula_weight.html
_chemical_formula_weight
   Formula mass in daltons. This mass should correspond to the
   formulae given under _chemical_formula_structural, *_iupac,
   *_moiety or *_sum and, together with the Z value and cell
   parameters, should yield the density given as
   _exptl_crystal_density_diffrn.
*/
	local #m_unique !formula_weight_for_CIF_output = Get(cell_mass) / Z;
	Out(Z, "\n_cell_formula_units_Z\t%.0f")
	Out(formula_weight_for_CIF_output, "\n_chemical_formula_weight\t%V")
}

macro Out_CIF_chemical_formula(formula) {
/*
https://www.iucr.org/__data/iucr/cifdic_html/1/cif_core.dic/Ichemical_formula_sum.html
_chemical_formula_sum
   See the _chemical_formula_[] category description for the rules
   for writing chemical formulae in which all discrete bonded
   residues and ions are summed over the constituent elements,
   following the ordering given in general rule (5) in the
   _chemical_formula_[] category description. Parentheses are not
   normally used.

   example
   'C18 H19 N7 O8 S'

   This will need manual editing, as TOPAS cannot output quotation marks.
*/
	Out(formula, "\n_chemical_formula_sum\t%s")
}

macro Out_CIF_diffrn_measurement_device_type(goniotype) {
/*
https://www.iucr.org/__data/iucr/cifdic_html/1/cif_core.dic/Idiffrn_measurement_device_type.html_cell_formula_units_Z
_diffrn_measurement_device_type
   The make, model or name of the measurement device
   (goniometer) used.
*/
	Out(goniotype, "\n_diffrn_measurement_device_type\t%s")
}

macro Out_CIF_space_group_crystal_system(system) {
/*
https://www.iucr.org/__data/iucr/cifdic_html/1/cif_core.dic/Ispace_group_crystal_system.html
_space_group_crystal_system
   The name of the system of geometric crystal classes of space
   groups (crystal system) to which the space group belongs.
   Note that rhombohedral space groups belong to the
   trigonal system.

triclinic
monoclinic
orthorhombic
tetragonal
trigonal
hexagonal
cubic
*/
	Out(system, "\n_space_group_crystal_system\t%s")
}

macro Out_CIF_minmax_theta {
/*
https://www.iucr.org/__data/iucr/cifdic_html/1/cif_core.dic/Icell_measurement_theta_.html
_cell_measurement_theta_min
_cell_measurement_theta_max
   The maximum and minimum theta angles of reflections
   used to measure the unit cell in degrees.
*/
	Out((X1/2), "\n_cell_measurement_theta_min\t%V")
	Out((X2/2), "\n_cell_measurement_theta_max\t%V")
}

macro Out_CIF_density {
/*
https://www.iucr.org/__data/iucr/cifdic_html/1/cif_core.dic/Iexptl_crystal_density_diffrn.html
_exptl_crystal_density_diffrn
   Density values calculated from the crystal cell and contents. The
   units are megagrams per cubic metre (grams per cubic centimetre).
*/
	local #m_unique !density_only_for_CIF_output = (1.6605402 Get(cell_mass)) / Get(cell_volume);
	Out(density_only_for_CIF_output, "\n_exptl_crystal_density_diffrn\t%V")
}

macro Out_CIF_absorption {
/*
https://www.iucr.org/__data/iucr/cifdic_html/1/cif_core.dic/Iexptl_absorpt_coefficient_mu.html
_exptl_absorpt_coefficient_mu
   The absorption coefficient mu in reciprocal millimetres
   calculated from the atomic content of the cell, the density and
   the radiation wavelength.
*/
	local #m_unique !density_for_CIF_output = ((1.6605402 Get(cell_mass)) / Get(cell_volume));
	local #m_unique !LAC_for_CIF_output = Get(phase_MAC) density_for_CIF_output / 10;
	Out(LAC_for_CIF_output, "\n_exptl_absorpt_coefficient_mu\t%V")
}


macro Out_CIF_cell_temperature(temp) {
/*
https://www.iucr.org/__data/iucr/cifdic_html/1/cif_core.dic/Icell_measurement_temperature.html
_cell_measurement_temperature\
   The temperature in kelvins at which the unit-cell parameters
   were measured (not the temperature of synthesis).
*/
	Out(temp, "\n_cell_measurement_temperature\t%V")
	Out_CIF_temperature(temp)
}
macro Out_CIF_cell_pressure(pres) {
/*
https://www.iucr.org/__data/iucr/cifdic_html/1/cif_core.dic/Icell_measurement_pressure.html
_cell_measurement_pressure
   The pressure in kilopascals at which the unit-cell parameters
   were measured (not the pressure at which the sample was
   synthesized).
*/
	Out(pres, "\n_cell_measurement_pressure\t%V")
	Out_CIF_pressure(pres)
}

macro Out_CIF_space_group_with_id {
/*
https://www.iucr.org/__data/iucr/cifdic_html/1/cif_core.dic/Ispace_group_name_H-M_alt.html
_space_group_name_H-M_alt
   _space_group_name_H-M_alt allows any Hermann-Mauguin symbol
   to be given. The way in which this item is used is determined
   by the user and in general is not intended to be interpreted by
   computer. It may, for example, be used to give one of the
   extended Hermann-Mauguin symbols given in Table 4.3.2.1 of
   International Tables for Crystallography Vol. A (2002) or
   a Hermann-Mauguin symbol for a conventional or unconventional
   setting.

   Each component of the space-group name is separated by a
   space or an underscore. Subscripts should appear without special
   symbols. Bars should be given as negative signs before the
   numbers to which they apply.

https://www.iucr.org/__data/iucr/cifdic_html/1/cif_core.dic/Ispace_group_symop_id.html
_space_group_symop_id
   An arbitrary identifier that uniquely labels each symmetry
   operation in the list.

https://www.iucr.org/__data/iucr/cifdic_html/1/cif_core.dic/Ispace_group_symop_operation_xyz.html
_space_group_symop_operation_xyz
   A parsable string giving one of the symmetry operations of the
   space group in algebraic form.

*/
	Out(Get(sp_grp_char), "\n_space_group_name_H-M_alt\n;%s\n;")
	Out_String("\nloop_\n\t_space_group_symop_id\n\t_space_group_symop_operation_xyz")
	Out(Get(sp_xyzs_txt_with_id), "%s")
}
macro Out_CIF_space_group_without_id {
/*
https://www.iucr.org/__data/iucr/cifdic_html/1/cif_core.dic/Ispace_group_name_H-M_alt.html
_space_group_name_H-M_alt
   _space_group_name_H-M_alt allows any Hermann-Mauguin symbol
   to be given. The way in which this item is used is determined
   by the user and in general is not intended to be interpreted by
   computer. It may, for example, be used to give one of the
   extended Hermann-Mauguin symbols given in Table 4.3.2.1 of
   International Tables for Crystallography Vol. A (2002) or
   a Hermann-Mauguin symbol for a conventional or unconventional
   setting.

   Each component of the space-group name is separated by a
   space or an underscore. Subscripts should appear without special
   symbols. Bars should be given as negative signs before the
   numbers to which they apply.

https://www.iucr.org/__data/iucr/cifdic_html/1/cif_core.dic/Ispace_group_symop_operation_xyz.html
_space_group_symop_operation_xyz
   A parsable string giving one of the symmetry operations of the
   space group in algebraic form.

*/
	Out(Get(sp_grp_char), "\n_space_group_name_H-M_alt\n;%s\n;")
	Out_String("\nloop_\n\t_space_group_symop_operation_xyz")
	Out(Get(sp_xyzs_txt), "%s")
}

macro Out_CIF_atom_coords(ciffile) {
/*
https://www.iucr.org/__data/iucr/cifdic_html/1/cif_core.dic/Iatom_site_label.html
_atom_site_label
   The _atom_site_label is a unique identifier for a particular site
   in the crystal. This code is made up of a sequence of up to seven
   components, _atom_site_label_component_0 to *_6, which may be
   specified as separate data items. Component 0 usually matches one
   of the specified _atom_type_symbol codes. This is not mandatory
   if an _atom_site_type_symbol item is included in the atom-site
   list. The _atom_site_type_symbol always takes precedence over
   an _atom_site_label in the identification of the atom type.

https://www.iucr.org/__data/iucr/cifdic_html/1/cif_core.dic/Iatom_site_type_symbol.html
_atom_site_type_symbol
   A code to identify the atom species (singular or plural)
   occupying this site.

https://www.iucr.org/__data/iucr/cifdic_html/1/cif_core.dic/Iatom_site_site_symmetry_multiplicity.html
_atom_site_site_symmetry_multiplicity
   The number of different sites that are generated by the
   application of the space-group symmetry to the
   coordinates given for this site. It is equal to the
   multiplicity given for this Wyckoff site
   in International Tables for Crystallography Vol. A (2002).

https://www.iucr.org/__data/iucr/cifdic_html/1/cif_core.dic/Iatom_site_fract_.html
_atom_site_fract_x
_atom_site_fract_y
_atom_site_fract_z
   Atom-site coordinates as fractions of the _cell_length_ values.

https://www.iucr.org/__data/iucr/cifdic_html/1/cif_core.dic/Iatom_site_occupancy.html
_atom_site_occupancy
   The fraction of the atom type present at this site.
   The sum of the occupancies of all the atom types at this site
   may not significantly exceed 1.0 unless it is a dummy site.

https://www.iucr.org/__data/iucr/cifdic_html/1/cif_core.dic/Iatom_site_B_iso_or_equiv.html
_atom_site_B_iso_or_equiv
   Isotropic atomic displacement parameter, or equivalent isotropic
   atomic displacement parameter, B(equiv), in angstroms squared,
   calculated from anisotropic displacement components.

   B(equiv) = (1/3) sum~i~[sum~j~(B^ij^ a*~i~ a*~j~ a~i~ a~j~)]

   a     = the real-space cell lengths
   a*    = the reciprocal-space cell lengths
   B^ij^ = 8 pi^2^ U^ij^

   Ref: Fischer, R. X. & Tillmanns, E. (1988). Acta Cryst. C44,
        775-776.
*/
	Out_CIF_newfile(ciffile)
	Out_String("\nloop_")
	Out_String("\n\t_atom_site_label")
	Out_String("\n\t_atom_site_type_symbol")
	Out_String("\n\t_atom_site_site_symmetry_multiplicity")
	Out_String("\n\t_atom_site_fract_x")
	Out_String("\n\t_atom_site_fract_y")
	Out_String("\n\t_atom_site_fract_z")
	Out_String("\n\t_atom_site_occupancy")
	Out_String("\n\t_atom_site_B_iso_or_equiv")
	atom_out ciffile append
		load out_record out_fmt out_eqn {
			"\n%s" = Get_From_String(Get(current_atom), site);
			"\t%s" = Get_From_String(Get(current_atom), atom);
			"\t%3.0f" = Get_From_String(Get(current_atom), num_posns);
			"\t%V" = Get_From_String(Get(current_atom), x);
			"\t%V" = Get_From_String(Get(current_atom), y);
			"\t%V" = Get_From_String(Get(current_atom), z);
			"\t%V" = Get_From_String(Get(current_atom), occ);
			"\t%V" = Get_From_String(Get(current_atom), beq);
		}
}

macro Out_CIF_hkls(ciffile) {
/*
https://www.iucr.org/__data/iucr/cifdic_html/1/cif_core.dic/Irefln_index_.html
_refln_index_h
_refln_index_k
_refln_index_l
   Miller indices of the reflection. The values of the Miller
   indices in the REFLN category must correspond to the cell
   defined by the cell lengths and cell angles in the CELL category.

https://www.iucr.org/__data/iucr/cifdic_html/1/cif_core.dic/Irefln_d_spacing.html
_refln_d_spacing
   The d spacing in angstroms for this reflection. This is related
   to the (sin theta)/lambda value by the expression
        _refln_d_spacing = 2/(_refln_sint/lambda)

https://www.iucr.org/__data/iucr/cifdic_html/1/cif_core.dic/Irefln_F_squared_.html
_refln_F_squared_calc
_refln_F_squared_meas
   Calculated, measured and estimated standard uncertainty (derived
   from measurement) of the squared structure factors (in electrons
   squared for X-ray diffraction).
*/
	Out_CIF_newfile(ciffile)
	Out_String("\nloop_")
	Out_String("\n\t_refln_index_h")
	Out_String("\n\t_refln_index_k")
	Out_String("\n\t_refln_index_l")
	Out_String("\n\t_refln_d_spacing")
	Out_String("\n\t_refln_F_squared_calc")
	Out_String("\n\t_refln_F_squared_meas")
	phase_out ciffile append
		load out_record out_fmt out_eqn {
			"\n%4.0f" = H;
			"\t%4.0f" = K;
			"\t%4.0f" = L;
			"\t%11.6f" = D_spacing;
			"\t%12.6f" = I_no_scale_pks;
			"\t%12.6f" = Iobs_no_scale_pks;
		}
}

macro Out_CIF_adps(ciffile) {
/*
https://www.iucr.org/__data/iucr/cifdic_html/1/cif_core.dic/Iatom_site_aniso_label.html
_atom_site_aniso_label
   Anisotropic atomic displacement parameters are usually looped in
   a separate list. If this is the case, this code must match the
   _atom_site_label of the associated atom in the atom coordinate
   list and conform with the same rules described in
   _atom_site_label.

https://www.iucr.org/__data/iucr/cifdic_html/1/cif_core.dic/Iatom_site_aniso_U_.html
_atom_site_aniso_U_11
_atom_site_aniso_U_22
_atom_site_aniso_U_33
_atom_site_aniso_U_12
_atom_site_aniso_U_13
_atom_site_aniso_U_23
   These are the standard anisotropic atomic displacement
   components in angstroms squared which appear in the
   structure-factor term

   T = exp{-2pi^2^ sum~i~ [sum~j~ (U^ij^ h~i~ h~j~ a*~i~ a*~j~) ] }

   h = the Miller indices
   a* = the reciprocal-space cell lengths

   The unique elements of the real symmetric matrix are
   entered by row.
*/
	Out_CIF_newfile(ciffile)
	Out_String("\nloop_")
	Out_String("\n\t_atom_site_aniso_label")
	Out_String("\n\t_atom_site_aniso_U_11")
	Out_String("\n\t_atom_site_aniso_U_22")
	Out_String("\n\t_atom_site_aniso_U_33")
	Out_String("\n\t_atom_site_aniso_U_12")
	Out_String("\n\t_atom_site_aniso_U_13")
	Out_String("\n\t_atom_site_aniso_U_23")
	atom_out ciffile append
		load out_record out_fmt out_eqn {
			"\n%s" = Get_From_String(Get(current_atom), site);
			"\t%V" = Get_From_String(Get(current_atom), u11);
			"\t%V" = Get_From_String(Get(current_atom), u22);
			"\t%V" = Get_From_String(Get(current_atom), u33);
			"\t%V" = Get_From_String(Get(current_atom), u12);
			"\t%V" = Get_From_String(Get(current_atom), u13);
			"\t%V" = Get_From_String(Get(current_atom), u23);
		 }
}

macro Out_CIF_bond_angles(ciffile) {
/*
https://www.iucr.org/__data/iucr/cifdic_html/1/cif_core.dic/Igeom_bond_atom_site_label_.html
_geom_bond_atom_site_label_1
_geom_bond_atom_site_label_2
   The labels of two atom sites that form a bond. These must match
   labels specified as _atom_site_label in the atom list.

https://www.iucr.org/__data/iucr/cifdic_html/1/cif_core.dic/Igeom_bond_distance.html
_geom_bond_distance
   The intramolecular bond distance in angstroms.

https://www.iucr.org/__data/iucr/cifdic_html/1/cif_core.dic/Igeom_bond_site_symmetry_.html
_geom_bond_site_symmetry_1
_geom_bond_site_symmetry_2
   The symmetry code of each atom site as the symmetry-equivalent
   position number 'n' and the cell translation number 'klm'.
   These numbers are combined to form the code 'n klm' or n_klm.
   The character string n_klm is composed as follows:

   n refers to the symmetry operation that is applied to the
   coordinates stored in _atom_site_fract_x, _atom_site_fract_y
   and _atom_site_fract_z. It must match a number given in
   _space_group_symop_id.

   k, l and m refer to the translations that are subsequently
   applied to the symmetry-transformed coordinates to generate
   the atom used in calculating the bond. These translations
   (x,y,z) are related to (k,l,m) by the relations
        k = 5 + x
        l = 5 + y
        m = 5 + z
   By adding 5 to the translations, the use of negative numbers
   is avoided.

https://www.iucr.org/__data/iucr/cifdic_html/1/cif_core.dic/Igeom_angle_atom_site_label_.html
_geom_angle_atom_site_label_1
_geom_angle_atom_site_label_2
_geom_angle_atom_site_label_3
   The labels of the three atom sites which define the angle
   given by _geom_angle. These must match labels specified as
   _atom_site_label in the atom list. Label 2 identifies the site at
   the apex of the angle.

https://www.iucr.org/__data/iucr/cifdic_html/1/cif_core.dic/Igeom_angle.html
_geom_angle
   Angle in degrees defined by the three sites
   _geom_angle_atom_site_label_1, *_2 and *_3. The site at *_2
   is at the apex of the angle.

https://www.iucr.org/__data/iucr/cifdic_html/1/cif_core.dic/Igeom_angle_site_symmetry_.html
_geom_angle_site_symmetry_1
_geom_angle_site_symmetry_2
_geom_angle_site_symmetry_3
   The symmetry code of each atom site as the symmetry-equivalent
   position number 'n' and the cell translation number 'klm'.
   These numbers are combined to form the code 'n klm' or n_klm.
   The character string n_klm is composed as follows:

   n refers to the symmetry operation that is applied to the
   coordinates stored in _atom_site_fract_x, _atom_site_fract_y
   and _atom_site_fract_z. It must match a number given in
   _space_group_symop_id.

   k, l and m refer to the translations that are subsequently
   applied to the symmetry-transformed coordinates to generate
   the atom used in calculating the angle. These translations
   (x,y,z) are related to (k,l,m) by the relations
        k = 5 + x
        l = 5 + y
        m = 5 + z
   By adding 5 to the translations, the use of negative numbers
   is avoided.
*/
	Out_CIF_newfile(ciffile)
	consider_lattice_parameters 'this propagates errors from lattice parameters to the bonds and angles'
	Out(Get(cif_bonds_angles), "%s")
}

macro Out_magCIF_space_group_with_id {
/*
https://www.iucr.org/__data/iucr/cifdic_html/3/MAGNETIC_CIF/Ispace_group_magn.number_BNS.html
_space_group_magn.number_BNS
     See _space_group_magn.number_OG for a description of magnetic
     space groups (MSGs). The Belov-Neronova-Smirnova (BNS) number for
     an MSG is composed of two positive integers separated by a
     period. The first integer lies in the range [1-230] and indicates
     the non-magnetic space group F for MSGs of types 1-3 or the
     non-magnetic space group of the subgroup D for MSGs of type 4.  The
     second integer is sequential over all MSGs associated  with the
     same crystal family.
     There are 1651 distinct equivalence classes of MSGs, each of
     which has a unique BNS number. These equivalence classes are most
     accurately referred to as magnetic space-group "types",
     following the usage in the International Tables for Crystallography.
     But the word "type"  is also commonly used to
     indicate the four-fold classification of MSGs presented above.
     To avoid confusion, the word "type" is only used in the latter
     sense here.

     Analogous tags: symCIF:_space_group.number_IT

     Ref: 'Magnetic Group Tables' by D.B. Litvin at
     http://www.iucr.org/publ/978-0-9553602-2-0. ISO-MAG tables of H.T.
     Stokes and B.J. Campbell at http://iso.byu.edu.

https://www.iucr.org/__data/iucr/cifdic_html/3/MAGNETIC_CIF/Ispace_group_symop_magn_operation.id.html
_space_group_symop_magn_operation.id
     An arbitrary identifier that uniquely labels each symmetry
     operation in a looped list of magnetic space-group symmetry
     operations. Most commonly, a sequence of positive  integers is
     used for this identification.
     The _space_group_symop_magn.id alias provides backwards
     compatibility with the established magCIF prototype.

https://www.iucr.org/__data/iucr/cifdic_html/3/MAGNETIC_CIF/Ispace_group_symop_magn_operation.xyz.html
_space_group_symop_magn_operation.xyz
     A parsable string giving one of the symmetry operations of the
     magnetic space group in algebraic form.  The analogy between
     parsable labels for magnetic and non-magnetic symmetry operations
     is perfect except for the fact that a magnetic symop label ends
     with an additional piece of information ("-1" or "+1") indicating
     that the operation is or is not time-reversed, respectively.
     This tag is intended for use with the BNS-supercell description
     of a magnetic structure.

     Analogous tags: symCIF:_space_group_symop.operation_xyz

     Ref: 'Magnetic Group Tables' by D.B. Litvin at
     http://www.iucr.org/publ/978-0-9553602-2-0. ISO-MAG tables of H.T.
     Stokes and B.J. Campbell at http://iso.byu.edu.

_space_group_symop.magn_operation.mxmymz
I cannot find a definition in the magCIF for this column.

_space_group_symop.magn_operation.timereversal
Topas does not include the time reversal in the xyz output.
It goes in its own column.

*/
	Out(Get(sp_grp_char ), "\n_space_group_magn.number_BNS\t%s")
	Out_String("\nloop_")
	Out_String("\n\t_space_group_symop_magn_operation.id")
	Out_String("\n\t_space_group_symop_magn_operation.xyz")
	Out_String("\n\t_space_group_symop_magn_operation.mxmymz")
	Out_String("\n\t_space_group_symop_magn_operation.timereversal")
	Out(Get(mag_sp_xyzs_txt_with_id),  "%s")
}

macro Out_mag_CIF_atom_site_moment {
/*
https://www.iucr.org/__data/iucr/cifdic_html/3/MAGNETIC_CIF/Iatom_site_moment.label.html
_atom_site_moment.label

https://www.iucr.org/__data/iucr/cifdic_html/3/MAGNETIC_CIF/Iatom_site_moment.crystalaxis_x.html
_atom_site_moment.crystalaxis_x
     The component of the atom-site magnetic-moment vector parallel to the first
     unit-cell axis.  See _atom_site_moment.crystalaxis.

https://www.iucr.org/__data/iucr/cifdic_html/3/MAGNETIC_CIF/Iatom_site_moment.crystalaxis_y.html
_atom_site_moment.crystalaxis_y
     The component of the atom-site magnetic-moment vector parallel to the second
     unit-cell axis.  See _atom_site_moment.crystalaxis.

https://www.iucr.org/__data/iucr/cifdic_html/3/MAGNETIC_CIF/Iatom_site_moment.crystalaxis_z.html
_atom_site_moment.crystalaxis_z
     The component of the atom-site magnetic-moment vector parallel to the third
     unit-cell axis.  See _atom_site_moment.crystalaxis.
*/
	Out_CIF_newfile(ciffile)
	Out_String("\nloop_")
	Out_String("\n\t_atom_site_moment.label")
	Out_String("\n\t_atom_site_moment.crystalaxis_x")
	Out_String("\n\t_atom_site_moment.crystalaxis_y")
	Out_String("\n\t_atom_site_moment.crystalaxis_z")
	mag_atom_out ciffile append
		load out_record out_fmt out_eqn {
			"\n%s" = Get_From_String(Get(current_atom), site);
			"\t%11.5f" = Get(a) Get_From_String(Get(current_atom), mlx);
			"\t%11.5f" = Get(b) Get_From_String(Get(current_atom), mly);
			"\t%11.5f" = Get(c) Get_From_String(Get(current_atom), mlz);
		}
}

'##############################################################%####### '
' These are the consoldiated macros to report structures and patterns   '
'###################################################################### '


macro Out_pdCIF_xdd_setup {
/*
This macro sets up a workaround in how pk_xo behaves differently between v5-6 and v7
It also defines an ID prm, so you do not need to if there is only one xdd to worry about.
*/
	if Or(Obj_There(pk_xo_prm),Obj_There(pk_xo)) { local !pk_xo_exists 0 }
	if Prm_There(CIF_ID) {
		'do nothing'
	} else {
		if Prm_There(CIF_MULTI_DIFFRACTOGRAM_ID) {
			if Obj_There(num_runs) {
				local CIF_ID = Run_Number;
			} else {
				local CIF_ID 1
			}
		} else { 'not a multi-pattern inp file'
			if Obj_There(range) {
				if Obj_There(num_runs) {
					local CIF_ID = 10000 Get(range) + Run_Number;
				} else {
					local CIF_ID = Get(range);
				}
			} else if Obj_There(num_runs) {
				local CIF_ID = Run_Number;
			} else {
				local CIF_ID 1
			}
		}
	}
}

macro Out_pdCIF_STR(ciffile, phase_id, id) {
	Out_pdCIF_STR(ciffile, phase_id, id,,)
}
macro Out_pdCIF_STR(ciffile, phase_id, id, n, m) {
/*
This macro constructs a crystal structure in CIF format that is likely
to pass checkCIF with minimal issues. Probably.

The construction of the block_id is simply the concatenation of the
phase_name and an identifier, most usually taken as the  number of the xdd,
either defined through the use of "Run_Number" if doing a sequential refinement
using #list, or by setting a local variable in each xdd - local !id = 1; (and
copying it and incrementing it in each xdd)

The diffractogram_id of each diffraction pattern is simply the string "pattern_"
with the id appended. This is also set to be the block id of the diffraction
pattern in the diffraction pattern macro.

The implementation of the block_id and diffractogram_id in is this macro is
extremely simplistic, and designed to be easily automated. If you change how
the _pd_block_id or _pd_diffractogram_id is implemented, make
sure to change it in all the other places - see _pd_phase_block_id also.

This macro can be placed into every str that you have, or better, placed at the end
of the input file in a `for strs {}` construct.


ciffile: the name of the file you want to write to. The data is appended.
phase_id: a number uniquely identifying a str inside an xdd
id: a number uniquely identifying an xdd

If you want to report molecular weight for a str, you must define a
local parameter defining the number of formula units. ie:
local !CIF_Z = 6;
You must name it "CIF_Z".
*/
	Out_CIF_newfile(ciffile)
	Out_String("\n")
	Out_CIF_section_break("Begin powder crystal structure")
	Out_CIF_datablock_dataname Out_unique_phase_id(id)
	Out_pdCIF_blockid_dataname Out_unique_phase_id(id)
	if Prm_There(CIF_MULTI_DIFFRACTOGRAM_ID) {
		Out_String("\n# The diffractogram block id loop is at the end of the datablock.")
	} else {
		Out_pdCIF_diffractogramid_dataname Out_unique_diffractogram_id(id)
	}
	if Prm_There(CIF_DIFFRACTOMETER_NAME) { Out_CIF_diffrn_measurement_device_type(CIF_DIFFRACTOMETER_NAME) }
	Out_pdCIF_phase_name
	Out_CIF_unit_cell_prms
	if Prm_There(CIF_Z) { Out_CIF_Z_molecular_weight(CIF_Z) }
	if Prm_There(CIF_SUM_FORMULA) { Out_CIF_chemical_formula(CIF_SUM_FORMULA) }
	if Prm_There(CIF_TEMP) { Out_CIF_cell_temperature(CIF_TEMP) }
	if Prm_There(CIF_PRES) { Out_CIF_cell_pressure(CIF_PRES) }
	Out_CIF_density
	TOF_ED_CW(,, Out_CIF_absorption Out_CIF_wavelength Out_CIF_minmax_theta)
	if Prm_There(CIF_CRYSTAL_SYSTEM) { Out_CIF_space_group_crystal_system(CIF_CRYSTAL_SYSTEM) }
	if Prm_There(CIF_PHASE_TEXT) { Out_CIF_free_text(CIF_PHASE_TEXT) }
	if Obj_There(mag_sg) {
		Out_magCIF_space_group_with_id
	} else {
		Out_CIF_space_group_with_id
	}
	Out_CIF_atom_coords(ciffile)
	if Obj_There(adps) { Out_CIF_adps(ciffile) }
	if Obj_There(mag_sg) { Out_mag_CIF_atom_site_moment }
	Out_CIF_bond_angles(ciffile)
	Out_CIF_newfile(ciffile)
	if Prm_There(CIF_MULTI_DIFFRACTOGRAM_ID) {
		'this is down here as there are TOPAS internal pointer details that do not allow it up there ^'
		Out_String("\nloop_")
		Out_pdCIF_diffractogramid_dataname
		for xdds n_to_m(n,m) {
			Out_String("\n\t")
			Out_unique_diffractogram_id(id)
		}
		'Cannot have any references to str things after this for xdds loop.'
	}
	Out_CIF_newfile(ciffile)
	Out_CIF_section_break("End powder crystal structure")
	Out_String("\n")
}

macro Out_pdCIF_diffraction_data(ciffile, data_type, bkg_eqn, phase_id, id) {
/*
This macro constructs a powder diffraction pattern in CIF format.

The construction of the block_id is simply the concatenation of the
string "pattern" and an identifier, most usually taken as the  number of the xdd,
either defined through the use of "Run_Number" if doing a sequential refinement
using #list, or by setting a local variable in each xdd - local !id = 1; (and
copying it and incrementing it in each xdd)

The implementation of the block_id in this macro is extremely simplistic, and
designed to be easily automated. If you change how the _pd_block_id or
_pd_diffractogram_id is implemented, make sure to change it in all the other
places - see _pd_phase_block_id also.

This macro can be placed into every xdd that you have, or if you have more, placed
at the end of the input file in a `for xdds {}` construct.

ciffile: the name of the file you want to write to. The data is appended.
data_type: "meas" - data as-measured; "proc" - data has been processed before analysis
bkg_eqn: an equation with the bkg you want to record
phase_id: a number uniquely identifiying a str in an xdd
is: a number uniquely identifying an xdd, or group of xdds in the case of a multi-pattern refinement
*/
	Out_CIF_newfile(ciffile)
	Out_String("\n")
	Out_CIF_section_break("Begin powder diffraction data")
	Out_CIF_datablock_dataname Out_unique_diffractogram_id(id)
	Out_pdCIF_blockid_dataname Out_unique_diffractogram_id(id)
	if Prm_There(CIF_DATETIME) { Out_pdCIF_datetime_initiated(CIF_DATETIME) }
	Out_String("\n_pd_calc_method\tRietveld")
	if Obj_There(neutron) {
		Out_String("\n_diffrn_radiation_probe\tneutron")
	} else {
		Out_String("\n_diffrn_radiation_probe\tx-ray")
	}
	if Prm_There(CIF_DIFFRACTOMETER_NAME) { Out_pdCIF_instr_special_details(CIF_DIFFRACTOMETER_NAME) }
	TOF_ED_CW(Out_pdCIF_scan_method("tof"),
	          Out_pdCIF_scan_method("disp"),
	          if Prm_There(CIF_SCAN_METHOD) { Out_pdCIF_scan_method(CIF_SCAN_METHOD) }
	          if Obj_There(lam) { Out_CIF_wavelength } )
	if Prm_There(CIF_TEMP) { Out_CIF_temperature(CIF_TEMP) }
	if Prm_There(CIF_PRES) { Out_CIF_pressure(CIF_PRES) }
	Out_CIF_Rfactors
	if Prm_There(CIF_DIFFRACTOGRAM_TEXT) { Out_CIF_free_text(CIF_DIFFRACTOGRAM_TEXT) }
	if Obj_There(str) {
		Out_pdCIF_phase_block_id(phase_id, id)
		Out_pdCIF_hkls_header(ciffile)
		Out_pdCIF_hkls(ciffile, phase_id)
	}
	TOF_ED_CW(Out_pdCIF_time_of_flight_data(ciffile, data_type, bkg_eqn),
	          Out_pdCIF_energy_dispersive_data(ciffile, data_type, bkg_eqn),
	          Out_pdCIF_angle_dispersive_data(ciffile, data_type, bkg_eqn))
	Out_CIF_newfile(ciffile)
	Out_CIF_section_break("End powder diffraction data")
	Out_String("\n")
}

macro Out_CIF_magic_number(ciffile) {
'write the CIF version number to file.'
	out ciffile append
	Out_String("#\#CIF_1.1\n")
}
'##############################################################%#####################################     '
'####################################################################################################     '
'######################################################################################################   '
'######################################################################################################   '
'####################################################################################################     '
'####################################################################################################     '

/* The macros to use at the end of your input file (literally)
   to report structures and patterns is just after this comment!

There are some helper macros that have fewer arguments, and make some
choices about what to write in the CIF file for you.

The use of these macros rely on you using some predefined parameters
for specific items. You can use whatever name you want in your own
calculations, and you only need to use them if you want to report on them,
but they need to be defined somewhere with the following names:

-Must be defined (eg local CIF_PHASE_ID 2 )
CIF_ID - (per xdd, or group of xdds) unique identifier to append to block ids to ensure everything is unique
CIF_PHASE_ID - (per str) unique identifier to append to block ids of strs to ensure everything is unique
t0, t1, t2 - (per xdd - only for tof) TOF calibration constants
CIF_TH2_FIXED - (per xdd - only for edxrd) Detector angle in energy-dispersive XRD

-Should be defined
CIF_SCAN_METHOD - (per xdd) "step" - step scan; "cont" continuous scan; "fixed" stationary detector.
									 This is only relevant for CW data.

-Can be defined
CIF_DATETIME	xdd	Date/time when data collection was initiated
CIF_TEMP - (per xdd) Temperature (K) at which data were acquired.
CIF_PRES - (per xdd) Pressure (kPa) at which data were acquired.
CIF_Z - (per str) formula units per unit cell
CIF_SUM_FORMULA - (per str) what is the chemical formula of the unit cell?
CIF_CRYSTAL_SYSTEM - (per str) the crystal system of the space group
CIF_DIFFRACTOMETER_NAME - (per xdd) short description of the diffractometer
(If you use these next two, you are on your own wrt maintaining uniqueness
CIF_DIFFRACTOGRAM_BLOCK_ID	xdd	Fully specified block ID for a diffraction pattern
CIF_PHASE_BLOCK_ID	str	Fully specified block ID for a crystal structure
CIF_DIFFRACTOGRAM_TEXT	xdd	Free-text entry that goes in the data block containing the diffraction data
CIF_PHASE_TEXT	str	Free-text entry that goes in the data block containing the structure


ciffile: the name of the file you want to write to. The data is appended.
data_type: "meas" - data as-measured; or "proc" - data has been processed before analysis
bkg_eqn: an equation defining your background function so it can be ouput in the CIF
n,m: numbers representing the xdds over which the output should be run.
*/
'######################################################################'

macro Out_pdCIF_per_xdd(ciffile)                     { Out_pdCIF_per_xdd(ciffile, "proc", =Get(bkg);) }
macro Out_pdCIF_per_xdd(ciffile, data_type)          { Out_pdCIF_per_xdd(ciffile, data_type, =Get(bkg);) }
macro Out_pdCIF_per_xdd(ciffile, data_type, bkq_eqn) {
/*
If you wish to change the output on a per-xdd basis, use this macro in each xdd.
Otherwise, use Out_pdCIF()
*/
	Out_pdCIF_xdd_setup
	if Obj_There(str) { for strs { Out_pdCIF_STR(ciffile, CIF_PHASE_ID, CIF_ID) } }
	Out_pdCIF_diffraction_data(ciffile, data_type, bkq_eqn, CIF_PHASE_ID, CIF_ID)
}


macro Out_pdCIF(ciffile)                     { Out_pdCIF(ciffile, "proc", =Get(bkg);) }
macro Out_pdCIF(ciffile, data_type)          { Out_pdCIF(ciffile, data_type, =Get(bkg);) }
macro Out_pdCIF(ciffile, data_type, bkq_eqn) { Out_pdCIF(ciffile, data_type, bkq_eqn, , ) }
macro Out_pdCIF(ciffile, data_type, bkq_eqn, n, m) {
/*
This is the macro to use if the structures in each xdd are independent of each other
ie, they are not being co-refined on multiple datasets

Some examples on how to use the Out_pdCIF macro:

-----------------------------------------------
# 1: single pattern, many strs
xdd
	...
	str
		local CIF_PHASE_ID 1
		local !CIF_Z = 2;
		...
	str
		local CIF_PHASE_ID 2
		...
	str
		local CIF_PHASE_ID 3
		...
macro CIF_OUTPUT_FILE { "filename.cif" }
Out_pdCIF(CIF_OUTPUT_FILE)
-----------------------------------------------
-----------------------------------------------
# 2: many patterns, many strs
xdd
	local CIF_ID 1
	local !CIF_SCAN_METHOD = "fixed";
	local CIF_PRES 100
	...
	str
		local CIF_PHASE_ID 1
		...
xdd
	local CIF_ID 2
	local !CIF_SCAN_METHOD = "cont";
	local CIF_PRES 400
	...
	str
		local CIF_PHASE_ID 1
		...
	str
		local CIF_PHASE_ID 2
		local !CIF_Z 6
		...
	str
		local CIF_PHASE_ID 3
		...
...
Out_pdCIF("filename.cif", meas)

-----------------------------------------------
-----------------------------------------------
# 3: sequential refinement, multiple strs

macro CIF_OUTPUT_FILE { "filename.cif" }
num_runs 30
#list File_Name Temperature {
file_01.xye	30
file_02.xye	45
...
}
prm CIF_ID = Run_Number;
prm CIF_TEMP = Temperature(Run_Number);
prm CIF_SCAN_METHOD = "fixed";
xdd
	...
	str
		local CIF_PHASE_ID 1
		local !CIF_Z = 6;
		...
	str
		local CIF_PHASE_ID 2
		local !CIF_Z = 8;
		...
	str
		local CIF_PHASE_ID 3
		...
Out_pdCIF(CIF_OUTPUT_FILE, meas)
-----------------------------------------------
*/
	for xdds n_to_m(n,m) {
		Out_pdCIF_per_xdd(ciffile, data_type, bkq_eqn)
	}
}

macro Out_pdCIF_multi(ciffile)                     { Out_pdCIF_multi(ciffile, "proc", =Get(bkg);) }
macro Out_pdCIF_multi(ciffile, data_type)          { Out_pdCIF_multi(ciffile, data_type, =Get(bkg);) }
macro Out_pdCIF_multi(ciffile, data_type, bkg_eqn) { Out_pdCIF_multi(ciffile, data_type, bkg_eqn, 1, ) }
macro Out_pdCIF_multi(ciffile, data_type, bkg_eqn, n, m) {
/*
This is the macro to use if the structures in each xdd are dependent of each other
ie, all structures are being co-refined on all xdds and all structures are present
in all xdds

eg multi-bank TOF data.

Some examples on how to use the Out_pdCIF_multi macro:

-----------------------------------------------
# 1: multiple patterns, multiple strs
prm CIF_ID 1
prm CIF_TEMP 5
xdd 'eg bank 1 of a tof dataset'
	...
	str
		local CIF_PHASE_ID 1
		...
	str
		local CIF_PHASE_ID 2
		...
	str
		local CIF_PHASE_ID 3
		...
xdd 'eg bank 2 of a tof dataset'
	...
	str
		local CIF_PHASE_ID 1
		...
	str
		local CIF_PHASE_ID 2
		local !CIF_Z 6
		...
	str
		local CIF_PHASE_ID 3
		...
...
Out_pdCIF_multi("filename.cif", proc)

-----------------------------------------------
-----------------------------------------------
# 2: sequential refinement, multiple strs,

macro CIF_OUTPUT_FILE { "filename.cif" }
num_runs 30
#list File_Name_b1 File_Name_b2 File_Name_b3 Temperature {
file_b1_01.xye	file_b2_01.xye	file_b3_01.xye	30
file_b1_02.xye	file_b2_02.xye	file_b3_02.xye	35
...
}
prm CIF_ID = Run_Number;
prm CIF_TEMP = Temperature(Run_Number);
xdd File_Name_b1(Run_Number)
	...
	str
		...
	str
		...
xdd File_Name_b2(Run_Number)
	...
	str
		...
	str
		...
xdd File_Name_b3(Run_Number)
	...
	str
		...
	str
		...
for xdds {
	local CIF_SCAN_METHOD = "cont";
	for strs 1 to 1 {
		local CIF_PHASE_ID 1
		local CIF_Z = 6;
	}
	for strs 2 to 2 {
		local CIF_PHASE_ID 2
		local CIF_Z = 8;
	}
}
Out_pdCIF_multi(CIF_OUTPUT_FILE, meas)
-----------------------------------------------
*/
	for xdds n_to_m(n,m) {
		Out_pdCIF_xdd_setup
		local CIF_MULTI_DIFFRACTOGRAM_ID  1
	}
	Out_CIF_newfile(ciffile)
	for xdds n to n { if Obj_There(str) { for strs { Out_pdCIF_STR(ciffile, CIF_PHASE_ID, CIF_ID, n, m) } } }
	for xdds n_to_m(n,m) { Out_pdCIF_diffraction_data(ciffile, data_type, bkg_eqn, CIF_PHASE_ID, CIF_ID) }
}
#endif
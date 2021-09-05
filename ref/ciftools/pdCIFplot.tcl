#!/bin/sh
# the next line restarts this script using wish found in the path\
exec wish "$0" "$@"
# If this does not work, change the #!/usr/bin/wish line below
# to reflect the actual wish location and delete all preceeding lines
#
# (delete here and above)
#!/usr/bin/wish
#
# $Id: pdCIFplot.tcl,v 1.13 2005/03/01 20:48:40 toby Exp toby $
set RevisionNumber {$Revision: 1.13 $}
set RevisionDate {$Date: 2005/03/01 20:48:40 $}
# A routine for plotting data in pdCIFs 
# 
# Prerequisites:
#  1a) BWidget routines be available (tested with version 1.2.1)
#      if the BWidget routines are not in a subdirectory of where this
#      file is located & is not in the normal tcl auto_path, add the 
#      path below by uncommenting & updating the next line:
#      lappend auto_path /usr/local/tcltk/
#      e.g. use /usr/local/tcltk/ if the package is in /usr/local/tcltk/BWidget-1.2.1
#  1b) BLT (for plotting)
#
#  2) file browsecif.tcl and opts.tcl must be in the same directory 
#     as this file
#
#  3) CIF dictionaries are expected to be found in subdirectory dict of the
#      where this file is located. The user can provide alternate locations
#      for CIF dictionaries, as well as decide which dictionaries will be used.
#

# required for starkit (does not hurt otherwise)
package require Tk


if {[llength $argv] != 1 || ![file exists [lindex $argv 0]]} {
    if {$tcl_platform(platform) == "windows"} {
	set types {{"CIF data" ".cif"} {"IUCr Rietveld" .rtv}}
    } else {
	set types {{"CIF data" ".cif .CIF"} {"IUCr Rietveld" ".rtv .RTV"}}
    }
    set file [tk_getOpenFile -title "Select CIF" -parent . \
	    -defaultextension .cif -filetypes $types]
    if {$file == ""} {exit}
    set argv $file
} else {
   set argv [lindex $argv 0]
}

#----------------------------------------------------------------------
#---  Code starts below -----------------------------------------------
#----------------------------------------------------------------------
# default font size
set CIF(font) 13
# Maximum CIF size is set by this variable:
set CIF(maxvalues) 100000
# don't show overridden definitions by default
set CIF(ShowDictDups) 0

# where is this file running from?
set script [info script]
# translate links -- go six levels deep
foreach i {1 2 3 4 5 6} {
    if {[file type $script] == "link"} {
	set link [file readlink $script]
	if { [file  pathtype  $link] == "absolute" } {
	    set script $link
	} {
	    set script [file dirname $script]/$link
	}
    } else {
	break
    }
}
# fixup relative paths
if {[file pathtype $script] == "relative"} {
    set script [file join [pwd] $script]
}
set scriptdir [file dirname $script ]

# where to find the BWidget & BLT libraries
lappend auto_path $scriptdir

source [file join $scriptdir browsecif.tcl]
source [file join $scriptdir opts.tcl]

# load saved dictionary/config info
if {[catch {
    if {$tcl_platform(platform) == "windows"} {
	set file ~/pdcifplot.cfg
    } else {
	set file ~/.pdcifplot_cfg
    }
    if {[file exists $file]} {source $file}
} errmsg]} {
    set ans [MyMessageBox -parent . -title "Save settings error" \
	    -message "Error reading saved settings from file [file nativename $file].\n$errmsg \nOK to try deleting this file?" \
	    -icon error -type {Delete Cancel} -default delete]
    if {$ans == "delete"} {file delete -force $file}
}

# this changes the font size
SetTkDefaultOptions $CIF(font)

# load the initial CIF dictionaries
LoadDictIndices

wm withdraw .
# create window/text widget for CIF file
catch {destroy [set filew .cif]}
toplevel $filew
wm title $filew "CIF file contents"
wm protocol $filew WM_DELETE_WINDOW exit
set CIF(txt) $filew.t
grid [text $CIF(txt) -height 10 -width 80 -yscrollcommand "$filew.s set" -wrap none] \
	-column 0 -row 0 -sticky news
grid [scrollbar $filew.s -command "$CIF(txt) yview"] -column 1 -row 0 -sticky ns
grid columnconfig $filew 0 -weight 1
grid rowconfig $filew 0 -weight 1

# create window/text widget for the CIF definition
catch {destroy [set defw .def]}
toplevel $defw
wm title $defw "CIF definitions"
wm protocol $defw WM_DELETE_WINDOW exit
set CIF(defBox) $defw.t
grid [text $CIF(defBox) -width 45 -height 18 -xscrollcommand "$defw.x set" \
	-yscrollcommand "$defw.y set" -wrap word] -column 0 -row 0 -sticky news
grid [scrollbar $defw.y -command "$CIF(defBox) yview"] -column 1 -row 0 -sticky ns
grid [scrollbar $defw.x -command "$CIF(defBox) xview" \
	-orient horizontal] -column 0 -row 1 -sticky ew
grid columnconfig $defw 0 -weight 1
grid rowconfig $defw 0 -weight 1
# hide it
wm withdraw $defw

if {$tcl_version < 8.2} {
    tk_dialog .error {Old Tcl/Tk} \
	    "Sorry, the CIF Browser requires version 8.2 or later of the Tcl/Tk package. This is $tcl_version" \
	    warning 0 Sorry
    exit
}

if [catch {package require BWidget}] {
    tk_dialog .error {No BWidget} \
	    "Sorry, the pdCIF Plotted requires the BWidget package" \
	    warning 0 Sorry
    exit
}
if [catch {package require BLT}] {
    tk_dialog .error {No BLT} \
	    "Sorry, the pdCIF Plotted requires the BLT package" \
	    warning 0 Sorry
    exit
}


# make frame for the CIF browser
set frame .browser
catch {destroy $frame}
toplevel $frame 
wm title $frame "CIF Browser"
grid [frame $frame.box] -column 0 -row 2 -sticky ew
grid [button $frame.box.c -text Close] -column 0 -row 1 -sticky w
grid columnconfig $frame.box 0 -weight 1
grid columnconfig $frame.box 2 -weight 1
set CIF(editmode) 0
set CIF(changes) 0
set plot(export) 0
set CIF(showCIF) 0

# show or hide the CIF definitions window
proc ShowDefWindow {button window} {
    if {[$button cget -text] == "Show CIF Definitions"} {
	$button config -text "Hide CIF Definitions"
	wm deiconify $window
    } else {
	$button config -text "Show CIF Definitions"
	wm withdraw $window
    }
}

# show of hide the CIF contents window
proc ShowCIFWindow {menu index window master} {
    global CIF
    if {[lindex [$menu entrycget $index -label] 0] == "Show"} {
	$menu entryconfig $index -label "Hide CIF Contents"
	if {$CIF(showCIF) == 0} {
	    # this puts the window under the browser on the first time
	    set x [winfo x $master]
	    set y [expr 5 + [winfo y $master] + [winfo height $master]]
	    wm geometry $window +$x+$y
	    update
	    set CIF(showCIF) 1
	}
	wm deiconify $window
    } else {
	$menu entryconfig $index -label "Show CIF Contents"
	wm withdraw $window
    }
}

# show of hide the CIF browser window
proc ShowCIFBrowser {menu index window} {
    if {[lindex [$menu entrycget $index -label] 0] == "Show"} {
	$menu entryconfig $index -label "Hide CIF Browser"
	wm deiconify $window
    } else {
	$menu entryconfig $index -label "Show CIF Browser"
	wm withdraw $window
    }
}

# make a new graph window
proc MakeEmptyPlot {} {
    global plot
    set name .plot$plot(window)
    toplevel $name
    grid [blt::graph $name.g] -sticky news
    catch {$name.g config -plotbackground white}
    grid columnconfig $name 0 -weight 1
    grid rowconfig $name 0 -weight 1
    incr plot(window)
    wm title $name "Plot #$plot(window)"
    if [catch {
	Blt_ZoomStack $name.g
	Blt_ActiveLegend $name.g
    } errmsg] {
	MyMessageBox -parent $name -title "BLT Error" \
		-message "BLT Setup Error: could not access a Blt_ routine \
		(msg: $errmsg). \
The pkgIndex.tcl is probably not loading bltGraph.tcl.
See the EXPGUI documentation for more info." \
	-icon warning -type {"Limp Ahead"} -default "limp Ahead" 
}
    $name.g legend config -hide 0
    catch {SetPlotLists}
    # reduce the highlight size
    catch {$name.g pen config activeLine -pixels 2}
    wm protocol $name WM_DELETE_WINDOW "destroy $name; catch {SetPlotLists}"
}

proc OpenOneNode {block} {
    global CIF plot
    catch {
	foreach n $plot(blocklist) {
	    $CIF(tree) closetree $n
	}
	$CIF(tree) itemconfigure $block -open 1
    }
}

proc Disableplotting {state} {
    global plot
    set i 1
    while {$i <= [$plot(plotmenu) index end]} {
	if {$state} {
	    $plot(plotmenu) entryconfig $i -state disabled
	} else {
	    $plot(plotmenu) entryconfig $i -state normal
	}
	incr i
    }
}

proc DisableTickWidgets {widgetlist} {
    global plot
    set state $plot(autoticks)
    foreach w $widgetlist {
	if {$state} {
	    catch {$w config -fg gray}
	    catch {$w config -state disabled}
	} else {
	    catch {$w config -fg black}
	    catch {$w config -state normal}
	}
    }
}

# initialize the plot variables used in the custom plot window
proc InitCustomVars {b} {
    global plot
    set col 1
#    foreach item {} {
#	[winfo parent $plot($item)] config -state normal
#    }

    set req 0
    set plot(xaxis) {Select Option}
    set menu [winfo children $b.$col.b]
    $b.$col.b config -state normal
    if {[$menu index end] == "none"} {
	set plot(xaxis) "(not available)"
	$b.$col.b config -state disabled
	incr req
    } elseif {[$menu index end] == 0} {
	$menu invoke 0
    }
    set plot(yaxis) {Select Option}
    set plot(yaxis2) "(Not Used)"
    set menu [winfo children $b.$col.d]
    set menu2 [winfo children $b.$col.e]
    $b.$col.d config -state normal
    $b.$col.e config -state normal
    if {[$menu index end] == "none"} {
	set plot(yaxis) "(not available)"
	set plot(yaxis2) "(not available)"
	$b.$col.d config -state disabled
	$b.$col.e config -state disabled
	incr req
    } elseif {[$menu index end] == 0} {
	$menu invoke 0
    }
    set plot(ymod) "(Not Used)"
    set menu [winfo children $b.$col.f2.e]
    $b.$col.f2.e config -state normal
    if {[$menu index end] == 0} {
	set plot(ymod) "(not available)"
	$b.$col.f2.e config -state disabled
    }
    set plot(ymult) 1.0
    set plot(ymult2) 1.0
    set plot(ymodpow) -1
    set plot(label) {}
    if {$req > 0} {
	$b.$col.f3.b1 config -state disabled
	$b.$col.f3.note config -text "Cannot be plotted: Missing x or y data set"
    } else {
	$b.$col.f3.b1 config -state normal
	$b.$col.f3.note config -text ""
    }
}


# make a selection dialog for the custom plot
proc MakeCustomBox {box} {
    global xdata ydata ymoddata yesd
    global plot

    catch {toplevel $box}
    eval destroy [winfo children $box]
    wm title $box "Custom Plot"

    pack [NoteBook $box.n -bd 2] -expand yes -fill both
    catch {$box.n configure -font [option get $box.n font Canvas]}

    set nl {}
    foreach item [array names xdata] {
	lappend nl [llength $xdata($item)]
    }
    foreach item [array names ydata] {
	lappend nl [llength $ydata($item)]
    }
    set nl [lsort -integer $nl]

    set plot(plotmenulist) {}
    set prev 1
    # testing
    #set prev -1
    set j 0
    foreach n $nl {
	if {$prev == $n} continue
	set prev $n
	incr j
	set b [$box.n insert end $n -text "Set $j: $n points"]
	$box.n itemconfigure $n -raisecmd "InitCustomVars $b"

	grid rowconfig $b 99 -weight 1

	# 1st column 
        set col 1
	grid [frame $b.$col -bd 4 -relief groove] \
		-row 1 -column $col -sticky ns
	set row 0
	grid [label $b.$col.a -text "x-axis" -bg yellow] \
		-row $row -column 0 -columnspan 4 -sticky ew
	set xmenu [tk_optionMenu $b.$col.b plot(xaxis) x]
	$xmenu delete 0 end
	incr row
	grid $b.$col.b -row $row -column 1 -columnspan 3
	$b.$col.b config -width 32
	
	foreach item [array names xdata] {
	    if {$n != [llength $xdata($item)]} continue
	    $xmenu add radiobutton -variable plot(xaxis) -value $item \
		    -label $item
	}
	grid rowconfig $b.$col [incr row] -min 10

	incr row
	grid [label $b.$col.c -text "y-axis" -bg yellow] \
		-row $row -column 0 -columnspan 4 -sticky we

	incr row
	set ymenu [tk_optionMenu $b.$col.d plot(yaxis) y]
	grid $b.$col.d -row $row -column 3 -sticky ew
	$b.$col.d config -width 32
	grid [entry $b.$col.m0 -width 5 -textvariable plot(ymult)] \
		-row $row -column 1 -sticky ew
	grid [label $b.$col.l0 -text " * "] \
		-row $row -column 2 -sticky ew

	incr row
	set ymenu2 [tk_optionMenu $b.$col.e plot(yaxis2) y]
	grid $b.$col.e -row $row -column 3 -sticky ew
	$b.$col.e config -width 32
	grid [entry $b.$col.m1 -width 5 -textvariable plot(ymult2)] \
		-row $row -column 1 -sticky ew
	grid [label $b.$col.l1 -text " * "] \
		-row $row -column 2 -sticky ew
	grid [label $b.$col.e1 -text " +"] \
		-row $row -column 0 -sticky ew

	incr row
	grid [label $b.$col.e2 -text " *"] \
		-row $row -column 0 -sticky ew
	grid [frame $b.$col.f2] \
		-row $row -column 1 -columnspan 3 -sticky ew
	set ymod [tk_optionMenu $b.$col.f2.e plot(ymod) y]
	incr row
	$b.$col.f2.e config -width 32
	grid $b.$col.f2.e -row 1 -column 1 -sticky ew
	grid [label $b.$col.f2.l1 -text " ** "] \
		-row 1 -column 2 -sticky ew
	grid [entry $b.$col.f2.m1 -width 3 -textvariable plot(ymodpow)] \
		-row 1 -column 3 -sticky ew

	grid [frame $b.$col.f3] \
		-row $row -column 0 -columnspan 4 -sticky ew
	grid [label $b.$col.f3.l1 -text "Plot label"] \
		-row 1 -column 2 -sticky ew
	grid [entry $b.$col.f3.m1 -width 8 -textvariable plot(label)] \
		-row 1 -column 3 -sticky ew
	grid [label $b.$col.f3.l2 -text "Plot in Window #"] \
		-row 1 -column 4 -sticky ew
	set menu [tk_optionMenu $b.$col.f3.m2 plot(graph) x]
	if {[lsearch $plot(plotmenulist) $menu] == -1} {
	    lappend plot(plotmenulist) $menu
	}
	grid $b.$col.f3.m2 -row 1 -column 5 -sticky ew
	grid [label $b.$col.f3.note -fg red -text ""] \
		-row 2 -column 0 -columnspan 6
	grid [button $b.$col.f3.b1 -text "Plot" -command MakeCustomPlot] \
		-row 3 -column 2 -sticky ew
	grid [button $b.$col.f3.b3 -text "New Plot Window" \
		-command MakeEmptyPlot] \
		-column 3 -columnspan 2 -row 3
	grid [button $b.$col.f3.b2 -text Close -command "destroy $box"] \
		-row 3 -column 6 -sticky ew

	$ymenu delete 0 end
	$ymenu2 delete 0 end
	$ymod delete 0 end
	$ymenu2 add radiobutton -variable plot(yaxis2) -value "(Not Used)" \
		    -label "(Not used)"
	$ymod add radiobutton -variable plot(ymod) -value "(Not Used)" \
		    -label "(Not used)"
	foreach item [array names ydata] {
	    if {$n != [llength $ydata($item)]} continue
	    $ymenu add radiobutton -variable plot(yaxis) -value $item \
		    -label $item
	    $ymenu2 add radiobutton -variable plot(yaxis2) -value $item \
		    -label $item
	}
	foreach item [array names ymoddata] {
	    if {$n != [llength $ymoddata($item)]} continue
	    $ymod add radiobutton -variable plot(ymod) -value $item \
		    -label $item
	}
	foreach item [array names yesd] {
	    if {$n != [llength $yesd($item)]} continue
	    $ymod add radiobutton -variable plot(ymod) -value "sigma $item" \
		    -label sigma($item)
	}
	grid rowconfig $b.$col [incr row] -weight 1

	# n-1 column 
	set col 20
	grid [frame $b.$col -bd 4 -relief groove] \
		-row 1 -column $col -sticky ns
	set row 0
	grid [label $b.$col.h -text "Select color" -bg yellow] \
		-row $row -column 1 -sticky we
	foreach c "black blue green red yellow magenta cyan" {
	    incr row
	    grid [radiobutton $b.$col.$row -text $c \
		    -variable plot(color) -value $c -fg $c] \
		    -row $row -column 1 -sticky w
	}
	grid rowconfig $b.$col [incr row] -weight 1

	# n-1 column 
	incr col
	grid [frame $b.$col -bd 4 -relief groove] \
		-row 1 -column $col -sticky ns
	set row 0
	grid [label $b.$col.h -text "Display opts" -bg yellow] \
		-row $row -column 1 -sticky we
	foreach c "{no line} thin thick" val "0 1 3" {
	    incr row
	    grid [radiobutton $b.$col.$row -text $c \
		    -variable plot(line) -value $val] \
		    -row $row -column 1 -sticky nw
	}
	grid rowconfig $b.$col $row -pad 5
	foreach c "{no symbol} cross {thick cross} circle square" \
		val "none      splus  plus         circle square" {
	    incr row
	    grid [radiobutton $b.$col.$row -text $c \
		    -variable plot(symbol) -value $val] \
		    -row $row -column 1 -sticky nw
	}
	grid rowconfig $b.$col [incr row] -weight 1
    }

    if {[SetPlotLists] == 0} {
	# if there are no open windows, create one
	MakeEmptyPlot
	SetPlotLists
    }
    set first [lindex [$box.n pages] 0]
    $box.n see $first
    $box.n raise $first
    $box.n compute_size
}

# set lists of variables for custom plot window
proc SetPlotLists {} {
    global plot
    set valueok 0
    foreach menu $plot(plotmenulist) {
	if {[winfo exists $menu]} {$menu delete 0 end}
    }
    set openplots 0
    for {set i 0} {$i < $plot(window)} {incr i} {
	if {[winfo exists .plot$i.g]} {
	    incr openplots
	    set j [expr $i + 1]
	    foreach menu $plot(plotmenulist) {
		if {[winfo exists $menu]} {
		    $menu add radiobutton -variable plot(graph) -value $j \
			    -label "Window #$j"
		}
	    }
	    if {$plot(graph) == $j} {set valueok 1}
	}
    }
    if {!$valueok && $openplots > 0} {
	foreach menu $plot(plotmenulist) {
	    if {[winfo exists $menu]} {$menu invoke 0}
	}
    }
    return $openplots
}

# make a custom plot
proc MakeCustomPlot {} {
    global plot xdata ydata ymoddata yesd
    if {$plot(xaxis) == ""} return
    if {$plot(yaxis) == ""} return
    set xlist  {}
    set ylist  {}
    set ylist2 {}
    set ymod   {}
    catch {
	set xlist $xdata([set plot(xaxis)])
	set ylist $ydata([set plot(yaxis)])
    }
    set ymult 1.0
    catch {set ymult [expr $plot(ymult)]}
    if {[llength $xlist] == 0 || [llength $ylist] == 0} {return}

    catch {set ylist2 $ydata([set plot(yaxis2)])}
    catch {set ymod   $ymoddata([set plot(ymod)])}
    if {$ymod == ""} {
	catch {set ymod   $yesd([lindex [set plot(ymod)] end])}
    }
    set ymult2 1.0
    catch {set ymult2 [expr $plot(ymult2)]}
    set ymodpow 1.0
    catch {set ymodpow [expr $plot(ymodpow)]}
    set xval {}
    set yval {}
    foreach x $xlist y1 $ylist y2 $ylist2 ym $ymod {
	if {$x != "." && $y1 != "." && $y2 != "." && $ym != "."} {
	    lappend xval $x
	    set y $y1
	    catch {
		if {$ymult != 1.0} {set y [expr {$ymult * $y}]}
		if {$y2 != "" } {set y [expr {$y + ($ymult2 * $y2)}]}
		if {$ym != "" } {set y [expr {$y * pow($ym,$ymodpow)}]}
	    }
	    lappend yval $y
	}
    }
    
    incr plot(entrynum)

    set i $plot(graph)
    incr i -1
    .plot$i.g element create $plot(entrynum) -xdata $xval -ydata $yval \
	    -symbol $plot(symbol) -color $plot(color) -line $plot(line) \
	    -pixels 2 -label $plot(label)

}

# set a color option widget to a list of colors, where names are
# displayed in the color
proc ColorMenu {button} {
    set var [$button cget -textvariable]
    set menu [winfo children $button]
    $menu delete 0 end
    foreach color {black blue green red yellow magenta cyan} {
	$menu add radiobutton -label $color -value $color \
		-variable $var -foreground $color
    }
}

# initialize the plot variables used in a Rietveld plot
proc InitRietveldVars {b} {
    global plot
    set flag 0
    foreach var {xaxis  yobs   ycalc   yback   sigy} \
	    req {  2     1       1       0       0 } {
	set plot($var) "(select an option)"
	$b.$var config -state normal
	set menu [winfo children $b.$var]
	if {[$menu index end] == "none"} {
	    set plot($var) "(not available)"
	    $b.$var config -state disabled
	    if {$req} {incr flag $req}
	} elseif {[$menu index end] == 0} {
	    $menu invoke 0
	}
    }
    if {$flag >= 2} {
	$b.bot.b1 config -state disabled
	$b.bot.note config -text "Cannot be plotted: Missing x or y data set"
    } else {
	$b.bot.b1 config -state normal
	$b.bot.note config -text ""
    }
}

# make a selection window for a Rietveld plot
proc MakeRietveldBox {box} {
    global xdata ydata ymoddata yesd
    global plot
    set plot(warnings) -1

    catch {toplevel $box}
    wm title $box "Plot Rietveld results"
    eval destroy [winfo children $box]

    # variables for possible use on xaxis
    global xaxisvars
    array set xaxisvars {
	_pd_meas_2theta_range_     2Theta
	_pd_proc_2theta_range_     "corrected 2Theta"
	_pd_meas_2theta_scan       2Theta
	_pd_meas_time_of_flight   "TOF, ms"
	_pd_proc_2theta_corrected "corrected 2Theta"
	_pd_proc_energy_incident  "energy, eV"
	_pd_proc_wavelength       "wavelength, A"
	_pd_proc_d_spacing        "d-space, A"
	_pd_proc_recip_len_Q      "Q, 1/A"
	_pd_meas_position         "linear position, mm"
    }
    array set yobsvars {
	_pd_meas_counts_total     Counts
	_pd_meas_intensity_total  Intensity
	_pd_proc_intensity_net    "Corrected Intensity"
	_pd_proc_intensity_total  Intensity
    }
    array set ybckvars {
	_pd_meas_counts_background     Background
	_pd_meas_counts_container      Container
	_pd_meas_intensity_background  Background
	_pd_meas_intensity_container   Container
	_pd_proc_intensity_bkg_calc    "Fit background"
	_pd_proc_intensity_bkg_fix     "Fixed background"
    }
    array set ycalcvars {
	_pd_calc_intensity_net         "Corrected Intensity"
	_pd_calc_intensity_total       Intensity
    }
    array set ymodvars {
	_pd_proc_ls_weight             1/sqrt(weight)
	_pd_meas_counts_total          sqrt(counts)
    }
    array set yesdvars {
	_pd_meas_intensity_total       "Intensity S.U."
	_pd_proc_intensity_net         "Intensity S.U."
	_pd_proc_intensity_total       "Intensity S.U."
    }

    pack [NoteBook $box.n -bd 2] -expand yes -fill both
    catch {$box.n configure -font [option get $box.n font Canvas]}
    
    set nl {}
    foreach item [array names xdata] {
	lappend nl [llength $xdata($item)]
    }
    foreach item [array names ydata] {
	lappend nl [llength $ydata($item)]
    }
    set nl [lsort -integer $nl]

    set prev 1
    set j 0
    foreach n $nl {
	if {$prev == $n} continue
	incr j
	set prev $n

	# what data items are available with the current number of points?
	set xaxislist {}
	foreach item [array names xdata] {
	    if {$n != [llength $xdata($item)]} continue
	    if {[lsearch [array names xaxisvars] $item] != -1} {
		lappend xaxislist $item
	    }
	}
	#if {$xaxislist == ""} continue

	set yobslist {}
	set ybcklist {}
	set ycalclist {}
	foreach item [array names ydata] {
	    if {$n != [llength $ydata($item)]} continue
	    if {[lsearch [array names yobsvars] $item] != -1} {
		lappend yobslist $item
	    }
	    if {[lsearch [array names ybckvars] $item] != -1} {
		lappend ybcklist $item
	    }
	    if {[lsearch [array names ycalcvars] $item] != -1} {
		lappend ycalclist $item
	    }
	}
	#if {$yobslist == "" && $ycalclist == ""} continue

	set yesdlist {}
	foreach item [array names yesd] {
	    if {$n != [llength $yesd($item)]} continue
	    if {[lsearch [array names yesdvars] $item] != -1} {
		lappend yesdlist $item
	    }
	}
	set b [$box.n insert end $n -text "Set $j: $n points"]
	$box.n itemconfigure $n -raisecmd "InitRietveldVars $b"
	grid rowconfig $b 99 -weight 1

        set row 0
	grid [label $b.a$row -text "CIF Data Item" -bg yellow] \
		    -row $row -column 0 -sticky ew
	grid [label $b.b$row -text color -bg yellow] \
		    -row $row -column 2 -sticky ew
	grid [label $b.c$row -text symbol -bg yellow] \
		    -row $row -column 3 -sticky ew
	grid [label $b.d$row -text line -bg yellow] \
		    -row $row -column 4 -sticky ew

	foreach lbl {x-axis y(obs) sigma(y) y(calc) y(bck) \
		obs-calc "Cumulative Chi2"  (obs-calc)/sig   norm}\
		var  {xaxis  yobs   sigy     ycalc   yback  \
		""       ""    ""        ""} \
		color { -    black  -        red     green  \
		blue     cyan  black     black } \
		symbol { -   cross  -        none    none   \
		none     none  none     none} \
		line { -  "no line"  -       thin   thick  \
		thin     thick thin    thin} {
	    incr row
	    grid [label $b.a$row -text $lbl -bg yellow] \
		    -row $row -column 1 -columnspan 1 -sticky ew
	    if {$var != ""} {
		set $var [tk_optionMenu $b.$var plot($var) x]
		grid $b.$var -row $row -column 0 -columnspan 1
		$b.$var config -width 32
	    } else {
		set var [lindex $lbl end]
	    }
	    if {$color != "-"} {
		set menu [tk_optionMenu $b.c$var plot(color_$var) \
			black blue green red yellow magenta cyan]
		ColorMenu $b.c$var
		set plot(color_$var) $color
		grid $b.c$var -row $row -column 2 -sticky ew
		$b.c$var config -width 7

		set menu [tk_optionMenu $b.s$var plot(sym_$var) \
			none cross plus circle square]
		set plot(sym_$var) $symbol
		grid $b.s$var -row $row -column 3 -sticky ew
		$b.s$var config -width 5

		set menu [tk_optionMenu $b.l$var plot(line_$var) \
			{no line} thin thick]
		set plot(line_$var) $line
		grid $b.l$var -row $row -column 4 -sticky ew
		$b.l$var config -width 7
	    }
	    if {$var == "yback"} {
		incr row
		grid [set refbox [frame $b.refl -relief sunken -bd 3]] \
			-row $row -column 0 -rowspan 7 -sticky news \
			-pady 5 -padx 5
		grid [frame $b.fr$var -relief groove -bd 2] \
			-row $row -column 2 -columnspan 3 -sticky ew
		grid [checkbutton  $b.fr$var.b \
			-variable plot(bkgsub) \
			-text "Subtract background"] -sticky w
	    } elseif {$var == "yobs"} {
		grid [frame $b.fr$var -relief groove -bd 2] \
			-row [expr $row+1] -column 2 -columnspan 3 -sticky ew
		grid [checkbutton  $b.fr$var.b \
			-variable plot(errorbars) \
			-text "Plot error bars"] -sticky w
	    } elseif {$var == "obs-calc"} {
		incr row
		grid [frame $b.fr$var -relief groove -bd 2] \
			-row $row -column 2 -columnspan 3 -sticky ew
		grid [checkbutton  $b.fr$var.b \
			-variable plot(diffoffset) \
			-text "Offset difference plot"] -sticky w
	    } elseif {$var == "norm"} {
		incr row
		grid [frame $b.fr$var -relief sunken -bd 4] \
			-row $row -rowspan 2 -column 2 -columnspan 3 -sticky ew
		grid [label $b.fr$var.b -text "Intensity rescaling" \
			-bg yellow] -sticky ew -column 0 -columnspan 2 -row 0
		set menu [tk_optionMenu $b.fr$var.b1 plot(normlbl) none]
		grid $b.fr$var.b1 -row 1 -column 0 -columnspan 2
		grid columnconfig $b.fr$var 1 -weight 1
		$menu delete 0 end
		foreach item {"Don't renormalize" \
			"Renormalize to counts" "Average & Renormalize" \
			"Smooth & Renormalize"} \
			val {0 3 1 2} {
		    $menu add radiobutton -variable plot(normlbl) \
			    -value $item -label $item \
			    -command "set plot(applynorm) $val"
		}
	    }
	}
	# reflection labeling options
	global refl
	set row1 1
	grid [label $refbox.a -text "Reflection Marks" -bg yellow] \
		    -row $row1 -column 1 -columnspan 99 -sticky new
	incr row1
	grid [checkbutton $refbox.b -text "Show Tickmarks for reflections" \
		-variable plot(reflections)] \
		    -row $row1 -column 1 -columnspan 99 -sticky nw
	incr row1
	grid [checkbutton $refbox.browse -text "Reflection Index Browser" \
		    -variable plot(browseticks)] \
		    -row $row1 -column 1 -columnspan 99 -sticky nw
	incr row1
	grid [checkbutton $refbox.auto -text "Automatic tickmark placement" \
		    -variable plot(autoticks)] \
		    -row $row1 -column 1 -columnspan 99 -sticky nw

	incr row1
	grid columnconfig $refbox 99 -weight 1
	grid rowconfig $refbox 99 -weight 1
	if {[llength $refl(phaselist)] > 1} {
	    grid [NoteBook $refbox.l -bd 2] \
		    -row $row1 -column 1 -sticky w -columnspan 99
	    catch {$refbox.l configure -font [option get $refbox.l font Canvas]}
	    set bxlist {}
	    foreach ph $refl(phaselist) {
		lappend bxlist [$refbox.l insert end $ph -text $ph]
	    }
	} else {
	    incr row1
	    grid [frame $refbox.l -bd 2 -relief groove] \
		    -row $row1 -column 1 -sticky w -columnspan 99
	    set bxlist $refbox.l
	}
	set TickWidgetList {}
	set i -1
	foreach ph $refl(phaselist) bx $bxlist {
	    incr i
	    grid [label $bx.c1 -text "Tickmark color"] \
		    -row 1 -column 0 -columnspan 2 -sticky w
	    tk_optionMenu $bx.c2 plot(refcolor$i) black
	    ColorMenu $bx.c2
	    grid $bx.c2 -row 1 -column 2 -columnspan 2 -sticky w
	    grid [label $bx.0 -text "Tickmark locations"] \
		    -row 2 -rowspan 2 -column 0 -columnspan 2 
	    grid [label $bx.1 -text "Ymin:"] -row 2 -column 2
	    grid [entry $bx.2 -textvariable plot(refmin$i) -width 8]\
		    -row 2 -column 3
	    grid [label $bx.3 -text "Ymax:"] -row 3 -column 2
	    grid [entry $bx.4 -textvariable plot(refmax$i) -width 8]\
		    -row 3 -column 3
	    lappend TickWidgetList $bx.0 $bx.1 $bx.2 $bx.3 $bx.4
	}
	if {[llength $refl(phaselist)] > 1} {
	    set first [lindex [$refbox.l pages] 0]
	    $refbox.l see $first
	    $refbox.l raise $first
	    $refbox.l compute_size
	}
	incr row1
	$refbox.auto configure -command \
		"DisableTickWidgets [list $TickWidgetList]"
	DisableTickWidgets $TickWidgetList

	# add entries to x-axis menubutton
  	$xaxis delete 0 end
	foreach item $xaxislist {
	    $xaxis add radiobutton -variable plot(xaxis) -value $item \
		    -label "$item ($xaxisvars($item))"
	}

	# add some easily derived units
	set wavelengths 0 
	catch {set wavelengths [llength $xdata(_diffrn_radiation_wavelength)]}
	if {[lsearch $xaxislist _pd_proc_recip_len_Q] == -1} {
	    if {[lsearch $xaxislist _pd_proc_d_spacing] != -1} {
		# conversion from d-space is easy
		$xaxis add radiobutton -variable plot(xaxis) \
			-value  "Q (_pd_proc_d_spacing)" \
			-label "Q (1/A) from _pd_proc_d_spacing"
	    } elseif {$wavelengths > 0} {
		# conversion from 2theta is easy, too
		foreach item {
		    _pd_proc_2theta_corrected
		    _pd_proc_2theta_range_
		    _pd_meas_2theta_range_
		    _pd_meas_2theta_scan
		} {
		    if {[lsearch $xaxislist $item] != -1} {
			$xaxis add radiobutton -variable plot(xaxis) \
				-value  "Q ($item)" \
				-label "Q (1/A) from $item"
			break
		    }
		}
	    }
	}
	if {[lsearch $xaxislist _pd_proc_d_spacing] == -1} {
	    if {[lsearch $xaxislist _pd_proc_recip_len_Q] != -1} {
		$xaxis add radiobutton -variable plot(xaxis) \
			-value  "d-space (_pd_proc_recip_len_Q)" \
			-label "D-space (A) from _pd_proc_recip_len_Q"
	    } elseif {$wavelengths > 0} {
		# conversion from 2theta is easy, too
		foreach item {
		    _pd_proc_2theta_corrected
		    _pd_proc_2theta_range_
		    _pd_meas_2theta_range_
		    _pd_meas_2theta_scan
		} {
		    if {[lsearch $xaxislist $item] != -1} {
			$xaxis add radiobutton -variable plot(xaxis) \
				-value  "d-space ($item)" \
				-label "D-space (A) from $item"
			break
		    }
		}
	    }
	}

	# observed Y
	$yobs delete 0 end
	foreach item $yobslist {
	    $yobs add radiobutton -variable plot(yobs) -value $item \
		    -label "$item ($yobsvars($item))"
	}
	$ycalc delete 0 end
	foreach item $ycalclist {
	    $ycalc add radiobutton -variable plot(ycalc) -value $item \
		    -label "$item ($ycalcvars($item))"
	}
	$yback delete 0 end
	foreach item $ybcklist {
	    $yback add radiobutton -variable plot(yback) -value $item \
		    -label "$item ($ybckvars($item))"
	}
	$sigy delete 0 end
	set item _pd_meas_counts_total
	if {[array names ydata $item] != ""} {
	    if {$n == [llength $ydata($item)]} {
		$sigy add radiobutton -variable plot(sigy) \
			-value "from $item" \
			-label "$ymodvars($item) from $item"
	    }
	}
	set item _pd_proc_ls_weight
	if {[array names ymoddata $item] != ""} {
	    if {$n == [llength $ymoddata($item)]} {
		$sigy add radiobutton -variable plot(sigy) \
			-value "from $item" \
			-label "$ymodvars($item) from $item"
	    }
	}
	foreach item $yesdlist {
	    $sigy add radiobutton -variable plot(sigy) \
		    -value "from $item" \
		    -label "S.U. (esd) of $item"
	}

	grid [frame $b.bot] \
		-row [incr row] -column 0 -columnspan 2 -sticky w
	grid columnconfig $b.bot 0 -weight 1
	grid [label $b.bot.note -fg red -text ""] \
		-row 0 -column 0 -columnspan 3
	grid [button $b.bot.b1 -text "Plot" -command "MakeRietveldPlot $box"] \
		-row 1 -column 0 -sticky w
	grid [button $b.bot.b2 -text "Close" -command "destroy $box"] \
		-row 1 -column 1 -sticky w
    }
    set first [lindex [$box.n pages] 0]
    $box.n see $first
    $box.n raise $first
    $box.n compute_size
}

# loop through plot windows to find an empty one, create one if needed
proc GetEmptyPlot {} {
    global plot
    # use a plot$n.g if empty, otherwise create a plot & use it
    set none 1
    for {set i 0} {$i < $plot(window)} {incr i} {
	if {[winfo exists .plot$i.g]} {
	    set none 0
	    if {[.plot$i.g element names] == ""} {
		return .plot$i.g
	    }
	}
    }
    if {$none} {set plot(window) 0}
    set graph .plot$plot(window).g
    MakeEmptyPlot
    return $graph
}

# evaluate the best-fit Chebyschev polynomial to a set of X and Y values.
# order is the # of terms 
proc FitFunc {X Y order Xmin Xmax} {
    set o $order
    # zero the matrix and vector
    for {set j 0} {$j < $o} {incr j} {
	set sum($j) 0.
	for {set i 0} {$i <= $j} {incr i} {
	    set sum(${i}_$j) 0.
	}
    }
    #global octave
    #set octave {}
    #append octave {des = [}
    set Xnorm  [expr {2. / (1.*$Xmax - 1.*$Xmin)}]
    foreach y $Y xt $X {
	# rescale x
	set x [expr {-1 + $Xnorm * (1.*$xt - $Xmin)}]
	# compute derivatives at point x
	set derivlist {}
	set Tpp 0
	set Tp 0
	# compute the Chebyschev term Tn(xs)
	for {set i 0} {$i < $o} {incr i} {
	    if {$Tpp == $Tp && $Tp == 0} {
		set T 1
	    } elseif {$Tpp == 0} {
		set T $x
	    } else {
		set T [expr {2. * $x * $Tp - $Tpp}]
	    }
	    lappend derivlist $T
	    set Tpp $Tp
	    set Tp $T
	}
	#append octave " $derivlist ;\n"
	# compute matrix elements
	for {set j 0} {$j < $o} {incr j} {
	    set Tj [lindex $derivlist $j]
	    # weighted
	    # set sum($j) [expr {$sum($j) + $y * $Tj / ($sigma*$sigma)}]
	    set sum($j) [expr {$sum($j) + $y * $Tj}]
	    for {set i 0} {$i <= $j} {incr i} {
		set Ti [lindex $derivlist $i]
		# weighted
		# set sum(${i}_$j) [expr {$sum(${i}_$j) + $Ti * $Tj / ($sigma * $sigma)}]
		set sum(${i}_$j) [expr {$sum(${i}_$j) + $Ti * $Tj}]
	    }
	}
    }
    # populate the matrix & vector in La format
    lappend V 2 $o 0
    lappend A 2 $o $o
    for {set i 0} {$i < $o} {incr i} {
	lappend V $sum($i)
	for {set j 0} {$j < $o} {incr j} {
	    if {$j < $i} {
		lappend A $sum(${j}_$i)
	    } else {
		lappend A $sum(${i}_$j)
	    }
	}
    }
    set termlist {}
    if {[catch {
	set termlist [lrange [La::msolve $A $V] 3 end]
    }]} {
	tk_dialog .singlar "Singular Matrix" \
	    "Unable to fit function: singular matrix. Too many terms or something else is wrong." ""\
	    0 OK
    }
    return $termlist
}

# evaluate the Chebyshev polynomial with coefficients A at point x
# coordinates are rescaled from $xmin=-1 to $xmax=1
proc chebeval {A x xmin xmax} {
    set xs [expr {-1 + 2 * (1.*$x - $xmin) / (1.*$xmax - 1.*$xmin)}]
    set Tpp 0
    set Tp 0
    set total 0
    foreach a $A {
	if {$Tpp == $Tp && $Tp == 0} {
	    set T 1
	} elseif {$Tpp == 0} {
	    set T $xs
	} else {	
	    set T [expr {2. * $xs * $Tp - $Tpp}]
	}
	set total [expr {$total + $a * $T}]
	set Tpp $Tp
	set Tp $T
    }
    return $total
}

# make a Rietveld plot
proc MakeRietveldPlot {parent} {
    global plot xdata ydata ymoddata yesd
    global refl
    foreach var {xaxis  yobs   ycalc} \
	    msg {"x-axis" y(obs) y(calc)} {
	if {$plot($var) == "(select an option)"} {
	    incr plot(warnings)
	    if {$plot(warnings)} {
		MyMessageBox -parent $parent -title "Select Axis" \
		-message "Unable to produce a plot.\nPlease select a data item for $msg" \
		-icon warning -type Continue -default continue
	    } else {
		bell
	    }
	    return
	#} elseif {$plot($var) == "(not available)"} {
	#    return
	}
    }
    global blcksel
    pleasewait "while computing values" "" $parent
    set xlist  {}
    set yobslist  {}
    set ybcklist  {}
    set ycalclist  {}
    set ydiflist  {}
    set difOsiglist  {}

    # process the x-axis
    set lambda {}
    catch {
	set lambda [lindex $xdata(_diffrn_radiation_wavelength) 0]
    }
    set xlist {}
    if {[llength $plot(xaxis)] != 1} {
	set unit [lindex $plot(xaxis) 0]
	# OK need to compute something -- from what?
	set from {}
	regexp {.*\((.*)\)} $plot(xaxis) junk from
	if {$from == ""} {
	    # this should not happen
	    error "why no match for the x-axis?"
	}
	if {$unit == "Q"} {
	    foreach x $xdata($from) {
		set Q .
		catch {
		    switch $from {
			_pd_proc_d_spacing {
			    set Q [expr {8*atan(1) / $x}]
			}
			_pd_proc_recip_len_Q {set Q $x}
			_pd_proc_2theta_corrected {-}
			_pd_proc_2theta_range_ {-}
			_pd_meas_2theta_range_ {-}
			_pd_meas_2theta_scan {
			    set Q [expr {16*atan(1) \
				    * sin($x * atan(1)/90. ) / $lambda}]
			}
		    }
		}
		lappend xlist $Q
	    }
	} else {
	    foreach x $xdata($from) {
		set d .
		catch {
		    switch $from {
			_pd_proc_d_spacing {set d $x}
			_pd_proc_recip_len_Q {
			    set d [expr {8*atan(1) / $x}]
			}
			_pd_proc_2theta_corrected {-}
			_pd_proc_2theta_range_ {-}
			_pd_meas_2theta_range_ {-}
			_pd_meas_2theta_scan {
			    set d [expr {0.5 * $lambda / \
				    sin($x * atan(1)/90.)}]
			}
		    }
		}
		lappend xlist $d
	    }
	}
    } else {
	global xaxisvars
	set unit $xaxisvars([set plot(xaxis)])
	# remove comma & remainder
	set unit [lindex [split $unit ,] 0]
	catch {
	    set xlist $xdata([set plot(xaxis)])
	}
    }

    # compile a list of the y values
    catch {
	set yobslist $ydata([set plot(yobs)])
    }
    catch {
	set ycalclist $ydata([set plot(ycalc)])
    }
    catch {
	set ybcklist $ydata([set plot(yback)])
    }
    # compile a list of sigma(yobs)
    set list {}
    set siglist {}
    switch [set var [lindex $plot(sigy) 1]] {
	_pd_proc_ls_weight       {
	    catch {set list $ymoddata(_pd_proc_ls_weight)}
	    foreach w $list {
		set val .
		catch {set val [expr {1./sqrt($w)}]}
		lappend siglist $val
	    }
	}
	_pd_meas_counts_total    {
	    catch {set list $ydata(_pd_meas_counts_total)}
	    foreach w $list {
		set val .
		catch {set val [expr {sqrt($w)}]}
		lappend siglist $val
	    }
	}
	_pd_meas_intensity_total {-}
	_pd_proc_intensity_net   {-}
	_pd_proc_intensity_total {catch {set siglist $yesd($var)}}
    }

    foreach list {obs calc bck diff sigdiff errordat \
	    normlist normdat normfit wifddat wifdlist wifdxlist} {
	set $list {}
    }

    # Process the normalizing 
    set normavg 0
    set xfit {}
    set nfit {}
    set Xmin {}
    set Xmax {}
    set n 0
    set plot(normfactor) 1
    catch {
	if {$plot(line_norm) == "no line" && $plot(sym_norm) == "none"} {
	    set plot(normfactor) 0
	}
    }
    if {$plot(normfactor) || $plot(applynorm) != 0} {
	foreach x $xlist yo $yobslist s $siglist {
	    set sf .
	    catch {
		set sf [expr {$yo / ($s*$s)}]
		set normavg [expr {$normavg + $sf}]
		incr n
		expr $x
		if {$Xmin == ""} {
		    set Xmin $x
		    set Xmax $x
		} elseif {$Xmin < $x} {
		    set Xmin $x
		} elseif {$Xmax > $x} {
		    set Xmax $x
		}
		lappend normdat $x $sf
		lappend xfit $x
		lappend nfit $sf
	    }
	    lappend normlist $sf
	}
    }
    if {[catch {
	set normavg [expr {$normavg/$n}]
    }]} {
	set normavg 1
    }
    if {$plot(applynorm) == 2 && [llength $xfit] > 20} {
	# need to smooth the normalization data
	if {[catch {package require La}]} {
	    tk_dialog .noLa "No Linear Algebra Package" \
	    "Unable to smooth. The Linear Algebra (La) package was not found." \
	    "" 0 OK
	} else {
	    set A [FitFunc $xfit $nfit 8 $Xmin $Xmax]
	    set normlist {}
	    foreach x $xlist {
		set sf .
		catch {
		    expr $x
		    set sf [chebeval $A $x $Xmin $Xmax]
		    lappend normfit $x $sf
		}
		lappend normlist $sf
	    }
	}
    } elseif {$plot(applynorm) == 1} {
	# set the normalization factor to the average
	set l {}
	foreach n $normlist {lappend l $normavg}
	set normlist $l
	set normfit 
    }
    # set a data direction, needed for errorbar plotting
    catch {
	if {[lindex $xlist 0] > [lindex $xlist end]} {
	    set traceopt increasing
	    set errcons 0.9999999
	} else {
	    set traceopt decreasing
	    set errcons 1.0000001
	}
    }
    set offset {}
    set wifdsum 0
    foreach var {allymin diffmin allymax diffmax} {
	global $var
	set $var {}
    }
    foreach x $xlist  yo $yobslist yc $ycalclist yb $ybcklist \
	    s $siglist n $normlist {
	if {$plot(applynorm) != 0} {
	    foreach var {yo yc yb s} {
		catch {
		    set val [expr {[set $var]*$n}]
		    set $var $val
		}
	    }
	}
	set min {}
	if {$plot(bkgsub)} {
	    catch {set yo [expr {$yo - $yb}]}
	    catch {set yc [expr {$yc - $yb}]}
	}
	foreach var {yo yc yb} list {obs calc bck} {
	    set val [set $var]
	    catch {
		expr {$x + $val}
		if {$plot(bkgsub)} {
		    if {$var == "yb"} continue
		    if {0 < $min} {set min 0}
		}
		lappend $list $x $val
		if {$plot(diffoffset)} {
		    if {$min == ""} {set min $val}
		    if {$val < $min} {set min $val}
		}
		if {$plot(autoticks)} {
		    if {$allymin == ""} {
			set allymin $val
			set allymax $val
		    }
		    if {$val < $allymin} {set allymin $val}
		    if {$val > $allymax} {set allymax $val}
		}
	    }
	}
	catch {
	    expr {$x + $yo + $yc}
	    set val [expr {$yo - $yc}]
	    if {$plot(diffoffset)} {
		set touch [expr {$min - $val}]
		if {$offset == ""} {set offset $touch}
		if {$touch < $offset} {set offset $touch}
	    }
	    if {$plot(autoticks)} {
		if {$diffmin == ""} {
		    set diffmin $val
		    set diffmax $val
		}
		if {$val < $diffmin} {set diffmin $val}
		if {$val > $diffmax} {set diffmax $val}
	    }
	    lappend xdiff $x
	    lappend ydiff $val
	    lappend diff $x $val
	    lappend sigdiff $x [expr {$val/$s}]

	}
	if {$plot(errorbars)} {
	    catch {
		lappend errordat [expr {$x*$errcons}] [expr {$yo + 2*$s}] \
			[expr {$x/$errcons}] [expr {$yo -2*$s}]	
	    }
	}
	# compute the cumulative chi**2
	if {$plot(line_Chi2) != "no line" || $plot(sym_Chi2) != "none"} {
	    catch {
		set val [expr {pow(($yo - $yc)/$s,2)}]
		expr $x
		lappend wifdlist [set wifdsum [expr {$wifdsum + $val}]]
		lappend wifdxlist $x
	    }
	}
    }
    # compute room needed for autoticks
    if {$plot(autoticks) && $plot(reflections)} {
	set nph [llength $refl(phaselist)]
	catch {
	    set tickspace [expr {($diffmax+$allymax-($diffmin+$allymin))\
		    *(0.025*$nph+.02)}]
	    set offset ""
	    if {($allymin - $diffmax) < $tickspace || $plot(diffoffset)} {
		set offset [expr {-$diffmax + $allymin - $tickspace}]
	    }
	    set tickstart [expr {$allymin - 0.01*($diffmax+$allymax-($diffmin+$allymin))}]
	    set tickinc [expr {0.025*($diffmax+$allymax-($diffmin+$allymin))}]
	}
    }
    # offset the difference plot
    if {($plot(diffoffset) || \
	    ($plot(reflections) && $plot(autoticks))) \
	    && $offset != ""} {
	set diff {}
	foreach x $xdiff y $ydiff {
	    lappend diff $x [expr {$y + $offset}]
	}
    }
    # compute the cumulative chi**2
    if {$plot(line_Chi2) != "no line" || $plot(sym_Chi2) != "none"} {
	set n [llength $wifdlist]
	foreach x $wifdxlist y $wifdlist {
	    catch {
		lappend wifddat $x [expr {$y/$n}]
	    }
	}
    }
    # use plot$n.g if empty, otherwise create a plot & use it
    set graph [GetEmptyPlot]
    foreach list {obs  calc  bck   diff} \
	    var  {yobs ycalc yback obs-calc} {
	set line 0
	set symbol none
	catch {
	    set line [lindex \
		    "0 1 3" [lsearch \
		    "{no line} thin thick" $plot(line_$var)]]
	    set symbol [lindex \
		    "none splus plus circle square" [lsearch \
		    "none cross plus circle square" $plot(sym_$var)]]
	}
	if {[llength [set $list]] > 1} {
	    $graph element create $list -data [set $list] \
		    -pixels 2 -label $list -color $plot(color_$var) \
		    -symbol $symbol -line $line
	}
    }
    if {$plot(errorbars) && [llength $errordat] > 1} {
	$graph element create errbar -data $errordat \
		-label "" -color $plot(color_yobs) \
		-symbol "" -line 1 -trace $traceopt
    }

    set refposlist {}
    global reflist
    set reflist($graph) {}
    set reflist(select_$graph) {}
    # create a vector for reflection indices
    set vec refposvec$graph
    regsub -all {\.} $vec _ vec
    catch {blt::vector $vec}
    if {$plot(reflections)} {
	set i 0
	foreach {ymin ymax} [$graph yaxis limits] {}
	foreach {newymin newymax} [$graph yaxis limits] {}
	foreach item $refl(reflist) {
	    incr i
	    catch {
		foreach {hkl d ph} $item {}
		set phnum [lsearch $refl(phaselist) $ph]
		if {$phnum == -1} {set phnum 0}
		set c $plot(refcolor$phnum)
		if {$plot(autoticks)} {
		    set y1 [expr {$tickstart - $phnum*$tickinc}]
		    set y2 [expr {$y1 - $tickinc}]
		} else {
		    set y1 $plot(refmin$phnum)
		    if {[string first % $y1] != -1} {
			regexp {([+-]?[0-9\.]*).*%} $y1 junk y
			set y1 [expr {$ymin + $y*($ymax-$ymin)/100.}]
		    }
		    if {$newymin > $y1} {set newymin $y1}
		    if {$newymax < $y1} {set newymax $y1}
		    set y2 $plot(refmax$phnum)
		    if {[string first % $y2] != -1} {
			regexp {([+-]?[0-9\.]*).*%} $y2 junk y
			set y2 [expr {$ymin + $y*($ymax-$ymin)/100.}]
		    }
		    if {$newymin > $y2} {set newymin $y2}
		    if {$newymax < $y2} {set newymax $y2}
		}
		if {$unit == "Q"} {
		    set val [expr {8*atan(1)/$d}]
		} elseif {$unit == "d-space"} {
		    set val $d
		} elseif {[string match *2Theta* $unit]} {
		    set val [expr 90*asin(0.5 * $lambda/$d)/atan(1)]
		}
		lappend reflist($graph) [list $val $hkl $ph $d]
		lappend refposlist $val
		set id [$graph marker create line -coords "$val $y1 $val $y2" \
			    -under 1 -outline $c]
		$graph marker bind $id <Enter> "ShowRefhkl $val $graph"
	    }
	}
	$vec set $refposlist
	$graph xaxis config -title $unit
	if {$ymin != $newymin} {$graph yaxis config -min $newymin}
	if {$ymax != $newymax} {$graph yaxis config -max $newymax}
    }
    if {($plot(line_Chi2) != "no line" || $plot(sym_Chi2) != "none") && \
	    [llength $wifddat] > 2} {
	set var Chi2
	set line 1
	set symbol none
	set color black
	catch {
	    set color $plot(color_$var)
	    set line [lindex \
		    "0 1 3" [lsearch \
		    "{no line} thin thick" $plot(line_$var)]]
	    set symbol [lindex \
		    "none splus plus circle square" [lsearch \
		    "none cross plus circle square" $plot(sym_$var)]]
	}
	$graph y2axis config -hide 0 -min 0 -title {Cumulative Chi Squared}
	# modify zoom so that y2axis is not zoomed in for blt2.4u+
	catch {
	    regsub -all y2axis [info body blt::PushZoom] " " b1
	    proc blt::PushZoom {graph} $b1
	}
	$graph element create cChi2 -data $wifddat -mapy y2 \
		-label cChi2 -color $color -dash 4 \
		-symbol $symbol -line $line
    }
    if {[llength $sigdiff] > 1} {
	set var (obs-calc)/sig
	set line 0
	set symbol none
	catch {
	    set line [lindex \
		    "0 1 3" [lsearch \
		    "{no line} thin thick" $plot(line_$var)]]
	    set symbol [lindex \
		    "none splus plus circle square" [lsearch \
		    "none cross plus circle square" $plot(sym_$var)]]
	}
	if {$line != 0 || $symbol != "none"} {
	    # use plot$n.g if empty, otherwise create a plot & use it
	    set graph [GetEmptyPlot]
	    $graph element create dif_s -data $sigdiff \
		    -pixels 2 -label dif/sigma -color $plot(color_$var) \
		    -symbol $symbol -line $line
	    $graph xaxis config -title $unit
	}
    }

    if {$plot(normfactor) && [llength $normdat] > 1} {
	set line 1
	set symbol none
	set color black
	catch {
	    set color $plot(color_norm)
	    set line [lindex \
		    "0 1 3" [lsearch \
		    "{no line} thin thick" $plot(line_norm)]]
	    set symbol [lindex \
		    "none splus plus circle square" [lsearch \
		    "none cross plus circle square" $plot(sym_norm)]]
	}
	if {$line != 0 || $symbol != "none"} {
	    # use plot$n.g if empty, otherwise create a plot & use it
	    set graph [GetEmptyPlot]
	    $graph element create norm -data $normdat \
		    -pixels 2 -label "Norm factor" -color $color \
		    -symbol $symbol -line $line
	    if {$normfit != "" && $plot(applynorm) == 2} {
		$graph element create smooth -data $normfit \
			-label Smoothed -color $color \
			-symbol $symbol -line [expr 3*$line] -dash 10
	    } elseif {$plot(applynorm) == 1} {
		$graph element create smooth \
			-data "$Xmin $normavg $Xmax $normavg" \
			-label Averaged -color $color \
			-symbol $symbol -line [expr 3*$line] -dash 10
	    }
	    $graph xaxis config -title $unit
	}
    }
    donewait
}


proc SelectBlock {block} {
    catch {destroy .b}
    OpenOneNode $block
    global blcksel
    pleasewait "interpreting contents of $block" "" $blcksel

    pdClassifyData $block
    donewait
    global xdata ydata
    if {[llength [array names xdata]] > 0 && \
	    [llength [array names ydata]]> 0} {
	Disableplotting 0
    } else {
	Disableplotting 1
    }
}

# classify the diffraction data in block
#   if checkonly == 0 (default) the data are copied into arrays xdata, ydata...
#   if checkonly == 1 the arrays xdata, ydata are defined but are empty
proc pdClassifyData {block "checkonly 0"} {
    global CIF $block plot
    foreach array {xdata xesd ydata yesd ymoddata} {
	global $array
	catch {unset $array}
    }
    
    set xlist {
	{_pd_meas_2theta_range_min _pd_meas_2theta_range_max _pd_meas_2theta_range_inc}
	{_pd_proc_2theta_range_min _pd_proc_2theta_range_max _pd_proc_2theta_range_inc}
	_pd_meas_2theta_scan
	_pd_meas_time_of_flight
	_pd_proc_2theta_corrected
	_pd_proc_d_spacing
	_pd_proc_energy_incident
	_pd_proc_energy_detection
	_pd_proc_recip_len_Q
	_pd_proc_wavelength
    }

    set ylist {
	_pd_meas_counts_total
	_pd_meas_counts_background
	_pd_meas_counts_container
	_pd_meas_intensity_total
	_pd_meas_intensity_background
	_pd_meas_intensity_container
	_pd_proc_intensity_net
	_pd_proc_intensity_total
	_pd_proc_intensity_bkg_calc
	_pd_proc_intensity_bkg_fix
	_pd_calc_intensity_net
	_pd_calc_intensity_total
    }
    
    set ymod {
	_pd_meas_step_count_time
	_pd_meas_counts_monitor
	_pd_meas_intensity_monitor
	_pd_proc_intensity_norm
	_pd_proc_intensity_incident
	_pd_proc_ls_weight
    }
    
    foreach item $xlist {
	if {[llength $item] == 1} {
	    set marks {}
	    catch {
		set marks [set ${block}($item)]
	    }
	    if {[llength $marks] > 1} {
		if {$checkonly} {
		    set xdata($item) {}
		    continue
		}
		set l {}
		set esdlist {}
		foreach m $marks {
		    set val [StripQuotes [$CIF(txt) get $m.l $m.r]]
		    foreach {val esd} [ParseSU $val] {}
		    lappend l $val
		    if {$esd != ""} {lappend esdlist $esd}
		}
		set xdata($item) $l
		if {[llength $l] == [llength $esdlist]} {
		    set xesd($item) $esdlist
		}
	    }
	} else {
	    catch {
		foreach i $item var {min max step} {
		    set m [set ${block}($i)]
		    set $var [StripQuotes [$CIF(txt) get $m.l $m.r]]
		}
		set l {}
		set i -1
		regsub _min [lindex $item 0] _ itm
		if {$checkonly} {
		    set xdata($itm) {}
		    continue
		}
		if {$step > 0.0} {
		    while {[set T [expr {$min+([incr i]*$step)}]] <= $max+$step/100.} {
			lappend l $T
		    }
		} else {
		    while {[set T [expr {$min+([incr i]*$step)}]] >= $max+$step/100.} {
			lappend l $T
		    }
		}
		set xdata($itm) $l
	    }
	}
    }
    # process the wavelength, if present
    set item _diffrn_radiation_wavelength
    set marks {}
    catch {
	set marks [set ${block}(_diffrn_radiation_wavelength)]
    }
    set l {}
    foreach m $marks {
	set val [StripQuotes [$CIF(txt) get $m.l $m.r]]
	foreach {val esd} [ParseSU $val] {}
	lappend l $val
    }
    if {$l != ""} {set xdata(_diffrn_radiation_wavelength) $l}

    foreach item $ylist {
	set marks {}
	catch {
	    set marks [set ${block}($item)]
	}
	if {[llength $marks] > 1} {
	    if {$checkonly} {
		set ydata($item) {}
		continue
	    }
	    set l {}
	    set esdlist {}
	    foreach m $marks {
		set val [StripQuotes [$CIF(txt) get $m.l $m.r]]
		foreach {val esd} [ParseSU $val] {}
		lappend l $val
		if {$esd != ""} {lappend esdlist $esd}
	    }
	    set ydata($item) $l
	    if {[llength $l] == [llength $esdlist]} {
		set yesd($item) $esdlist
	    }
	}
    }
    
    if {$checkonly} {return}

    foreach item $ymod {
	set marks {}
	catch {
	    set marks [set ${block}($item)]
	}
	if {[llength $marks] > 1} {
	    set l {}
	    foreach m $marks {
		lappend l [StripQuotes [$CIF(txt) get $m.l $m.r]]
	    }
	    set ymoddata($item) $l
	}
    }
    
    # process reflections
    foreach item {_refln_index_h _refln_index_k _refln_index_l \
	    _pd_refln_phase_id _refln_d_spacing} \
	    list {hlist klist llist idlist dlist} {
	set $list {}
	catch {
	    set $list [set ${block}($item)]
	}
    }
    global refl
    set refl(reflist) {}
    catch {unset phaselist}
    # if there are d-spaces in the list, show them
    if {[llength dlist] > 0} {
	foreach h $hlist k $klist l $llist id $idlist d $dlist {
	    set hkl {}
	    foreach m [list $h $k $l] {
		if {$m != ""} {
		    lappend hkl [StripQuotes [$CIF(txt) get $m.l $m.r]]
		}
	    }
	    set phase {}
	    catch {
		set phase [StripQuotes [$CIF(txt) get $id.l $id.r]]
	    }
	    set phaselist($phase) 1
	    set dsp {}
	    catch {
		set dsp [StripQuotes [$CIF(txt) get $d.l $d.r]]
	    }
	    lappend refl(reflist) [list $hkl $dsp $phase]
	}
    }
    set refl(phaselist) {}
    foreach item [array names phaselist] {
	lappend refl(phaselist) $item
    }
    set i -1
    foreach p $refl(phaselist) {
	incr i
	set plot(refcolor$i) black
	set plot(refmin$i) [expr 100 + ($i*5)]%
	set plot(refmax$i) [expr 100 + ($i+1)*5]%
    }
}

# make a list of reflections by graph
proc ShowRefhkl {pos graph} {
    global plot reflist    
    if {!$plot(browseticks)} return
    # if anything goes wrong, give up
    catch {
	set win [winfo parent $graph].hkl
	if {![winfo exists $win]} {
	    toplevel $win
	    wm title $win "hkl browser"
	    grid [frame $win.a] -row 0 -column 0 -sticky w
	    grid [frame $win.con] -row 99 -column 0 -sticky ew
	    grid [label $win.con.r0 -text "Mark reflections\nwith"] \
		    -row 0 -column 0 -rowspan 2
	    grid [checkbutton $win.con.r1 -command "HighlightHKL $graph" \
		    -text line -variable reflist(line)] \
		    -row 1 -column 1 -sticky w
	    grid [checkbutton $win.con.r2 -command "HighlightHKL $graph" \
		    -text indices -variable reflist(label)] \
		    -row 0 -column 1 -sticky w
	    grid [button $win.con.close -command "destroy $win" -text Close] \
		    -row 0 -column 2 -rowspan 2
	    grid columnconfig $win.con 2 -weight 1
	    grid [button $win.a.val -text [$graph xaxis cget -title] \
		    -command "SortHKL val $win $graph" \
		    ] -row 0 -column 0
	    grid [button $win.a.h -text h \
		    -command "SortHKL h $win $graph" \
		    ] -row 0 -column 1
	    grid [button $win.a.k -text k \
		    -command "SortHKL k $win $graph" \
		    ] -row 0 -column 2
	    grid [button $win.a.l -text l \
		    -command "SortHKL l $win $graph" \
		    ] -row 0 -column 3
	    grid [button $win.a.ph -text Phase \
		    -command "SortHKL phase $win $graph" \
		    ] -row 0 -column 4
	    grid [label  $win.a.sel -text Mark] -row 0 -column 5
	    grid [canvas $win.c \
		    -scrollregion {0 0 5000 1000} -width 200 -height 200 \
		    -yscrollcommand "$win.scroll set"] \
		    -column 0 -row 1 -sticky nsw
	    grid [scrollbar $win.scroll -command "$win.c yview"] \
		    -row 1 -column 1 -sticky ns
	    grid columnconfigure $win 0 -weight 1
	    grid rowconfigure $win 1 -weight 1
	    set reflist(select_$graph) {}
	    frame $win.c.fr
	    $win.c create window 0 0 -anchor nw -window $win.c.fr 
	}

	raise $win
	# generate the reflection vector name
	set vec refposvec$graph
	regsub -all {\.} $vec _ vec
	# get the reflection tolerance (2% of the x-axis range)
	set lim [$graph xaxis limits]
	set tol [expr {0.02 * abs([lindex $lim 1] - [lindex $lim 0])}]
	set posmin [expr {$pos - $tol}]
	set posmax [expr {$pos + $tol}]
	foreach ref [$vec search $posmin $posmax] {
	    if {[lsearch -exact $reflist(select_$graph) $ref] == -1} {
		lappend reflist(select_$graph) $ref
		set row [llength $reflist(select_$graph)]
		foreach {val hkl ph d} [lindex $reflist($graph) $ref] {}
		foreach {h k l} $hkl {}
		if {$val < 1} {
		    set val [format %.5f $val]
		} else {
		    set val [format %.4f $val]
		}
		grid [label $win.c.fr.val$row -text $val] -row $row -column 0
		grid [label $win.c.fr.h$row -text $h] -row $row -column 1
		grid [label $win.c.fr.k$row -text $k] -row $row -column 2
		grid [label $win.c.fr.l$row -text $l] -row $row -column 3
		grid [label $win.c.fr.ph$row  -text $ph ] -row $row -column 4
		grid [checkbutton $win.c.fr.sel$row -width 4 -anchor e \
			-command "HighlightHKL $graph" \
			-variable reflist(${graph}-$ref)] -row $row -column 5
		set reflist(${graph}-$ref) 0
	    }
	}
	HighlightHKL $graph
    }
    # queue a resize if not already in the works
    if {! $reflist(ResizePending)} {
	set reflist(ResizePending) 1
	after idle "SizeHKLwin $win"
    }
}

# sort selected reflection list
proc SortHKL {opt win graph} {
    global reflist
    eval destroy [winfo children $win.c.fr]
    set row 0
    foreach ref $reflist(select_$graph) {
	foreach {val hkl ph d} [lindex $reflist($graph) $ref] {}
	if {$opt == "val"} {
	    lappend sortlist [list $ref $val]
	} elseif {$opt == "h"} {
	    foreach {h k l} $hkl {}
	    lappend sortlist [list $ref $h]
	} elseif {$opt == "k"} {
	    foreach {h k l} $hkl {}
	    lappend sortlist [list $ref $k]
	} elseif {$opt == "l"} {
	    foreach {h k l} $hkl {}
	    lappend sortlist [list $ref $l]
	} elseif {$opt == "phase"} {
	    lappend sortlist [list $ref $ph]
	}
    }
    if {$opt == "val"} {
	set type -real
    } elseif {$opt == "phase"} {
	set type -ascii
    } else {
	set type -integer
    }
    foreach item [lsort -index 1 $type $sortlist] {
	set ref [lindex $item 0]
	incr row
	foreach {val hkl ph d} [lindex $reflist($graph) $ref] {}
	foreach {h k l} $hkl {}
	if {$val < 1} {
	    set val [format %.5f $val]
	} else {
	    set val [format %.4f $val]
	}
	grid [label $win.c.fr.val$row -text $val] -row $row -column 0
	grid [label $win.c.fr.h$row -text $h] -row $row -column 1
	grid [label $win.c.fr.k$row -text $k] -row $row -column 2
	grid [label $win.c.fr.l$row -text $l] -row $row -column 3
	grid [label $win.c.fr.ph$row  -text $ph ] -row $row -column 4
	grid [checkbutton $win.c.fr.sel$row  -width 4 -anchor e \
		-command "HighlightHKL $graph" \
		-variable reflist(${graph}-$ref)] -row $row -column 5
    }
    # queue a resize if not already in the works
    if {! $reflist(ResizePending)} {
	set reflist(ResizePending) 1
	after idle "SizeHKLwin $win"
    }
}

# resize the reflection table
proc SizeHKLwin {win} {
    update

    # resize is now in progress, allow another to be queued if needed
    global reflist
    set reflist(ResizePending) 0

    foreach col {0 1 2 3 4 5} w {val h k l ph sel} {
	set wid  [winfo width $win.a.$w]
	set wid1 [winfo width $win.c.fr.${w}1]
	if {$wid1 > $wid} {set wid $wid1}
	grid columnconfig $win.a $col -minsize $wid -pad 5
	grid columnconfig $win.c.fr $col  -minsize $wid -pad 5
    }
    # resize the canvas & scrollbar
    update
    set sizes [grid bbox $win.c.fr]
    $win.c config -scrollregion $sizes -width [lindex $sizes 2]
    set hgt [lindex $sizes 3]
    # set the maximum height for the canvas from the frame
    set maxheight [$win.c cget -height]

    # use the scroll for BIG constraint lists
    if {$hgt > $maxheight} {
	grid $win.scroll -sticky ns -column 1 -row 1
    } else {
	grid forget $win.scroll
    }
}

# Mark reflections with a line and/or label
proc HighlightHKL {graph} {
    global reflist blt_version plot refl
    # workaround bug in BLT 2.3 where Inf does not work for text markers
    if {$blt_version == 2.3} {
	set ycen [lindex [$plot yaxis limits] 1]
    } else  {
	set ycen Inf
    }
    eval $graph marker delete [$graph marker names hkl*]
    foreach ref $reflist(select_$graph) {
	if {$reflist(${graph}-$ref)} {
	    foreach {val hkl ph d} [lindex $reflist($graph) $ref] {}
	    set phnum [lsearch $refl(phaselist) $ph]
	    set c $plot(refcolor$phnum)
	    if {$reflist(label)} {
		$graph marker create text -coords "$val $ycen" \
			-rotate 90 -text $hkl -anchor n -bg "" -name hkllbl$ref
	    }
	    if {$reflist(line)} {
		$graph marker create line -coords "$val -Inf $val Inf" \
			-name hklln$ref -outline $c
	    }
	}
    }
}

#-------------------------------------------------------------------------
# export current plot to Grace
#-------------------------------------------------------------------------
proc exportPlotGrace {parent} {
    global tcl_platform plot argv
    catch {toplevel .export}
    raise .export
    eval destroy [winfo children .export]
    set col 5
    grid [label .export.l2 -text "Plot from Window #"] \
		-row 0 -column 1 -sticky ew
    set menu [tk_optionMenu .export.m1 plot(graph) x]
    grid .export.m1 -column 2 -row 0 -sticky w
    if {[lsearch $plot(plotmenulist) $menu] == -1} {
	lappend plot(plotmenulist) $menu
    }
    if {[SetPlotLists] == 0} {
	destroy .export
	MyMessageBox -parent $parent -title "Export problem" \
		-message "Sorry, No plots to export" \
		-icon warning -type {"Oh, well"} -default "oh, well"
	return
    }
    grid [label .export.1a -text Title:] -column 1 -row 1
    set block $plot(block)
    global $block
    set blockname [set ${block}(data_)]
    set plot(title) "CIF $argv, block $blockname"
    grid [entry .export.1b -width 60 -textvariable plot(title)] \
	    -column 2 -row 1 -columnspan 4
    grid [label .export.2a -text Subtitle:] -column 1 -row 2
    grid [entry .export.2b -width 60 -textvariable plot(subtitle)] \
	    -column 2 -row 2 -columnspan 4
    grid [button .export.c -text "Close" \
	    -command "set plot(export) 0; destroy .export"] \
	    -column [incr col -1] -row 4
    if {$tcl_platform(platform) == "unix" && [auto_execok xmgrace] != ""} {
	grid [button .export.d -text "Export & \nstart grace" \
	    -command "set plot(export) 1; destroy .export"] \
		-column [incr col -1] -row 4
    } else {
	grid [button .export.d -text "Export & \nstart grace" \
	    -state disabled] \
		-column [incr col -1] -row 4
    }
    grid [button .export.e -text "Export" \
	    -command "set plot(export) 2; destroy .export"] \
	    -column [incr col -1] -row 4
    tkwait window .export
    if {$plot(export) == 0} return
    set file [tk_getSaveFile -title "Select output file" -parent $parent \
	    -defaultextension .agr -filetypes {{"Grace ASCII input" .agr}}]
    if {$file == ""} return
    if {[catch {
	set fp [open $file w]
	set i $plot(graph)
	incr i -1
	puts $fp [output_grace .plot$i.g $plot(title) $plot(subtitle)]
	close $fp
    } errmsg]} {
	MyMessageBox -parent $parent -title "Export Error" \
		-message "An error occured during the export: $errmsg" \
		-icon error -type Ignore -default ignore
	return
    }

    if {$plot(export) == 1} {
	set err [catch {exec xmgrace $file &} errmsg]
	if $err {
	MyMessageBox -parent $parent -title "Grace Error" \
		-message "An error occured launching grace (xmgrace): $errmsg" \
		-icon error -type Ignore -default ignore
	}
    } else {
	MyMessageBox -parent $parent -title "OK" \
		-message "File $file created" \
		-type OK -default ok
    }
}
#-------------------------------------------------------------------------
# export current plot to (crummy) postscript
#-------------------------------------------------------------------------
proc exportPlotPostScript {parent} {
    global tcl_platform plot argv
    catch {toplevel .export}
    raise .export
    eval destroy [winfo children .export]
    set col 5
    grid [label .export.l2 -text "Plot from Window #"] \
		-row 0 -column 1 -sticky ew
    set menu [tk_optionMenu .export.m1 plot(graph) x]
    grid .export.m1 -column 2 -row 0 -sticky w
    if {[lsearch $plot(plotmenulist) $menu] == -1} {
	lappend plot(plotmenulist) $menu
    }
    if {[SetPlotLists] == 0} {
	destroy .export
	MyMessageBox -parent $parent -title "Export problem" \
		-message "Sorry, No plots to export" \
		-icon warning -type {"Oh, well"} -default "oh, well"
	return
    }
    grid [button .export.c -text "Close" \
	    -command "set plot(export) 0; destroy .export"] \
	    -column [incr col -1] -row 4
    grid [button .export.e -text "Export" \
	    -command "set plot(export) 2; destroy .export"] \
	    -column [incr col -1] -row 4
    tkwait window .export
    if {$plot(export) == 0} return
    if {[catch {
	set file [tk_getSaveFile -title "Select output file" -parent $parent \
	    -defaultextension .ps -filetypes {{PostScript .ps}}]
	if {$file == ""} return
	set i $plot(graph)
	incr i -1
	.plot$i.g postscript output $file
    } errmsg]} {
	MyMessageBox -parent $parent -title "Export Error" \
		-message "An error occured during the export: $errmsg" \
		-icon error -type Ignore -default ignore
	return
    } else {
	MyMessageBox -parent $parent -title "OK" \
		-message "File $file created" \
		-type OK -default ok
    }
}


# tcl code that attempts to duplicate a BLT graph in XMGRACE
# (see http://plasma-gate.weizmann.ac.il/Grace/)
# this was written by John Cowgill and later hacked by Brian Toby
# to deal with un-recognized colors, export markers, warn on old BLT versions
# & brace expressions (seems faster?)

proc output_grace { graph_name "title {}" "subtitle {}"} {
    global blt_version
    # trap pre 2.4 BLT versions, where options have different names
    # but beware, really old versions of blt don't have a version number
    if [catch {set blt_version}] {set blt_version 0}
    if {$blt_version <= 2.3 || $blt_version == 8.0} {
	# version 8.0 is ~same as 2.3
	tk_dialog .tooOld "Old BLT" \
		"Sorry, you are using a version of BLT that is too old for this routine" \
		"" 0 OK
	return
    }
    set element_count 0

    # define translation tables
    array set grace_colormap {
	black 1 red 2 green 3 blue 4 yellow 5 brown 6 gray 7 purple 8 \
		cyan 9 magenta 10 orange 11
    }
    array set grace_symbols {
	none 0 circle 1 square 2 diamond 3 triangle 4 arrow 6 plus 8 splus 8 \
		cross 9 scross 9
    }
    
    # general header stuff
    set output_string "# Grace project file\n#\n@version 50010\n"
    
    # loop through each element in the graph but reverse order, so that
    # elements on the bottom are done first
    set element_list [$graph_name element names] 
    set index [llength $element_list]
    while {[incr index -1] >= 0} {
	set element_name [lindex $element_list $index]
	set element_cmd "$graph_name element cget $element_name"
	
	# get xy data for this element
	set data_list [eval $element_cmd -data]
	
	#if there is no data, skip this set as Grace does not like null sets
	if {[llength $data_list] == 0} continue

	# write the legend name for this element
	append output_string "@s$element_count legend \"" \
		[eval $element_cmd -label] "\"\n"

	# get the color and symbol type for this element
	set color_data 1
	catch {
	    set color_data $grace_colormap([eval $element_cmd -color])
	}
	append output_string "@s$element_count line color $color_data\n" \
		"@s$element_count errorbar color $color_data\n" \
		"@s$element_count symbol color $color_data\n"
	set symbol_data 1
	catch {
	    set symbol_data $grace_symbols([eval $element_cmd -symbol])
	}
	append output_string "@s$element_count symbol $symbol_data\n"
	# fill defaults to symbol color
	catch {
	    set color_data $grace_colormap([eval $element_cmd -fill])
	}
	append output_string "@s$element_count symbol fill color $color_data\n"

	# get element symbol/line width/size settings
	set size_data [eval $element_cmd -linewidth]
	append output_string \
		"@s$element_count linewidth $size_data\n" \
		"@s$element_count symbol linewidth $size_data\n"
	# turn off the line, if the width is zero
	if {$size_data == 0} {
	    append output_string \
		    "@s$element_count line type 0\n" 
	}

	# approximate the BLT size in grace
	set size_data 1
	catch {
	    set size_data [expr {[eval $element_cmd -pixels]/15.0}]
	}
	append output_string "@s$element_count symbol size $size_data\n" \
		"@s$element_count symbol fill pattern 1\n"

	# check if this element is hidden or not
	set hidden_data [eval $element_cmd -hide]
	if {[string compare "1" $hidden_data] == 0} {
	    append output_string "@s$element_count hidden true\n"
	} else {
	    append output_string "@s$element_count hidden false\n"
	}

	# check to see if there is -edata defined for this element
	# should work for versions of BLT that do not support -edata
	if {[catch \
		"$graph_name element configure $element_name -edata" edata_list] || \
		[string compare "" [lindex $edata_list 4]] == 0} {
	    # no error data present, just use xy data
	    append output_string "@s$element_count errorbar off\n@type xy\n"
	    set max [expr {[llength $data_list] / 2}]
	    for {set i 0} {$i < $max} {incr i} {
		append output_string [lindex $data_list [expr {2*$i}]] " " \
			[lindex $data_list [expr {2*$i + 1}]] "\n"
	    }
	} else {
	    # error data present, check for error vector
	    set edata_list [lindex $edata_list 4]
	    if {[llength $edata_list] == 1} {
		# found a vector name instead of a list, so get the values
		set edata_list [$edata_list range 0 end]
	    }
	    # get xy data for this element
	    set data_list [eval $element_cmd -data]
	    set max [expr {[llength $data_list] / 2}]
	    if {[llength $edata_list] >= [expr {[llength $data_list] * 2}]} {
		append output_string \
			"@s$element_count errorbar on\n@type xydxdxdydy\n"
		for {set i 0} {$i < $max} {incr i} {
		    append output_string [lindex $data_list  [expr {2*$i + 0}]] " " \
			    [lindex $data_list  [expr {2*$i + 1}]] " " \
			    [lindex $edata_list [expr {4*$i + 2}]] " " \
			    [lindex $edata_list [expr {4*$i + 3}]] " " \
			    [lindex $edata_list [expr {4*$i + 0}]] " " \
			    [lindex $edata_list [expr {4*$i + 1}]] "\n"
		}
	    } else {
		append output_string \
			"@s$element_count errorbar on\n@type xydy\n"
		for {set i 0} {$i < $max} {incr i} {
		    append output_string [lindex $data_list [expr {2*$i}]] " " \
			    [lindex $data_list [expr {2*$i + 1}]] " " \
			    [lindex $edata_list $i] "\n"
		}
	    }
	}
	append output_string "&\n"
	incr element_count
    }

    # general graph header stuff
    append output_string "@with g0\n"
    
    # get x and y axis limits
    foreach v {x y} {
	set limit_data [$graph_name ${v}axis limits]
	set ${v}min [lindex $limit_data 0]
	set ${v}max [lindex $limit_data 1]
	append output_string "@world ${v}min [set ${v}min]\n"
	append output_string "@world ${v}max [set ${v}max]\n"
    }
    
    # get legend information from graph
    set legend_data [lindex [$graph_name legend configure -hide] 4]
    if {[string compare "1" $legend_data] == 0} {
	append output_string "@legend off\n"
    } else {
	append output_string "@legend on\n"
    }

    # get title of graph
    if {$title == ""} {
	set title [$graph_name cget -title]
    }
    append output_string \
	    "@title \"$title\"\n" \
	    "@subtitle \"$subtitle\"\n"
    
    # get labels for x and y axes
    foreach z {x y} {
	set axistitle [$graph_name ${z}axis cget -title]
	set ticklist [$graph_name ${z}axis cget -majorticks]
	set tickspace [expr {[lindex $ticklist 1] - [lindex $ticklist 0]}]
	set minorticks [expr {$tickspace / (1 + \
		[llength [$graph_name ${z}axis cget -minorticks]])}]
	append output_string \
		"@${z}axis label \"$axistitle\"\n" \
		"@${z}axis tick major $tickspace\n" \
		"@${z}axis tick minor $minorticks\n"
    }
    
    # check for log scale on either axis
    set log_data [lindex [$graph_name xaxis configure -logscale] 4]
    if {[string compare "1" $log_data] == 0} {
	append output_string "@xaxes scale Logarithmic\n"
    }
    set log_data [lindex [$graph_name yaxis configure -logscale] 4]
    if {[string compare "1" $log_data] == 0} {
	append output_string "@yaxes scale Logarithmic\n"
    }

    # now get graph markers
    foreach m [$graph_name marker names] {
	if {[$graph_name marker type $m] == "line"} {
	    set coords [$graph_name marker cget $m -coords]
	    if {[$graph_name marker cget $m -dashes] == {}} {
		set linestyle 1
	    } else {
		set linestyle 3
	    }
	    set color_data 1
	    catch {
		set color_data $grace_colormap([$graph_name marker cget $m -outline])
	    }

	    if {[lindex $coords 0] < $xmin || [lindex $coords 0] > $xmax} \
		    continue 
	    regsub -all -- "\\+Inf" $coords $ymax coords
	    regsub -all -- "-Inf" $coords $ymin coords
	    while {[llength $coords] >= 4} {
		set c [lindex $coords 0]
		foreach c1 [lrange $coords 1 3] {append c ", $c1"}
		append output_string \
			"@with line\n" \
			"@ line on\n@ line loctype world\n@ line g0\n" \
			"@ line $c\n" \
			"@ line linewidth 1.0\n@ line linestyle $linestyle\n" \
			"@ line color $color_data\n@ line arrow 0\n" \
			"@line def\n"
		set coords [lrange $coords 2 end]
	    }
	} elseif {[$graph_name marker type $m] == "text"} {
	    set coords [$graph_name marker cget $m -coords]
	    # leave a 5% margin for markers on plot limits
	    set aymax [expr {$ymax - 0.05 * ($ymax - $ymin)}]
	    set aymin [expr {$ymin + 0.05 * ($ymax - $ymin)}]
	    regsub -all -- "\\+Inf" $coords $aymax coords
	    regsub -all -- "-Inf" $coords $aymin coords	
	    set c "[lindex $coords 0], [lindex $coords 1]"
	    set text [$graph_name marker cget $m -text]
	    set just [$graph_name marker cget $m -anchor]
	    if {[string range $just 0 0] == "c"} {
		set center 2
	    } elseif {[string range $just 0 0] == "n"} {
		set center 10
	    } elseif {[string range $just 0 0] == "e"} {
		# is this correct?
		set center 0
	    } else {
		set center 1
	    }
	    set color_data 1
	    catch {
		set color_data $grace_colormap([$graph_name marker cget $m -fg])
	    }
	    set angle [$graph_name marker cget $m -rotate]

	    append output_string \
		    "@with string\n" \
		    "@ string on\n@ string loctype world\n@ string g0\n" \
		    "@ string color $color_data\n@ string rot $angle\n" \
		    "@ string just $center\n" \
		    "@ string $c\n@ string def \"$text\"\n"
	}
    }    
    return $output_string
}
#-------------------------------------------------------------------------
# export current plot to a CSV file
#-------------------------------------------------------------------------
proc exportPlotSpreadsheet {parent} {
    global tcl_platform plot argv
    catch {toplevel .export}
    raise .export
    eval destroy [winfo children .export]
    set col 5
    grid [label .export.l2 -text "Plot from Window #"] \
		-row 0 -column 1 -sticky ew
    set menu [tk_optionMenu .export.m1 plot(graph) x]
    grid .export.m1 -column 2 -row 0 -sticky w
    if {[lsearch $plot(plotmenulist) $menu] == -1} {
	lappend plot(plotmenulist) $menu
    }
    if {[SetPlotLists] == 0} {
	destroy .export
	MyMessageBox -parent $parent -title "Export problem" \
		-message "Sorry, No plots to export" \
		-icon warning -type {"Oh, well"} -default "oh, well"
	return
    }
    if {[catch {set plot(csvfmt)}]} {set plot(csvfmt) csv}
    grid [radiobutton .export.1 -text "Comma separated variables" \
	    -value csv -variable plot(csvfmt)] \
	    -column 0 -columnspan 3 -row 1 -sticky w
    grid [radiobutton .export.2 -text "Tab separated variables" \
	    -value tab -variable plot(csvfmt)] \
	    -column 0 -columnspan 3 -row 2 -sticky w
    grid [button .export.c -text "Close" \
	    -command "set plot(export) 0; destroy .export"] \
	    -column 2 -row 4
    grid [button .export.e -text "Export" \
	    -command "set plot(export) 2; destroy .export"] \
	    -column 1 -row 4
    tkwait window .export
    if {$plot(export) == 0} return
#    set file x.csv
    set file [tk_getSaveFile -title "Select output file" -parent $parent \
	    -defaultextension .csv \
	    -filetypes {{"Comma separated variables" .csv}}]
    if {$file == ""} return
    if {[catch {
	set fp [open $file w]
	set i $plot(graph)
	incr i -1
	output_csv .plot$i.g $plot(csvfmt) $fp
	close $fp
    } errmsg]} {
	MyMessageBox -parent $parent -title "Export Error" \
		-message "An error occured during the export: $errmsg" \
		-icon error -type Ignore -default ignore
	return
    }

    MyMessageBox -parent $parent -title "OK" \
	    -message "File $file created" \
	    -type OK -default ok
}

# tcl code to dump the contents of a BLT graph in a file
# based on output_grace by John Cowgill
proc output_csv {graph_name fmt fp} {
    global blt_version
    # trap pre 2.4 BLT versions, where options have different names
    # but beware, really old versions of blt don't have a version number
    if [catch {set blt_version}] {set blt_version 0}
    if {$blt_version <= 2.3 || $blt_version == 8.0} {
	# version 8.0 is ~same as 2.3
	tk_dialog .tooOld "Old BLT" \
		"Sorry, you are using a version of BLT that is too old for this routine" \
		"" 0 OK
	return
    }
    set element_count 0

    # define field separator
    if {$fmt == "csv"} {
	set sep ","
    } else {
	set sep \t
    }

    # get title of graph
    puts $fp "title:${sep}[$graph_name cget -title]"
	
    # get x and y axis limits & labels
    foreach v {x y} {
	set limit_data [$graph_name ${v}axis limits]
	set ${v}min [lindex $limit_data 0]
	set ${v}max [lindex $limit_data 1]
	puts $fp "${v}-axis label:${sep}[$graph_name ${v}axis cget -title]"
	puts $fp "${v}-axis range:${sep}[lindex $limit_data 0]${sep}[lindex $limit_data 1]"
    }

    # loop through each element in the graph but reverse order, so that
    # elements on the bottom are done first
    set element_list [$graph_name element names] 
    set index [llength $element_list]
    set i 0
    set variablelist {}
    set headers {}
    while {[incr index -1] >= 0} {
	set element_name [lindex $element_list $index]
	set element_cmd "$graph_name element cget $element_name"
	
	# get xy data for this element
	set data_list [eval $element_cmd -data]
	
	#if there is no data, skip this set
	if {[llength $data_list] == 0} continue
	incr i
	
	# save the legend name for this element
	set lbl [eval $element_cmd -label]

	# save xy data
	set f 1
	set data(${i}_x) {}
	set data(${i}_y) {}
	lappend variablelist data(${i}_x) data(${i}_y)
	append headers "x-${lbl}${sep}y-${lbl}${sep}"
	foreach item $data_list {
	    if {$f} {
		lappend data(${i}_x) $item
		set f 0
	    } else {
		lappend data(${i}_y) $item
		set f 1
	    }
	}
	
	# check to see if there is -edata defined for this element
	# should work for versions of BLT that do not support -edata
	if {[catch \
		"$graph_name element configure $element_name -edata" edata_list] || \
		[string compare "" [lindex $edata_list 4]] == 0} {
	    # no error data present, just use xy data
	    set data(${i}_ey) ""
	} else {
	    # error data present, check for error vector
	    set edata_list [lindex $edata_list 4]
	    if {[llength $edata_list] == 1} {
		# found a vector name instead of a list, so get the values
		set edata_list [$edata_list range 0 end]
	    }
	    set data(${i}_ey) ""
	    # get xy data for this element
	    set data_list [eval $element_cmd -data]
	    set max [expr {[llength $data_list] / 2}]
	    set data(${i}_ey) ""
	    if {[llength $edata_list] >= [expr {[llength $data_list] * 2}]} {
		for {set i 0} {$i < $max} {incr i} {
		    lappend data(${i}_ey) [lindex $edata_list [expr {4*$i + 1}]]
		}
	    }
	    lappend variablelist data(${i}_ey)
	    append headers "sig(y)-${lbl}${sep}"
	}
    }
    # now get graph markers
    set i 0
    foreach m [$graph_name marker names] {
	if {[$graph_name marker type $m] == "line"} {
	    if {$i == 0} {
		append headers "marker-x1${sep}marker-x2${sep}marker-y1${sep}marker-y2${sep}"
		set i 1
		foreach v {x1 y1 x2 y2} {
		    lappend variablelist data(${i}_marker$v)
		    set data(${i}_marker$v) {}
		}
	    }
	    set coords [$graph_name marker cget $m -coords]
	    if {[lindex $coords 0] < $xmin || [lindex $coords 0] > $xmax} \
		    continue 
	    regsub -all -- "\\+Inf" $coords $ymax coords
	    regsub -all -- "-Inf" $coords $ymin coords
	    while {[llength $coords] >= 4} {
		foreach c [lrange $coords 0 3] v {x1 y1 x2 y2} {
		    lappend data(${i}_marker$v) $c
		}
		set coords [lrange $coords 2 end]
	    }
	} elseif {[$graph_name marker type $m] == "text"} {
	    # at least for now, ignore text markers
	}
    }    
    puts $fp $headers
    set max 0
    foreach var $variablelist {
	set l [llength [set $var]]
	if {$max < $l} {set max $l}
    }
    for {set i 0} {$i < $max} {incr i} {
	set line {}
	foreach var $variablelist {
	    append line [lindex [set $var] $i] $sep
	}
	puts $fp $line
    }
    return
}


# for development -- recreate a menu
#set i 1
#while {[$blcksel.a.plot.menu.export index end] != 0} {
#    $blcksel.a.plot.menu.export delete 1
#}
#foreach w [info procs export*] {
#    set lbl [string range $w 6 end]
#    $blcksel.a.plot.menu.export add command -label "to $lbl" \
#	    -command "$w $blcksel"
#}

# make the new font size take effect
proc ChangeFont {font} {
    catch {
	SetTkDefaultOptions $font
	ResizeFont .
	.b.n compute_size
    }
}

proc SaveOptions {} {
    global CIF tcl_platform
    if {[catch {
	if {$tcl_platform(platform) == "windows"} {
	    set file ~/pdcifplot.cfg
	} else {
	    set file ~/.pdcifplot_cfg
	}
	set fp [open $file w]
	puts $fp "set CIF(dictfilelist) [list $CIF(dictfilelist)]"
	puts $fp "array set CIF {"
	foreach name {font ShowDictDups maxvalues} {
	    catch {
		puts $fp "\t$name \t[list $CIF($name)]"
	    }
	}
	foreach name [array names CIF dict_*] {
	    puts $fp "\t$name \t[list $CIF($name)]"
	}
	puts $fp "}"
	close $fp
	MyMessageBox -parent . -title "Saved settings" \
	    -message "Dictionary settings have been saved in file [file nativename $file]." \
	    -icon "info" -type OK -default OK
    } errmsg]} {
	set ans [MyMessageBox -parent . -title "Save settings error" \
		-message "Error writing saved settings to file [file nativename $file].\n$errmsg \nOK to try deleting this file?" \
	    -icon error -type {Delete Cancel} -default delete]
	if {$ans == "delete"} {file delete -force $file}
    }
}

proc ScanBlocks {blcksel frame} {
    global plot argv xdata ydata
    wm title $blcksel "pdCIF Plotter: file $argv"
    wm title $frame "pdCIF Plotter: file $argv"
    set blockbox $blcksel.canvas.fr
    eval destroy [winfo children $blcksel.canvas.fr]
    set row 0
    set col 0
    set i 0
    set plotable 0
    foreach n $plot(blocklist) {
	global $n
	incr i
	set blockname [set ${n}(data_)]
	pdClassifyData $n 1
	if {[llength [array names xdata]] > 0 && \
		[llength [array names ydata]]> 0} {
	    set state normal
	    incr plotable
	} else {
	    set state disabled
	}
	grid [radiobutton $blockbox.$i -text "$n $blockname" -value $n \
		-state $state \
		-variable plot(block) -command "SelectBlock $n"] \
		-sticky w -row [incr row] -column $col
	if {$row > 15} {
	    incr col
	    set row 0
	}
    }
    set plot(block) ""
    Disableplotting 1
    update idletasks
    set sizes [grid bbox $blockbox]
    $blcksel.canvas config -scrollregion $sizes -width 400 -height 250
    if {[lindex $sizes 3] < [$blcksel.canvas cget -height]} {
	grid forget $blcksel.yscroll
	$blcksel.canvas config -height [lindex $sizes 3]
    } else {
	grid $blcksel.yscroll -row 1 -column 2 -sticky ns
    }
    if {[lindex $sizes 2] < [$blcksel.canvas cget -width]} {
	grid forget $blcksel.xscroll
	#$blcksel.canvas config -width [lindex $sizes 2]
    } else {
	grid $blcksel.xscroll -row 2 -column 1 -sticky ew
    }
    update idletasks
    if {[llength $plot(blocklist)] == 1} {$blockbox.1 invoke}
    if {$plotable == 0} {
	set ans [MyMessageBox -parent $blcksel -title "No Data" \
		-message "File \"$argv\" does not contain any powder diffraction data. Nothing to plot." \
		-icon warning -type {Continue "Browse CIF"} -default "continue"]
	if {$ans == "browse cif"} {ShowCIFBrowser $blcksel.a.window.menu 2 $frame}
    }
}

proc LoadFile {blcksel filew frame} {
    global argv CIF plot tcl_platform
    if {$tcl_platform(platform) == "windows"} {
	set types {{"CIF data" ".cif"} {"IUCr Rietveld" .rtv}}
    } else {
	set types {{"CIF data" ".cif .CIF"} {"IUCr Rietveld" ".rtv .RTV"}}
    }
    set file [tk_getOpenFile -title "Select CIF" -parent $blcksel \
	    -defaultextension .cif -filetypes $types]
    if {$file == ""} {return}
    set argv $file
    wm withdraw $blcksel
    wm deiconify $filew
    update
    pleasewait "while loading CIF file" CIF(status) $filew {Quit exit}
    # need to parse the revised CIF
    foreach i $CIF(blocklist) {
	global block$i
	unset block$i
    }
    # destroy the text box as that is faster than deleting the contents
    destroy $CIF(txt) 
    grid [text $CIF(txt) -height 10 -width 80 -yscrollcommand "$filew.s set"] \
	-column 0 -row 0 -sticky news
    set CIF(maxblocks) [ParseCIF $CIF(txt) $argv]
    set CIF(blocklist) {}
    set plot(blocklist) {}
    global block0
    if {[array names block0] != ""} {
	set i 0
    } else {
	set i 1
    }
    for {} {$i <= $CIF(maxblocks)} {incr i} {
	lappend CIF(blocklist) $i
	lappend plot(blocklist) block$i
    }
    CIFBrowser $CIF(txt) $CIF(blocklist) 0 $frame
    ScanBlocks $blcksel $frame
    donewait
    wm withdraw $filew
    wm deiconify $blcksel
    raise $blcksel
    # work in the directory where the file is located
    catch {cd [file dirname $argv]}
}

proc MakeHelp {page}  {
    global scriptdir
    set url [file join $scriptdir doc $page]
    # urls need to be absolute, at least for -remote in UNIX
    if {[string index $url 0] == "."} {
	set url [file join [pwd] $url]
	regsub "/\./" $url "/" url
    }
    urlOpen $url
}

# browse a WWW page with URL. The URL may contain a #anchor
# On UNIX assume netscape is in the path or env(BROWSER) is loaded. 
# On Windows search the registry for a browser. Mac branch not tested.
# This is taken from http://mini.net/cgi-bin/wikit/557.html with many thanks
# to the contributers
proc urlOpen {url} {
    global env tcl_platform
    switch $tcl_platform(platform) {
	"unix" {
	    if {![info exists env(BROWSER)]} {
		set progs [auto_execok netscape]
		if {[llength $progs]} {
		    set env(BROWSER) [list $progs]
		}
	    }
	    if {[info exists env(BROWSER)]} {
		if {[catch {exec $env(BROWSER) -remote openURL($url)}]} {
		    # perhaps browser doesn't understand -remote flag
		    if {[catch {exec $env(BROWSER) $url &} emsg]} {
			error "Error displaying $url in browser\n$emsg"
		    }
		}
	    } else {
		MyMessageBox -parent . -title "No Browser" \
			-message "Could not find a browser. Netscape is not in path. Define environment variable BROWSER to be full path name of browser." \
			-icon warn
	    }
        }
        "windows" {
	    package require registry
	    # Look for the application under
	    # HKEY_CLASSES_ROOT
	    set root HKEY_CLASSES_ROOT

	    # Get the application key for HTML files
	    set appKey [registry get $root\\.html ""]

	    # Get the command for opening HTML files
	    set appCmd [registry get \
		    $root\\$appKey\\shell\\open\\command ""]

	    # Substitute the HTML filename into the command for %1
	    # or stick it on the end
	    if {[string first %1 $appCmd] != -1} {
		regsub %1 $appCmd $url appCmd
	    } else {
		append appCmd " " $url
	    }
	    
	    # Double up the backslashes for eval (below)
	    regsub -all {\\} $appCmd  {\\\\} appCmd
	    
	    # Invoke the command
	    eval exec $appCmd &
        }
        "macintosh" {
            if {0 == [info exists env(BROWSER)]} {
                set env(BROWSER) "Browse the Internet"
            }
            if {[catch {
                AppleScript execute\
                    "tell application \"$env(BROWSER)\"
                         open url \"$url\"
                     end tell
                "} emsg]
            } then {
                error "Error displaying $url in browser\n$emsg"
            }
        }
    }
}

set plot(window) 0
set plot(graph) {}
set plot(plotmenulist) {}
set plot(color) black
set plot(line) 1
set plot(symbol) none
set plot(entrynum) 0
set reflist(ResizePending) 0
#------- options ---------
# display reflections
set plot(reflections) 1
# subtract background (1)
set plot(bkgsub) 0
# offset background (1)
set plot(diffoffset) 0
# error bars on yobs (1)
set plot(errorbars) 0
# Intensity rescaling
#   0 don't apply
#   1 apply average
#   2 apply smoothed function
#   3 apply ymorm
set plot(normlbl) "Don't renormalize" 
set plot(applynorm) 0
set plot(autoticks) 1
# label "marked" reflections with a 
# ...hkl label (no)
set reflist(label) 0
# ...line (yes)
set reflist(line)  1
#--------------------------

wm withdraw $frame

set blcksel .choose
toplevel $blcksel
#set blockbox $blcksel.block
#grid [frame $blockbox] -column 1 -row 1 -sticky ew

grid [frame $blcksel.a -bd 4 -relief groove -class MenuFrame] \
	-column 1  -columnspan 3 -row 0 -sticky nsew
# File menu button
pack [menubutton $blcksel.a.file -text File -underline 0 \
	-menu $blcksel.a.file.menu] -side left
menu $blcksel.a.file.menu
$blcksel.a.file.menu add command -command "LoadFile $blcksel $filew $frame" \
	-label "Open" -underline 0

# get a list of files to export CIF contents
set exportmenu {}
set filelist [glob -nocomplain [file join $scriptdir CIFto*.tcl]]
foreach file $filelist {
    catch {
	source $file
	if {$exportmenu == ""} {
	    $blcksel.a.file.menu add cascade -label "Export to..." \
		    -menu $blcksel.a.file.menu.export
	    menu [set exportmenu $blcksel.a.file.menu.export]
	}
	$exportmenu add command -label $label -command $action
    }
}
$blcksel.a.file.menu add command -command {exit} \
	-label "Exit" -underline 1

# Plot menu button
pack [menubutton $blcksel.a.plot -text Plots -underline 0 \
	-menu $blcksel.a.plot.menu] -side left
menu $blcksel.a.plot.menu
set plot(plotmenu) $blcksel.a.plot.menu
$blcksel.a.plot.menu add command -label "Rietveld Plot" \
	-command "MakeRietveldBox .b"
$blcksel.a.plot.menu add command -label "Custom Plot" \
	-command "MakeCustomBox .b"
$blcksel.a.plot.menu add cascade -label "Export Plot" \
	-menu $blcksel.a.plot.menu.export
menu $blcksel.a.plot.menu.export
foreach w [info procs exportPlot*] {
    set lbl [string range $w 10 end]
    $blcksel.a.plot.menu.export add command -label "to $lbl" \
	    -command "$w $blcksel"
}

# Window menu button
pack [menubutton $blcksel.a.window -text Windows -underline 0 \
	-menu $blcksel.a.window.menu] -side left
menu $blcksel.a.window.menu
$blcksel.a.window.menu add command -label "Show CIF Contents" -underline 9 \
	-command "ShowCIFWindow $blcksel.a.window.menu 1 $filew $blcksel"
wm protocol $filew WM_DELETE_WINDOW \
	"ShowCIFWindow $blcksel.a.window.menu 1 $filew $blcksel"
$blcksel.a.window.menu add command -label "Show CIF Browser" -underline 9 \
	-command "ShowCIFBrowser $blcksel.a.window.menu 2 $frame"
wm protocol $frame WM_DELETE_WINDOW \
	"ShowCIFBrowser $blcksel.a.window.menu 2 $frame"
$frame.box.c config -command "ShowCIFBrowser $blcksel.a.window.menu 2 $frame"


# Options menu button
pack [menubutton $blcksel.a.opts -text Options -underline 0 \
	-menu $blcksel.a.opts.menu] -side left
menu $blcksel.a.opts.menu
set menubar $blcksel.a
$menubar.opts.menu add command -label "Select Dictionaries..." -underline 0 \
	-command "MakeDictSelect $blcksel"
$blcksel.a.opts.menu add cascade -menu $blcksel.a.opts.menu.font \
	-label "Screen font"
menu $blcksel.a.opts.menu.font 
foreach f {10 11 12 13 14 16 18 20 22} {
    $blcksel.a.opts.menu.font add radiobutton \
	    -command {ChangeFont $CIF(font)} \
	    -label $f -value $f -variable CIF(font) -font "Helvetica -$f"
}
$menubar.opts.menu add checkbutton -variable CIF(ShowDictDups) \
	-label "Show Duplicate Dict. defs."
$menubar.opts.menu add cascade -menu $menubar.opts.menu.maxitems \
	-label "Maximum data items"
menu $menubar.opts.menu.maxitems
foreach n {50000 100000 500000 1000000 5000000 10000000 50000000 100000000 0} \
	l {50K   100K   500K   1M      5M      10M      50M      100M      "no limit"} {
    $menubar.opts.menu.maxitems add radiobutton \
	    -label $l -value $n -variable CIF(maxvalues)
}

$menubar.opts.menu add command -label "Save options" -underline 0 \
	-command SaveOptions

# Help menu button
pack [menubutton $blcksel.a.help -text Help -underline 0 \
	-menu $blcksel.a.help.menu -width 15 -justify right -anchor e] \
	-side right 
menu $blcksel.a.help.menu
$blcksel.a.help.menu add command -label "About" -underline 0 \
	-command {tk_dialog .warn About "\
Program pdCIFplot\n\n\
B. Toby, NIST\nBrian.Toby@NIST.gov\n\n
Not subject to copyright\n\n\
Version: [lindex $RevisionNumber 1] ([lindex $RevisionDate 1])" {} 0 OK
}
$blcksel.a.help.menu add command -label "Web page" -underline 0 \
	-command {MakeHelp pdCIFplot.html}
if {![catch {package require tkcon} errmsg]} {
    $blcksel.a.help.menu add command -label "Open console" \
	-command {tkcon show}
} elseif {$tcl_platform(platform) == "windows"} {
    $blcksel.a.help.menu add command -label "Open console" \
	-command {console show}
}

grid columnconf $blcksel 1 -weight 1
grid [canvas $blcksel.canvas \
	-scrollregion {0 0 5000 1000} -width 400 -height 250 \
	-xscrollcommand "$blcksel.xscroll set" \
	-yscrollcommand "$blcksel.yscroll set"] \
	    -column 1 -row 1  -sticky nsew 
grid [scrollbar $blcksel.xscroll -orient horizontal \
	-command "$blcksel.canvas xview"] \
	-row 2 -column 1 -sticky ew
grid [scrollbar $blcksel.yscroll \
	-command "$blcksel.canvas yview"] \
	-row 1 -column 2 -sticky ns
grid columnconfigure $blcksel 1 -weight 0
grid rowconfigure $blcksel 1 -weight 1
grid rowconfigure $blcksel 2 -pad 5
set blockbox [frame $blcksel.canvas.fr]
$blcksel.canvas create window 0 0 -anchor nw -window $blockbox

grid [frame $blcksel.box] -column 1 -columnspan 3 -row 3 -sticky ew

wm protocol $blcksel WM_DELETE_WINDOW exit
grid columnconfig $blcksel.box 0 -weight 1
grid columnconfig $blcksel.box 2 -weight 1

grid [button $frame.box.d -text "Show CIF Definitions" \
	-command "ShowDefWindow $frame.box.d $defw"] \
	-column 2 -row 1 -sticky w
wm protocol $defw WM_DELETE_WINDOW "ShowDefWindow $frame.box.d $defw"

update
wm withdraw $blcksel
# center the CIF text window
wm withdraw $filew
set x [expr {[winfo screenwidth $filew]/2 - [winfo reqwidth $filew]/2 \
            - [winfo vrootx [winfo parent $filew]]}]
set y [expr {[winfo screenheight $filew]/2 - [winfo reqheight $filew]/2 \
	- [winfo vrooty [winfo parent $filew]]}]
wm geometry $filew +$x+$y
update
wm deiconify $filew

pleasewait "while loading CIF file" CIF(status) $filew {Quit exit}
update idletasks

set CIF(maxblocks) [ParseCIF $CIF(txt) $argv]
set CIF(blocklist) {}
if {[array names block0] != ""} {
    set i 0
} else {
    set i 1
}
for {} {$i <= $CIF(maxblocks)} {incr i} {
    lappend CIF(blocklist) $i
    lappend plot(blocklist) block$i
#    if {![catch {set block${i}(errors)} errmsg]} {
#	puts "Block $i ([set block${i}(data_)]) errors:"
#	puts "[set block${i}(errors)]"
#    }
}

if {$CIF(blocklist) != ""} {
    CIFOpenBrowser $frame
    wm title $frame "pdCIF Plotter: file $argv"
    CIFBrowser $CIF(txt) $CIF(blocklist) 0 $frame
}
donewait
wm withdraw $filew
wm deiconify $blcksel
raise $blcksel 
# work in the directory where the file is located
catch {cd [file dirname $argv]}

#--># scan through to find blocks with data
ScanBlocks $blcksel $frame

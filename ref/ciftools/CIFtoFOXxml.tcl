# define the information needed to list in the file menu
set action "MakeFoxBox .fox"
set label "Fox XML"

# make a selection window for exporting to a Fox XML file
proc MakeFoxBox {box} {
    global xdata ydata ymoddata yesd
    global plot
    set plot(warnings) -1

    catch {toplevel $box}
    wm title $box "Export to FOX"
    eval destroy [winfo children $box]

    # variables for possible use on xaxis
    global xaxisvars
    array set xaxisvars {
	_pd_proc_2theta_corrected "corrected 2Theta"
	_pd_proc_2theta_range_     "corrected 2Theta"
	_pd_meas_2theta_range_     2Theta
	_pd_meas_2theta_scan       2Theta
	_pd_proc_wavelength       "wavelength, A"
	_pd_proc_d_spacing        "d-space, A"
	_pd_proc_recip_len_Q      "Q, 1/A"
    }
    array set yobsvars {
	_pd_meas_counts_total     Counts
	_pd_meas_intensity_total  Intensity
	_pd_proc_intensity_net    "Corrected Intensity"
	_pd_proc_intensity_total  Intensity
    }
    array set ybckvars {
	_pd_proc_intensity_bkg_calc    "Fit background"
	_pd_proc_intensity_bkg_fix     "Fixed background"
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
	foreach item [array names ydata] {
	    if {$n != [llength $ydata($item)]} continue
	    if {[lsearch [array names yobsvars] $item] != -1} {
		lappend yobslist $item
	    }
	    if {[lsearch [array names ybckvars] $item] != -1} {
		lappend ybcklist $item
	    }
	}

	set yesdlist {}
	foreach item [array names yesd] {
	    if {$n != [llength $yesd($item)]} continue
	    if {[lsearch [array names yesdvars] $item] != -1} {
		lappend yesdlist $item
	    }
	}
	set b [$box.n insert end $n -text "Set $j: $n points"]
 	$box.n itemconfigure $n -raisecmd "InitFoxVars $b"
	grid rowconfig $b 99 -weight 1

        set row 0
	grid [label $b.a$row -text "CIF Data Item" -bg yellow] \
		    -row $row -column 1 -sticky ew

	foreach lbl {x-axis y(obs) sigma(y) y(bck)} \
		var  {xaxis  yobs   sigy    yback} {
	    incr row
	    grid [label $b.a$row -text $lbl -bg yellow] \
		    -row $row -column 0 -columnspan 1 -sticky ew
	    set $var [tk_optionMenu $b.$var plot($var) x]
	    grid $b.$var -row $row -column 1 -columnspan 1
	    $b.$var config -width 32
	}	    
	# add entries to x-axis menubutton
  	$xaxis delete 0 end
	foreach item $xaxislist {
	    $xaxis add radiobutton -variable plot(xaxis) -value $item \
		    -label "$item ($xaxisvars($item))"
	}

	# add some easily derived units

	# observed Y
	$yobs delete 0 end
	foreach item $yobslist {
	    $yobs add radiobutton -variable plot(yobs) -value $item \
		    -label "$item ($yobsvars($item))"
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

	grid [frame $b.par -bd 2 -relief groove] \
		-row [incr row] -column 0 -columnspan 2 -sticky w
	grid [label $b.par.1 -text "Dataset name:"] \
		-row 0 -column 0
	global plot
	if {[catch {set plot(projname)}]} {set plot(projname) "my dataset"}
	grid [entry $b.par.2 -textvariable plot(projname) -width 25] \
		-row 0 -column 1 -columnspan 3 -sticky w
	set plot(lambda) 0
	catch {
	    set plot(lambda) [lindex $xdata(_diffrn_radiation_wavelength) 0]
	}
	grid [label $b.par.3 -text "wavelength:"] \
		-row 1 -column 0
	grid [entry $b.par.4 -textvariable plot(lambda) -width 9] \
		-row 1 -column 1 -sticky w

	grid [label $b.par.5 -text "max:"] \
		-row 2 -column 0
	if {[catch {set plot(sinthmax_type)}]} {set plot(sinthmax_type) 1}
	if {[catch {set plot(sinthmax)}]} {set plot(sinthmax) 0.3}
	grid [entry $b.par.6 -textvariable plot(sinthmax) -width 9] \
		-row 2 -column 1  -sticky w
	grid [radiobutton $b.par.7 -variable plot(sinthmax_type) \
		-text sin(th)/lam -value 1 \
		-command {set plot(sinthmax) [expr $plot(sinthmax)/6.28]} \
		] -row 2 -column 2
	grid [radiobutton $b.par.8 -variable plot(sinthmax_type) \
		-text Q -value 6.28\
		-command {set plot(sinthmax) [expr $plot(sinthmax)*6.28]} \
		] -row 2 -column 3	
	grid [label $b.par.9 -text "# of Bkg points:"] \
		-row 3 -column 0
	if {[catch {set plot(nbkg)}]} {set plot(nbkg) 20}
	grid [entry $b.par.10 -textvariable plot(nbkg) -width 3] \
		-row 3 -column 1 -sticky w

	grid [frame $b.bot] \
		-row [incr row] -column 0 -columnspan 2 -sticky w
	grid columnconfig $b.bot 0 -weight 1
	grid [label $b.bot.note -fg red -text ""] \
		-row 0 -column 0 -columnspan 3
	grid [button $b.bot.b1 -text "Write" -command "MakeFoxfile $b"] \
		-row 1 -column 0 -sticky w
	grid [button $b.bot.b2 -text "Close" -command "destroy $box"] \
		-row 1 -column 1 -sticky w
    }
    set first [lindex [$box.n pages] 0]
    $box.n see $first
    $box.n raise $first
    $box.n compute_size
}
# initialize the plot variables used in a Rietveld plot
proc InitFoxVars {b} {
    global plot
    set flag 0
    foreach var {xaxis  yobs   yback   sigy} \
	    req {  2     1      0       1 } {
	set plot($var) "(select an option)"
	$b.$var config -state normal
	set menu [winfo children $b.$var]
	if {[$menu index end] == "none"} {
	    set plot($var) "(not available)"
	    $b.$var config -state disabled
	    if {$req} {incr flag $req}
	} elseif {[$menu index end] == 0} {
	    $menu invoke 0
	    $b.$var config -state disabled
	} else {
	    $menu invoke 0
	}
    }
    if {$flag >= 2} {
	$b.bot.b1 config -state disabled
	$b.bot.note config -text "Cannot be exported: Missing x or y data set"
    } else {
	$b.bot.b1 config -state normal
	$b.bot.note config -text ""
    }
}

# write the FOX XML file
proc MakeFoxfile {parent} {
    global plot xdata ydata ymoddata yesd
    global refl
    foreach var {xaxis  yobs} \
	    msg {"x-axis" y(obs)} {
	if {$plot($var) == "(select an option)"} {
	    incr plot(warnings)
	    if {$plot(warnings)} {
		MyMessageBox -parent $parent -title "Select Axis" \
		-message "Unable to produce a file.\nPlease select a data item for $msg" \
		-icon warning -type Continue -default continue
	    } else {
		bell
	    }
	    return
	}
    }
    set file [tk_getSaveFile -title "Select output file" -parent $parent \
	    -defaultextension .xml -filetypes {{"FOX XML file" .xml}}]
    if {$file == ""} return
    if {[catch {
	set fp [open $file w]
    } errmsg]} {
	MyMessageBox -parent $parent -title "Export Error" \
		-message "An error occured during the export: $errmsg" \
		-icon error -type Ignore -default ignore
	return
    }

    pleasewait "while computing values" "" $parent
    set xlist  {}
    set yobslist  {}
    set ybcklist  {}

    set utc [clock format [clock seconds] -gmt 1 -format "%Y-%m-%dT%H:%M:%S%Z"]
    puts $fp "<ObjCryst Date=\"$utc\">"
    puts $fp "  <PowderPattern Name=\"${plot(projname)}\">"
    FoxXMLputpar $fp 2ThetaZero 
    FoxXMLputpar $fp 2ThetaDisplacement
    FoxXMLputpar $fp 2ThetaTransparency
    puts $fp "  <Radiation>"
    FoxXMLputopt $fp Radiation Neutron
    FoxXMLputopt $fp Spectrum Monochromatic
    FoxXMLputpar $fp Wavelength $plot(lambda) \
	    [expr 0.9*$plot(lambda)]  [expr 1.1*$plot(lambda)]
    #  <LinearPolarRate>2.8026e-45</LinearPolarRate>
    puts $fp "  </Radiation>"
    puts $fp "  <MaxSinThetaOvLambda>[expr $plot(sinthmax)/$plot(sinthmax_type)]</MaxSinThetaOvLambda>"

    # process the x-axis
    set xlist {}
    global xaxisvars
    set unit $xaxisvars([set plot(xaxis)])
    # remove comma & remainder
    set unit [lindex [split $unit ,] 0]
    catch {
	set xlist $xdata([set plot(xaxis)])
    }
    catch {
	set ybcklist $ydata([set plot(yback)])
    }
    # compile a list of the y values
    catch {
	set yobslist $ydata([set plot(yobs)])
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

    puts $fp "   <PowderPatternBackground Name=\"\" Interpolation=\"Linear\">"
    puts $fp "\t<TThetaIntensityList>"
     set incr [expr {[set npts [llength $xlist]] / $plot(nbkg)}]
    for {set i 0} {$i < $npts} {incr i $incr} {
	puts $fp "\t[lindex $xlist $i] [lindex $ybcklist $i] 0"
    }
    puts $fp "\t</TThetaIntensityList>"
    puts $fp "   </PowderPatternBackground>"
    puts $fp {<PowderPatternComponent Scale="1" Name=""/>}

    set datalist {}
    foreach x $xlist y $yobslist sigy $siglist {
	lappend datalist [list $x $y $sigy]
    }
    set datalist [lsort -index 0 -real $datalist]
    set xmin [lindex [lindex $datalist 0] 0]
    set xmax [lindex [lindex $datalist end] 0]
    set xstepavg [expr {($xmax - $xmin) / ([llength $datalist]-1)}]
    puts $fp "    <IobsSigmaWeightList TThetaMin=\"${xmin}\" TThetaStep=\"${xstepavg}\">"
    set xsmin [set xsmax $xstepavg]
    set xprev {}
    foreach item $datalist {
	foreach {x y sigy} $item {}
	if {$xprev != ""} {
	    set xstep [expr {$x - $xprev}]
	    if {$xstep > $xsmax} {set xsmax $xstep}
	    if {$xstep < $xsmin} {set xsmin $xstep}
	}
	set xprev $x
	# make sure we have valid numbers
	if {[catch {expr $y}]} {set y 0; set sigy 1e10}
	if {[catch {expr $sigy}]} {set sigy 1e10}
	set w 1e-20
	catch {set w [expr {1./($sigy*$sigy)}]}
	puts $fp "\t${y} ${sigy} $w"
    }
    puts $fp "    </IobsSigmaWeightList>"

    puts $fp "  </PowderPattern>"
    puts $fp "</ObjCryst>"
    close $fp
    donewait
    if {$xstepavg/50. < ($xsmax-$xsmin)} {
	MyMessageBox -parent $parent -title "Not Fixed Step" \
		-message "File $file created.\n\nWarning, step sizes range from $xsmin to $xsmax.\nFOX requires fixed step size data. Using the approximate step size of $xstepavg" \
		-icon warning -type Continue -default continue
    } else {
	MyMessageBox -parent $parent -title "OK" \
		-message "File $file created" \
		-type OK -default ok
    }
}

proc FoxXMLputpar {fp name "value 0" "min -2.86479" "max 2.86479" "refine 0"} {
    puts $fp "\t<Par Refined=\"${refine}\" Limited=\"1\" Min=\"${min}\" Max=\"${max}\" Name=\"${name}\">${value}</Par>"
}
proc FoxXMLputopt {fp name choicename "choice 0"} {
    puts $fp "\t<Option Name=\"${name}\" Choice=\"${choice}\" ChoiceName=\"${choicename}\"/>"
}

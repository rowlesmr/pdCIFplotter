# A routine for editing CIF template file(s) adapted for specific
# use with GSAS2CIF. This program edits files template_*.cif or
# <expnam>_*.cif. If neither are available, it copies the template_*.cif 
# from the GSAS data directory ../data (relative to this file)
#

# $Id: fillcif.tcl,v 1.6 2005/02/24 20:54:12 toby Exp toby $

# this routine is intended for use within the EXPGUI program, but may be 
# useful for adaptation into other CIF preparation environments.
# Permission is granted by the author (Brian Toby) for reuse of any part 
# of this code.

# Prerequisites:
#  1) BWidget routines be available (tested with version 1.2.1)
#      These routines are included with EXPGUI
#
#  2) files browsecif.tcl & gsascmds.tcl must be in the same directory as 
#      this file (Included with EXPGUI)
#
#  3) The CIF core & powder dictionaries are included in the GSAS data 
#      directory (../data/), files cif_core_2.2.dic and cif_pd.dic
#      (Included with GSAS/EXPGUI distribution)
#
#  4) The GSAS2CIF template files (template_instrument.cif, 
#      template_phase.cif and template_publ.cif) are included in the GSAS data 
#      directory (../data/).
#      (Included with GSAS/EXPGUI distribution)

# required for starkit (does not hurt otherwise)
package require Tk

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

if {$tcl_version < 8.2} {
    tk_dialog .error {Old Tcl/Tk} \
	    "Sorry, the CIF Browser requires version 8.2 or later of the Tcl/Tk package. This is $tcl_version" \
	    warning 0 Sorry
    exit
}

if {[llength $argv] != 1} {
    set file [tk_getOpenFile -title "Select GSAS Experiment" -parent . \
	    -defaultextension EXP -filetypes {{"GSAS experiment" .EXP}}]
    if {$file == ""} {exit}
    set prefix [file root $file]
} else {
    set prefix $argv
}

if {[set dir [file dirname $prefix]] != ""} {
    cd $dir
    set prefix [file tail $prefix]
}
# used by some gsascmds routines
set expgui(scriptdir) $scriptdir
set expgui(gsasdir) [file dirname $expgui(scriptdir)]
set expgui(gsasexe) [file join $expgui(gsasdir) exe]
set expgui(docdir) [file join $expgui(scriptdir) doc]
# location for web pages, if not found locally
set expgui(website) www.ncnr.nist.gov/xtal/software/expgui

# where to find the BWidget program
lappend auto_path $scriptdir
# now look
if [catch {package require BWidget} errmsg] {
    tk_dialog .error {No BWidget} \
	    "Sorry, the CIF Browser requires the BWidget package." \
	    warning 0 Sorry
    exit
}

source [file join $scriptdir browsecif.tcl]
source [file join $scriptdir gsascmds.tcl]
bind . <Key-F1> "MakeWWWHelp gsas2cif.html filltemplate"

set CIF(filelist) [glob -nocomplain ${prefix}_*.cif]
if {$CIF(filelist) == ""} {
    set CIF(filelist) [glob -nocomplain template_*.cif]
}
if {$CIF(filelist) == ""} {
    set CIF(filelist) [glob -nocomplain [file join $scriptdir ../data template_*.cif]]
    if {$CIF(filelist) == ""} {
	MyMessageBox -parent . -title "No template files" \
	    -message "No CIF template files found. Cannot continue" \
		-icon error -type Quit -default quit
	exit
    }
    set ans [MyMessageBox -parent . -title "Copy template files?" \
	    -message "No CIF template files (template_*.cif or ${prefix}_*.cif) in the current directory. Copy standard templates from GSAS data directory?" \
	    -icon question -type {Copy Quit} -default copy]
    if {$ans == "quit"} {exit}
    eval file copy $CIF(filelist) .
    set CIF(filelist) [glob -nocomplain template_*.cif]
}


proc SaveCIFtoFile {} {
    global CIF
    set CIF(changes) 0
    set CIF(undolist) {}
    set CIF(redolist) {}
    # at least for the moment, keep the previous version
    file rename -force $CIF(lastCIFfilename) $CIF(lastCIFfilename).old
    set fp [open $CIF(lastCIFfilename) w]
    puts -nonewline $fp [$CIF(txt) get 1.0 end]
    close $fp
}

proc ConfirmDestroy {} {
    global CIF
    if {[CheckForCIFEdits]} return
    if {$CIF(changes) != 0 && $CIF(autosavetodisk)} {
	SaveCIFtoFile
    }
    if {$CIF(changes) != 0} {
	set ans [MyMessageBox -parent . -title "Discard Changes?" \
		-message "You have changed this CIF. Do you want to save or discard your changes?" \
		-icon question -type {Save Discard Cancel} -default Save]
	if {$ans == "save"} {
	    SaveCIFtoFile
	    destroy .
	} elseif {$ans == "discard"} {
	    destroy .
	}
    } else {
	destroy .
    }
}

proc NextCIFtemplate {} {
    global CIF CIFtreeindex
    if {[CheckForCIFEdits]} return
    set loopindex ""
    set pointer ""
    set block ""
    set dataname ""
    set nextpointer ""

    if {$CIF(lastShownItem) != ""} {
	set pointer [lindex $CIF(lastShownItem) 0]
	set block [lindex $pointer 0]
	set dataname [lindex $CIF(lastShownItem) 1]
    }
    if {[llength $pointer] == 2} {	
	set loopindex [$CIF(LoopSpinBox) getvalue]
    }
    # find the next template item in current file
    foreach {nextpointer nextdataname nextloopindex} \
	    [FindNextCIFQuestionMark $block $dataname $loopindex] {}
    if {$nextpointer != ""} {
	# got one
	showCIFbyDataname $nextpointer $nextdataname $nextloopindex
	# show the tree here
	catch {
	    $CIF(tree) see $CIFtreeindex([lindex $nextpointer 0]$nextdataname)
	}
	return
    }
    # go on to the next file
    if {$CIF(changes) != 0 && $CIF(autosavetodisk)} {
	SaveCIFtoFile
    }
    if {$CIF(changes) != 0} {
	set ans [MyMessageBox -parent . -title "Save Changes?" \
		-message "You have changed this CIF. Do you want to save your changes?" \
		-icon question -type {Save Cancel} -default Save]
	if {$ans == "save"} {
	    SaveCIFtoFile
	} else {
	    return
	}
    }
    # is there another file to look at?
    if {$CIF(CIFfilename) == [lindex $CIF(filelist) end]} {
	set ans [MyMessageBox -parent . -title "No remaining items" \
		-message "No template items from this point in the current file, scan from the beginning of the first file?" \
		-icon question -type {Yes Cancel} -default Cancel]
	if {$ans == "cancel"} return
	# go on to first file here
	set filelist $CIF(filelist)
    } else {
	# go on to next file here
	set filelist [lrange $CIF(filelist) [expr 1+[lsearch $CIF(filelist) $CIF(CIFfilename)]] end]
    }
    foreach CIF(CIFfilename) $filelist {
	ParseShowCIF $CIF(browserBox)
	foreach {nextpointer nextdataname nextloopindex} \
		[FindNextCIFQuestionMark $block $dataname $loopindex] {}
	if {$nextpointer != ""} {
	    showCIFbyDataname $nextpointer $nextdataname $nextloopindex
	    # show the tree here
	    catch {
		$CIF(tree) see $CIFtreeindex([lindex $nextpointer 0]$nextdataname)
	    }
	    return
	}
    }
    MyMessageBox -parent . -title "All done" \
	    -message "No ? fields found. All template items have been completed." \
	    -type OK -default OK
}

proc FindNextCIFQuestionMark {block dataname loopindex} {
    global CIF

    set blocklist {}
    foreach i $CIF(blocklist) {
	if {$block == "block$i"} {
	    set blocklist block$i
	} else {
	    lappend blocklist block$i
	}
    }

    set first -1
    foreach n $blocklist {
	global $n	
	incr first
	# compile a list of names then loops
	set namelist [lsort [array names $n _*]]
	set looplist [lsort [array names $n loop_*]]
	if {$looplist != ""} {set namelist [concat $namelist $looplist]}
	# make a list of data names in loops
	set loopednames {}
	foreach loop [array names $n loop_*] {
	    eval lappend loopednames [set ${n}($loop)]
	}

	# loop index, if needed
	set start 0
	# on the first pass
	if {$first == 0} {
	    set i [lsearch $namelist $dataname]
	    if {$i != -1} {
		# found the last entry -- is it looped?
		if {$loopindex == ""} {
		    incr i
		} else {
		    set start [expr 1 + $loopindex]
		}
		set namelist [lrange $namelist $i end]
	    }
	}
	# now start searching for an entry
	foreach name $namelist {
	    # skip over datanames in loops or in the ignore list
	    set match 0
	    foreach ignore $CIF(TemplateIgnoreList) {
		if {[string match $ignore $name]} {
		    set match 1
		    break
		}
	    }
	    if {$match} continue
	    if {[lsearch $loopednames $name] != -1} continue

	    if {[string range $name 0 4] != "loop_"} {
		set mark [set ${n}($name)]
		set value [string trim [StripQuotes [$CIF(txt) get $mark.l $mark.r]]]
		if {$value == "?"} {return "$n $name {}"}
	    } else {
		set looplist [set ${n}($name)]
		set looplength [llength [set ${n}([lindex $looplist 0])]]
		for {set i $start} {$i < $looplength} {incr i} {
		    foreach var $looplist {
			set mark [lindex [set ${n}($var)] $i]
			set value [string trim [StripQuotes [$CIF(txt) get $mark.l $mark.r]]]
			if {$value == "?"} {
			    return [list [list $n loop] $name $i]
			}
		    }
		}
	    }
	}
    }
}

proc ShowDefWindow {button window} {
    if {[lindex [$button cget -text] 0] == "Show"} {
	$button config -text "Hide CIF\nDefinitions"
	# this is an attempt to put the window under the browser
	set x [winfo x .]
	set y [expr 5 + [winfo y .] + [winfo height .]]
	wm geometry $window +$x+$y
	wm deiconify $window
    } else {
	$button config -text "Show CIF\nDefinitions"
	wm withdraw $window
    }
}
proc ShowCIFWindow {button window} {
    if {[lindex [$button cget -text] 0] == "Show"} {
	$button config -text "Hide CIF\nContents"
	# this is an attempt to put the window under the browser
	set x [winfo x .]
	set y [expr 5 + [winfo y .] + [winfo height .]]
	wm geometry $window +$x+$y
	wm deiconify $window
    } else {
	$button config -text "Show CIF\nContents"
	wm withdraw $window
    }
}

proc ParseShowCIF {frame} {
    global CIF
    # check for edits in progress
    if {[CheckForCIFEdits]} return
    # check for unsaved changes here
    if {$CIF(changes) != 0} {
	set ans [MyMessageBox -parent . -title "Discard Changes?" \
		-message "You have changed this CIF. Do you want to save or discard your changes?" \
		-icon question -type {Save Discard Cancel} -default Save]
	if {$ans == "save"} {
	    SaveCIFtoFile
	} elseif {$ans == "cancel"} {
	    set CIF(CIFfilename) $CIF(lastCIFfilename)
	    return
	}
    }
    set CIF(changes) 0
    set CIF(undolist) {}
    set CIF(redolist) {}

    $CIF(txt) configure -state normal
    $CIF(txt) delete 1.0 end
    $CIF(txt) configure -state disabled
    foreach i $CIF(blocklist) {
	global block$i
	unset block$i
    }
    set CIF(maxblocks) [ParseCIF $CIF(txt) $CIF(CIFfilename)]
    set CIF(lastCIFfilename) $CIF(CIFfilename)
    wm title . "CIF Browser: file $CIF(CIFfilename)"
	
    # make a list of blocks
    set CIF(blocklist) {}
    set errors {}
    global block0
    if {[array names block0] != ""} {
	set i 0
    } else {
	set i 1
    }
    for {} {$i <= $CIF(maxblocks)} {incr i} {
	lappend CIF(blocklist) ${i}
	if {![catch {set block${i}(errors)} errmsg]} {
	    append errors "Block $i ([set block${i}(data_)]) errors: [set block${i}(errors)]\n"
	}
	if {$errors != ""} {
	    MyMessageBox -parent . -title "CIF errors" \
		    -message "Note: file $CIF(CIFfilename) has errors.\n$errors" \
		    -icon error -type Continue -default continue
	}
    }

    if {$CIF(blocklist) != ""} {
	CIFBrowser $CIF(txt) $CIF(blocklist) "" $frame
    }
}

# create window/text widget for CIF file
catch {destroy [set file .file]}
toplevel $file
wm title $file "CIF file contents"
bind $file <Key-F1> "MakeWWWHelp gsas2cif.html filltemplate"

set CIF(txt) $file.t
grid [text $CIF(txt) -height 10 -width 80 -yscrollcommand "$file.s set"] \
	-column 0 -row 0 -sticky news
grid [scrollbar $file.s -command "$CIF(txt) yview"] -column 1 -row 0 -sticky ns
grid columnconfig $file 0 -weight 1
grid rowconfig $file 0 -weight 1
# hide it
wm withdraw $file

# create window/text widget for the CIF definition
catch {destroy [set defw .def]}
toplevel $defw
bind $defw <Key-F1> "MakeWWWHelp gsas2cif.html filltemplate"
wm title $defw "CIF definitions"
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

# is there a defined list of dictionary files?
if {[catch {set ::CIF(dictfilelist)}]} {
    set dictfilelist [glob -nocomplain \
			  [file join $::expgui(gsasdir) data *.dic]]
    foreach f $dictfilelist {
	lappend ::CIF(dictfilelist) $f
	set ::CIF(dict_$f) 1
    }
}
# load the initial CIF dictionaries
LoadDictIndices

# make frame for the CIF browser
wm title . "CIF Browser"
grid [set CIF(browserBox) [frame .top]] -column 0 -row 0 -sticky ew
grid [set box [frame .box]] -column 0 -row 1 -sticky ew

set filemenu [tk_optionMenu $box.file CIF(CIFfilename) ""]
$box.file config -width 25
$filemenu delete 0 end
foreach f $CIF(filelist) {
    $filemenu add radiobutton -value $f -label $f -variable CIF(CIFfilename) \
	    -command "ParseShowCIF $CIF(browserBox)"
}

set col -1
grid [label $box.lf -text "template\nfile:"] -column [incr col] \
	-row 1 -rowspan 2
grid $box.file	-column [incr col] -row 1 -rowspan 2 -sticky w
grid [button $box.next -text "Next ? in\ntemplate" \
	-command NextCIFtemplate] -column [incr col] -row 1 -rowspan 2
grid columnconfig $box $col -weight 1
incr col
grid [button $box.c -text Exit -command ConfirmDestroy] \
	-column [incr col] -row 1 -rowspan 2 -sticky w
grid columnconfig $box $col -weight 1

incr col
grid [button $box.f -text "Show CIF\nContents" \
	-command "ShowCIFWindow $box.f $file"] -column [incr col] \
	-row 1 -rowspan 2
grid [button $box.d -text "Show CIF\nDefinitions" \
	-command "ShowDefWindow $box.d $defw"] -column [incr col] \
	-row 1 -rowspan 2 -sticky w

incr col
grid [button $box.u -text "Undo" -command UndoChanges \
	-state disabled] \
	-column $col -row 1 -rowspan 2 -sticky w
incr col
grid [button $box.r -text "Redo" -command RedoChanges \
	-state disabled] \
	-column $col -row 1 -rowspan 2 -sticky w

incr col
grid [button $box.6 -text "Save" \
	-command SaveCIFtoFile -state disabled] -column $col \
	-row 1
grid [checkbutton $box.7b -text "Auto-Save" \
	-variable CIF(autosavetodisk)] -column $col -columnspan 2 \
	-row 2 -sticky w

grid [button $box.help -text Help -bg yellow \
	    -command "MakeWWWHelp gsas2cif.html filltemplate"] \
	    -column [incr col] -row 1 -rowspan 2 -sticky nw

set CIF(autosavetodisk) 0
set CIF(editmode) 1

wm protocol . WM_DELETE_WINDOW ConfirmDestroy
wm protocol $file WM_DELETE_WINDOW "ShowCIFWindow $box.f $file"
wm protocol $defw WM_DELETE_WINDOW "ShowDefWindow $box.d $defw"

trace variable CIF(changes) w "EnableSaveEdits $box.6"
proc EnableSaveEdits {w args} {
    global CIF
    if {$CIF(changes)} {
	$w config -state normal
    } else {
	$w config -state disabled
    }
}
trace variable CIF(undolist) w "EnableUndo $box.u undolist"
trace variable CIF(redolist) w "EnableUndo $box.r redolist"
proc EnableUndo {w var args} {
    global CIF
    if {[llength $CIF($var)] > 0} {
	$w config -state normal
    } else {
	$w config -state disabled
    }
}

set CIF(blocklist) {}
set CIF(CIFfilename) [lindex $CIF(filelist) 0]
CIFOpenBrowser $CIF(browserBox)
ParseShowCIF $CIF(browserBox)

#------- work in progress

set CIF(TemplateIgnoreList) {_journal_*}


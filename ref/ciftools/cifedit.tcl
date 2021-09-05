#!/bin/sh
# the next line restarts this script using wish found in the path\
exec wish "$0" "$@"
# If this does not work, change the #!/usr/bin/wish line below
# to reflect the actual wish location and delete all preceeding lines
#
# (delete here and above)
#!/usr/bin/wish
#
# $Id: cifedit.tcl,v 1.13 2005/03/01 20:51:26 toby Exp toby $
set RevisionNumber {$Revision: 1.13 $}
set RevisionDate {$Date: 2005/03/01 20:51:26 $}
# A routine for editing CIFs 
# 
# Prerequisites:
#  1) BWidget routines be available (tested with version 1.2.1)
#      if the BWidget routines are not in a subdirectory of where this
#      file is located & is not in the normal tcl auto_path, add the 
#      path below by uncommenting & updating the next line:
#      lappend auto_path /usr/local/tcltk/
#      e.g. use /usr/local/tcltk/ if the package is in /usr/local/tcltk/BWidget-1.2.1
#
#  2) file browsecif.tcl and opts.tcl must be in the same directory 
#     as this file
#
#  3) CIF dictionaries are expected to be found in subdirectory dict of the
#      where this file is located. The user can provide alternate locations
#      for CIF dictionaries, as well as decide which dictionaries will be used.

# Note the Maximum CIF size is set by this variable:
set CIF(maxvalues) 100000
# where CIF(maxvalues) is the number of data items (each value in a loop
# is counted). 
# 100,000 => 25Mb task size (Linux) & ~0.5Mb CIF
# use "set CIF(maxvalues) 0" to defeat the limit

# Note the maximum number of "rows" that can be displayed by selecting a row
# is set by this variable:
set CIF(maxRows) 100

# the maximum number of characters/line in CIF size is set by this variable:
set CIF(maxlinelength) 80

# location of dictionary files, overridden by ~/cifedit.cfg or ~/.cifedit_cfg
#set CIF(dictfilelist) {}

# display button bar by default
set CIF(ShowButtonBar) 1

# don't show overridden definitions by default
set CIF(ShowDictDups) 0

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

# where to find the BWidget program
lappend auto_path $scriptdir

source [file join $scriptdir browsecif.tcl]
source [file join $scriptdir opts.tcl]
# default font
set CIF(font) 14

if {$tcl_version < 8.2} {
    tk_dialog .error {Old Tcl/Tk} \
	    "Sorry, the CIF Editor requires version 8.2 or later of the Tcl/Tk package. This is $tcl_version" \
	    warning 0 Sorry
    exit
}

if [catch {package require BWidget}] {
    tk_dialog .error {No BWidget} \
	    "Sorry, CIFEDIT requires the BWidget package" \
	    warning 0 Sorry
    exit
}

# load saved dictionary/config info
if {[catch {
    if {$tcl_platform(platform) == "windows"} {
	set file ~/cifedit.cfg
    } else {
	set file ~/.cifedit_cfg
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
set CIF(txt) $filew.t
# shrink file viewer on small screens & add a scroll bar
set w 80 
if {[winfo screenwidth .] < 700} {set w 60}
grid [text $CIF(txt) -height 10 -width $w -yscrollcommand "$filew.s set" \
	-wrap none] -column 0 -row 0 -sticky news
grid [scrollbar $filew.s -command "$CIF(txt) yview"] \
	-column 1 -row 0 -sticky ns
if {[winfo screenwidth .] < 700} {
    grid [scrollbar $filew.sx -command "$CIF(txt) xview" \
	    -orient horizontal] -column 0 -row 1 -sticky ew
    $CIF(txt) config -xscrollcommand "$filew.sx set" 
}
grid columnconfig $filew 0 -weight 1
grid rowconfig $filew 0 -weight 1
grid [frame $filew.f] -column 0 -columnspan 2 -row 2 -sticky news
grid columnconfig $filew.f 4 -weight 1
grid [button $filew.f.edit -text "Open for Editing" \
	-command "EditCIFBox $filew.f.edit"] -column 0 -row 0
grid [button $filew.f.b -text "go to line:" \
	-command {MarkGotoLine $CIF(goto)}] -column 5 -row 0
grid [entry $filew.f.e -textvariable CIF(goto) -width 6] -column 6 -row 0
set CIF(goto) 1
bind $filew.f.e <Return> "$filew.f.b invoke"

# create window/text widget for the CIF definition
catch {destroy [set defw .def]}
toplevel $defw
wm title $defw "CIF definitions"
set CIF(defBox) $defw.t
# shrink definition viewer on small screens
set w 45
set h 18
if {[winfo screenwidth .] <= 800} {set w 35; set h 12}
grid [text $CIF(defBox) -width $w -height $h -xscrollcommand "$defw.x set" \
	-yscrollcommand "$defw.y set" -wrap word] -column 0 -row 0 -sticky news
grid [scrollbar $defw.y -command "$CIF(defBox) yview"] -column 1 -row 0 -sticky ns
grid [scrollbar $defw.x -command "$CIF(defBox) xview" \
	-orient horizontal] -column 0 -row 1 -sticky ew
grid columnconfig $defw 0 -weight 1
grid rowconfig $defw 0 -weight 1
# hide it
wm withdraw $defw
update

set CIF(showCIF) 0
set CIF(showDefs) 0
# make window for the CIF Editor
set CIF(browser) .browser
catch {destroy $CIF(browser)}
toplevel $CIF(browser) 
wm title $CIF(browser) "CIF Editor"
# put box in upper left
wm withdraw $CIF(browser)
wm geometry $CIF(browser) +0+0
update
wm deiconify $CIF(browser)
grid [set menubar [frame $CIF(browser).menu \
	-bd 4 -relief groove -class MenuFrame]] -column 0 -row 0 -sticky ew
grid [frame $CIF(browser).tree] -column 0 -row 1 -sticky news
frame $CIF(browser).box
set col 0
grid [button $CIF(browser).box.c -text Close \
	-command {ConfirmDestroy $CIF(browser)} \
	] -column $col -row 1 -sticky w
grid columnconfig $CIF(browser).box $col -weight 1
incr col
grid [button $CIF(browser).box.f -text "Show CIF Contents" \
	-command "ShowCIFWindow $filew $CIF(browser)"] \
	-column $col -row 1
incr col
grid [button $CIF(browser).box.d -text "Show CIF Definitions" \
	-command "ShowDefWindow $defw $CIF(browser) $filew"] \
	-column $col -row 1 -sticky w
grid columnconfig $CIF(browser).box $col -weight 1

incr col
grid [button $CIF(browser).box.v -text "Validate CIF" \
	-command "ValidateAllItems $CIF(txt)"] -column $col -row 1 -sticky w
incr col
grid [button $CIF(browser).box.u -text "Undo" -command UndoChanges \
	-state disabled] \
	-column $col -row 1 -sticky w
incr col
grid [button $CIF(browser).box.r -text "Redo" -command RedoChanges \
	-state disabled] \
	-column $col -row 1 -sticky w

incr col
grid [label $CIF(browser).box.3 -text "Mode:"] -column $col -row 1
incr col
grid [radiobutton $CIF(browser).box.4 -text "browse" \
	-variable CIF(editmode) -value 0 -command RepeatLastshowCIFvalue \
	] -column $col -row 1
incr col
grid [radiobutton $CIF(browser).box.5 -text "edit" \
	-variable CIF(editmode) -value 1 -command RepeatLastshowCIFvalue \
	] -column $col -row 1
incr col
grid [button $CIF(browser).box.6 -text "Save" \
	-command {SaveCIFtoFile $CIF(ciffile)} -state disabled] -column $col -row 1
set CIF(editmode) 0

wm protocol $filew WM_DELETE_WINDOW \
	"ShowCIFWindow $filew $CIF(browser)"
wm protocol $defw WM_DELETE_WINDOW \
	"ShowDefWindow $defw $CIF(browser) $filew"
wm protocol $CIF(browser) WM_DELETE_WINDOW \
	{ConfirmDestroy $CIF(browser)}

trace variable CIF(changes) w "EnableSaveEdits"
proc EnableSaveEdits {args} {
    global CIF menubar
    set menubutton $menubar.file.menu
    set i [$menubutton index end]
    set menuindex {}
    while {$i > 0} {
	catch {
	    if {[string match "Save" [$menubutton entrycget $i -label]]} {
		set menuindex $i
		break
	    }
	}
	incr i -1
    }
    set button  $CIF(browser).box.6
    if {$CIF(changes)} {
	set mode normal
    } else {
	set mode disabled
    }
    $button config -state $mode
    catch {$menubutton entryconfigure $menuindex -state $mode}
}
trace variable CIF(undolist) w "EnableUndoRedo undolist"
trace variable CIF(redolist) w "EnableUndoRedo redolist"
proc EnableUndoRedo {var args} {
    global CIF menubar
    if {$var == "undolist"} {
	set button $CIF(browser).box.u
	set lbl Undo
    } else {
	set button $CIF(browser).box.r 
	set lbl Redo
    }
    set menubutton $menubar.edit.menu
    set i [$menubutton index end]
    set menuindex {}
    while {$i > 0} {
	catch {
	    if {$lbl == [$menubutton entrycget $i -label]} {
		set menuindex $i
		break
	    }
	}
	incr i -1
    }

    if {[llength $CIF($var)] > 0} {
	set mode normal
    } else {
	set mode disabled
    }
    $button config -state $mode
    catch {$menubutton entryconfigure $menuindex -state $mode}
}


proc SaveCIFtoFile {file} {
    global CIF
    if {$file == ""} {
	set file [tk_getSaveFile -parent $CIF(browser)  \
		-filetypes {{"CIF file" .cif}} -defaultextension .cif]
	set CIF(ciffile) $file
	wm title $CIF(browser) "CIF Browser: file $file"
    }
    set CIF(changes) 0
    set CIF(undolist) {}
    set CIF(redolist) {}
    # at least for the moment, keep the previous version
    catch {file rename -force $file ${file}.old}
    set fp [open $file w]
    puts -nonewline $fp [$CIF(txt) get 1.0 end]
    close $fp
}

proc ConfirmDestroy {frame} {
    global CIF
    if {$CIF(changes) != 0} {
	set ans [MyMessageBox -parent . -title "Discard Changes?" \
		-message "You have changed this CIF. Do you want to save or discard your changes?" \
		-icon question -type {Save Discard Cancel} -default Save]
	if {$ans == "save"} {
	    SaveCIFtoFile $CIF(ciffile)
	    destroy $frame
	} elseif {$ans == "discard"} {
	    destroy $frame
	} else {
	    return
	}
    } else {
	destroy $frame
    }
    exit
}

proc ShowDefWindow {window master cifw} {
    global CIF tcl_platform menubar
    set menubutton $menubar.window.menu
    set button $CIF(browser).box.d 
    set i [$menubutton index end]
    set mode Show
    set menuindex {}
    while {$i > 0} {
	catch {
	    set txt [$menubutton entrycget $i -label]
	    if {[string match "* CIF Definitions" $txt]} {
		set menuindex $i
		set mode [lindex $txt 0]
		break
	    }
	}
	incr i -1
    }
    if {$mode == "Show"} {
	set txt "Hide CIF Definitions"
	if {$CIF(showDefs) == 0} {
	    # approximate size of border
	    if {$tcl_platform(platform) == "windows"} {
		# on windows border is included in computations
		set border 0
	    } else {
		set border [expr [winfo rooty $master] - [winfo vrooty $master]]
	    }
	    # put the window under the browser/file window on the first call
	    if {[winfo ismapped $cifw]} {
		# next to the cif contents window
		set x [expr 5 + [winfo x $cifw] + [winfo width $cifw]]
		set y [expr [winfo rooty $master] + [winfo height $master] + \
			   $border]
	    } else {
		# under the browser
		set x [winfo x $master]
		set y [expr [winfo rooty $master] + [winfo height $master] + \
			   $border]
	    }
	    wm geometry $window +$x+$y
	    update
	    set CIF(showDefs) 1
	}
	wm deiconify $window
    } else {
	set txt "Show CIF Definitions"
	wm withdraw $window
    }
    catch {$menubutton entryconfigure $menuindex -label $txt}
    $button config -text $txt
}

proc ShowCIFWindow {window master} {
    global CIF tcl_platform menubar
    set menubutton $menubar.window.menu
    set button $CIF(browser).box.f
    set i [$menubutton index end]
    set mode Show
    set menuindex {}
    while {$i > 0} {
	catch {
	    set txt [$menubutton entrycget $i -label]
	    if {[string match "* CIF Contents" $txt]} {
		set menuindex $i
		set mode [lindex $txt 0]
		break
	    }
	}
	incr i -1
    }
    if {$mode == "Show"} {
	set txt "Hide CIF Contents"
	# approximate size of border
	if {$tcl_platform(platform) == "windows"} {
	    # on windows border is included in computations
	    set border 0
	} else {
	    set border [expr [winfo rooty $master] - [winfo vrooty $master]]
	}
	if {$CIF(showCIF) == 0} {
	    # put the window under the browser on the first call
	    set x [winfo x $master]
	    set y [expr [winfo rooty $master] + [winfo height $master] + \
			   $border]
	    wm geometry $window +$x+$y
	    update
	    set CIF(showCIF) 1
	    set CIF(showDefs) 0
	}
	wm deiconify $window
    } else {
	set txt "Show CIF Contents"
	wm withdraw $window
    }
    catch {$menubutton entryconfigure $menuindex -label $txt}
    $button config -text $txt
}

proc EditCIFBox {button} {
    global CIF
    if {[$button cget -text] == "Open for Editing"} {
	if {[CheckForCIFEdits]} return
	$button config -text "Close Editing"
	# save the current mode
	set CIF(oldeditmode) $CIF(editmode)
	set CIF(editmode) 0
	RepeatLastshowCIFvalue
	$CIF(browser).box.3 config -fg gray
	# disable most of the editor to avoid conflicts
	foreach w {4 5 6 c f u r} {
	    $CIF(browser).box.$w config -state disabled
	}
	$CIF(txt) config -state normal
	# prevent other windows from functioning
	#grab $CIF(txt)
    } else {
	$button config -text "Open for Editing"
	# reenable the other windows
	#grab release $CIF(txt)
	$CIF(browser).box.3 config -fg black
	foreach w {4 5 6 c f} {
	    $CIF(browser).box.$w config -state normal
	}
	incr CIF(changes)
	set CIF(editmode) $CIF(oldeditmode)
	$CIF(txt) config -state disabled
	RepeatLastshowCIFvalue
	# need to parse the revised CIF
	foreach i $CIF(blocklist) {
	    global block$i
	    unset block$i
	}

	pleasewait "Parsing CIF"  CIF(status) $CIF(txt)

	set CIF(maxblocks) [ParseCIF $CIF(txt)]

	# update the blocklist & display them
	set CIF(blocklist) {}
	if {[array names block0] != ""} {
	    set i 0
	} else {
	    set i 1
	}
	set errors ""
	for {} {$i <= $CIF(maxblocks)} {incr i} {
	    lappend CIF(blocklist) $i
	    if {![catch {set block${i}(errors)}]} {
		if {$errors ==""} {set errors "Errors in file $CIF(ciffile)\n\n"}
		append errors "Data block #$i [set block${i}(data_)]\n"
		append errors "======================================\n\n"
		append errors "[set block${i}(errors)]\n"
	    }
	}
	
	if {$CIF(blocklist) != ""} {
	    CIFBrowser $CIF(txt) $CIF(blocklist) "" $CIF(browser).tree
	}
	catch {donewait}
	if {$errors != ""} {
	    if {[MyMessageBox -parent $CIF(txt) -title "CIF errors" \
		    -message "Note: $errors" \
		    -icon error -type {Continue "Save Errors"} \
		    -default continue] == "continue"} {return}
	    set file [tk_getSaveFile -parent $CIF(txt) \
		    -filetypes {{"text file" .txt}} -defaultextension .txt]
	    if {$file == ""} return
	    set fp [open $file w]
	    puts $fp $error
	    close $fp
	}
    }
}

# validate the fields in a CIF
proc ValidateAllItems {txt} {
    global CIF
    set errors 0
    pleasewait "Validating CIF" {} $CIF(browser)
    set blocklist $CIF(blocklist)
    foreach n $blocklist {
	set block block$n
	global block$n
	# make a list of data names in loops
	set looplist {}
	foreach loop [array names block$n loop_*] {
	    eval lappend looplist [set block${n}($loop)]
	}
	# clear out the block error list
	set ${block}(validate) {}
	# loop over data names
	foreach dataname [lsort [array names block$n _*]] {
	    if {[lsearch $looplist $dataname] == -1} {
		set mark [set ${block}($dataname)]
		set item [$CIF(txt) get $mark.l $mark.r]
		set err [ValidateCIFName $dataname]
		if {$err != ""} {
		    append ${block}(validate) "$err\n"
		    incr errors
		} else {
		    set err [ValidateCIFItem $dataname $item]
		    if {$err != ""} {
			append ${block}(validate) "$err\n"
			incr errors
		    }
		}
	    } else {
		# looped names
		set err [ValidateCIFName $dataname]
		if {$err != ""} {
		    append ${block}(validate) "$err\n"
		    incr errors
		    continue
		}
		set index 0
		foreach mark [set ${block}($dataname)] {
		    incr index
		    set item [$CIF(txt) get $mark.l $mark.r]
		    set err [ValidateCIFItem $dataname $item]
		    if {$err != ""} {
			append ${block}(validate) "$err (loop index #$index)\n"
			incr errors
		    }
		}
	    }
	}
	if {[catch {set ${block}(validateicon)} err]} {
	    if {[set ${block}(validate)] != ""} {
		# insert validation error pointer
		$CIF(tree) insert 0 block$n [incr CIF(tree_lastindex)] \
			-text "Validation-errors" -image [Bitmap::get undo] \
			-data block$n
		set ${block}(validateicon) $CIF(tree_lastindex)
	    }
	}
    }
    donewait
    if {$errors > 0} {
	set i 0
	set msg "$errors validation errors were found in $CIF(ciffile).\n\n"
	foreach n $blocklist {
	    incr i
	    set block block$n
	    global block$n
	    # get the block name
	    if {[set err [set block${n}(validate)]] != ""} {
		append msg "Data block #$i [set block${n}(data_)]\n"
		append msg "======================================\n\n"
		append msg "[set block${n}(validate)]\n"
	    }
	}
	if {[MyMessageBox -parent $CIF(tree) -title "Validation errors" \
		-message $msg -icon error -type {OK "Save Errors"} -default "ok"] \
		== "ok"} return
	set file [tk_getSaveFile -parent $CIF(tree) \
		-filetypes {{"text file" .txt}} -defaultextension .txt]
	if {$file == ""} return
	set fp [open $file w]
	puts $fp $msg
	close $fp
    } else {
	MyMessageBox -parent $CIF(tree) -title "No validation errors" \
	    -message "No validation errors encountered" \
	    -type OK -default "ok"
    }
}

# make the new font size take effect
proc ChangeFont {font} {
    global CIF
    catch {
	SetTkDefaultOptions $font
	ResizeFont .
	# redraw the browser
	CIFBrowser $CIF(txt) $CIF(blocklist) "" $CIF(browser).tree
    }
}

proc loadCIF {file} {
    global CIF filew

    if {$CIF(changes) != 0} {
	set ans [MyMessageBox -parent . -title "Discard Changes?" \
		-message "You have changed the current CIF. Do you want to save or discard your changes?" \
		-icon question -type {Save Discard Cancel} -default Save]
	if {$ans == "save"} {
	    SaveCIFtoFile $CIF(ciffile)
	} elseif {$ans == "cancel"} {
	    return
	}
    }

    if {[llength $file] != 1 || ![file exists [lindex $file 0]]} {
	set file [tk_getOpenFile -title "Select CIF" -parent . \
		-defaultextension .cif -filetypes {{"CIF data" ".cif .CIF"}}]
	if {$file == ""} {return}
    }
    # make sure the file exists
    if {![file exists $file]} {return}
    # work in the directory where the file is located
    catch {cd [file dirname $file]}
    set CIF(ciffile) $file

    # clear out the old CIF
    catch {
	foreach i $CIF(blocklist) {
	    global block$i
	    unset block$i
	}
    }
    # destroy the text box as that is faster than deleting the contents
    set w [$CIF(txt) cget -width]
    destroy $CIF(txt) 
    grid [text $CIF(txt) -height 10 -width $w -yscrollcommand "$filew.s set" \
	    -wrap none] -column 0 -row 0 -sticky news

    pleasewait "while loading CIF file" CIF(status) $filew {Quit exit}

    set CIF(maxblocks) [ParseCIF $CIF(txt) $file]
    set CIF(blocklist) {}
    global block0
    if {[array names block0] != ""} {
	set i 0
    } else {
	set i 1
    }
    set errors ""
    for {} {$i <= $CIF(maxblocks)} {incr i} {
	global block$i
	lappend CIF(blocklist) $i
	if {![catch {set block${i}(errors)}]} {
	    if {$errors ==""} {set errors "Errors in file $file\n\n"}
	    append errors "Data block #$i [set block${i}(data_)]\n"
	    append errors "======================================\n\n"
	    append errors "[set block${i}(errors)]\n"
	}
    }

    wm title $CIF(browser) "CIF Browser: file $file"
    if {$CIF(blocklist) != ""} {
	CIFBrowser $CIF(txt) $CIF(blocklist) "" $CIF(browser).tree
	wm deiconify $CIF(browser)
	# hide the CIF window
	wm withdraw $filew
    }

    donewait
    if {$errors != ""} {
	if {[MyMessageBox -parent $CIF(browser) -title "CIF errors" \
		-message "Note: this CIF has errors.\n\n$errors" \
		-icon error -type {Continue "Save Errors"} \
		-default continue] != "continue"} {
	    set file [tk_getSaveFile -parent $CIF(browser) \
		    -filetypes {{"text file" .txt}} -defaultextension .txt]
	    if {$file != ""} {
		set fp [open $file w]
		puts $fp $errors
		close $fp
	    }
	}
    }
}

proc ShowButtonBar {} {
    global CIF menubar
    set menubutton $menubar.opts.menu
    set i [$menubutton index end]
    set menuindex {}
    while {$i > 0} {
	if {[string match "* Button bar" [$menubutton entrycget $i -label]]} {
	    set menuindex $i
	    break
	}
	incr i -1
    }
    if {[winfo viewable $CIF(browser).box]} {
	grid forget $CIF(browser).box
	set lbl "Show Button bar"
	set CIF(ShowButtonBar) 0
    } else {
	grid $CIF(browser).box -column 0 -row 2 -sticky ew
	set lbl "Hide Button bar"
	set CIF(ShowButtonBar) 1
    }
    catch {$menubutton entryconfigure $menuindex -label $lbl}
}

proc SaveOptions {} {
    global CIF tcl_platform
    if {[catch {
	if {$tcl_platform(platform) == "windows"} {
	    set file ~/cifedit.cfg
	} else {
	    set file ~/.cifedit_cfg
	}
	set fp [open $file w]
	puts $fp "set CIF(dictfilelist) [list $CIF(dictfilelist)]"
	puts $fp "array set CIF {"
	foreach name {font ShowDictDups ShowButtonBar maxvalues} {
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

#----------------------------------------------------------------------
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


#----------------------------------------------------------------------
# populate the menubar
pack [menubutton $menubar.file -text File -underline 0 \
	-menu $menubar.file.menu] -side left
menu $menubar.file.menu
$menubar.file.menu add command -command "loadCIF {}" -label "Open" -underline 0

$menubar.file.menu add command \
	-command {SaveCIFtoFile $CIF(ciffile)} \
	-label "Save" -underline 0 -state disabled
$menubar.file.menu add command \
	-command {SaveCIFtoFile ""} \
	-label "Save As" -underline 1
$menubar.file.menu add command \
	-command {ConfirmDestroy $CIF(browser)} \
	-label "Exit" -underline 1

# Edit menu button
pack [menubutton $menubar.edit -text Edit -underline 0 \
	-menu $menubar.edit.menu] -side left
menu $menubar.edit.menu

$menubar.edit.menu add command -underline 0 \
	-label "Undo" -command UndoChanges -state disabled
$menubar.edit.menu add command -underline 0 \
	-label "Redo" -command RedoChanges -state disabled
$menubar.edit.menu add command -command "ValidateAllItems $CIF(txt)" \
	-label "Validate CIF" -underline 0
$menubar.edit.menu add cascade -menu $menubar.edit.menu.mode \
	-label "Mode" -underline 0
menu $menubar.edit.menu.mode
$menubar.edit.menu.mode add radiobutton -variable CIF(editmode) -value 0 \
	-label "Browse" -underline 0 -command RepeatLastshowCIFvalue 
$menubar.edit.menu.mode add radiobutton -variable CIF(editmode) -value 1 \
	-label "Edit" -underline 0 -command RepeatLastshowCIFvalue 
$menubar.edit.menu add cascade -menu $menubar.edit.menu.add \
	-label "Add" -underline 0
menu $menubar.edit.menu.add
$menubar.edit.menu.add add command \
	-label "New Loop" -command "AddDataItem2CIF loop .browser"
$menubar.edit.menu.add add command \
	-label "Item by Category" -command "AddDataItem2CIF category .browser"
$menubar.edit.menu.add add command \
	-label "Item by Name" -command "AddDataItem2CIF name .browser"


# Window menu button
pack [menubutton $menubar.window -text Windows -underline 0 \
	-menu $menubar.window.menu] -side left
menu $menubar.window.menu
$menubar.window.menu add command -label "Show CIF Contents" -underline 9 \
	-command "ShowCIFWindow $filew $CIF(browser)"
$menubar.window.menu add command -label "Show CIF Definitions" -underline 9 \
	-command "ShowDefWindow $defw $CIF(browser) $filew"
# Options menu button
pack [menubutton $menubar.opts -text Options -underline 0 \
	-menu $menubar.opts.menu] -side left
menu $menubar.opts.menu
$menubar.opts.menu add command -label "Select Dictionaries..." -underline 0 \
	-command "MakeDictSelect $CIF(browser)"
$menubar.opts.menu add command -label "Show Button bar" -underline 5 \
	-command ShowButtonBar
$menubar.opts.menu add cascade -menu $menubar.opts.menu.font \
	-label "Screen font"
menu $menubar.opts.menu.font 
foreach f {10 11 12 13 14 16 18 20 22} {
    $menubar.opts.menu.font add radiobutton \
	    -command {ChangeFont $CIF(font)} \
	    -label $f -value $f -variable CIF(font) -font "Helvetica -$f"
}
$menubar.opts.menu add checkbutton -variable CIF(ShowDictDups) \
    -label "Show Duplicate Dict. defs." \
    -command {if $CIF(ShowDictDups) LoadDictIndices}
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
pack [menubutton $menubar.help -text Help -underline 0 \
	-menu $menubar.help.menu -width 15 -justify right -anchor e] \
	-side right 
menu $menubar.help.menu
$menubar.help.menu add command -label "About" -underline 0 \
	-command {tk_dialog .warn About "\
Program CIFEDIT\n\n\
B. Toby, NIST\nBrian.Toby@NIST.gov\n\n
Not subject to copyright\n\n\
Version: [lindex $RevisionNumber 1] ([lindex $RevisionDate 1])" {} 0 OK
}
$menubar.help.menu add command -label "Web page" -underline 0 \
	-command {MakeHelp cifedit.html}
if {![catch {package require tkcon} errmsg]} {
    $menubar.help.menu add command -label "Open console" \
	-command {tkcon show}
} elseif {$tcl_platform(platform) == "windows"} {
    $menubar.help.menu add command -label "Open console" \
	-command {console show}
}
#
#----------------------------------------------------------------------

# hide the browser window
wm iconify $CIF(browser)
# center the CIF text window
wm withdraw $filew
set x [expr {[winfo screenwidth $filew]/2 - [winfo reqwidth $filew]/2 \
            - [winfo vrootx [winfo parent $filew]]}]
set y [expr {[winfo screenheight $filew]/2 - [winfo reqheight $filew]/2 \
	- [winfo vrooty [winfo parent $filew]]}]
wm geometry $filew +$x+$y
update
wm deiconify $filew



CIFOpenBrowser $CIF(browser).tree
# display button bar if requested
if {$CIF(ShowButtonBar)} ShowButtonBar

set CIF(ciffile) {}
loadCIF $argv
# make sure we start with a file
if {$CIF(ciffile) == ""} {
    wm title $CIF(browser) "CIF Browser: no file loaded"
    wm deiconify $CIF(browser)
    # hide the CIF window
    wm withdraw $filew 
}

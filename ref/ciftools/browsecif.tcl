# $Id: browsecif.tcl,v 1.12 2005/03/01 20:50:25 toby Exp toby $

# possible future work:
#   implement adding a new data item to a CIF? Delete one?
#   can I bind to the tree window only? (.browser.pw.f0.frame.lf.tree)
#   clean up use of block<n> arrays. Should the prefix be changable? Use
#    the same syntax throughout

#------------------------------------------------------------------------------
# Misc Tcl/Tk utility routines follow
#------------------------------------------------------------------------------
#	Message box code that centers the message box over the parent.
#          or along the edge, if too close, 
#          but leave a border along +x & +y for reasons I don't remember
#       It also allows the button names to be defined using 
#            -type $list  -- where $list has a list of button names
#       larger messages are placed in a scrolled text widget
#       capitalization is now ignored for -default
#       The command returns the name button in all lower case letters
#       otherwise see  tk_messageBox for a description
#
#       This is a modification of tkMessageBox (msgbox.tcl v1.5)
#
proc MyMessageBox {args} {
    global tkPriv tcl_platform

    set w tkPrivMsgBox
    upvar #0 $w data

    #
    # The default value of the title is space (" ") not the empty string
    # because for some window managers, a 
    #		wm title .foo ""
    # causes the window title to be "foo" instead of the empty string.
    #
    set specs {
	{-default "" "" ""}
        {-icon "" "" "info"}
        {-message "" "" ""}
        {-parent "" "" .}
        {-title "" "" " "}
        {-type "" "" "ok"}
        {-helplink "" "" ""}
    }

    tclParseConfigSpec $w $specs "" $args

    if {[lsearch {info warning error question} $data(-icon)] == -1} {
	error "bad -icon value \"$data(-icon)\": must be error, info, question, or warning"
    }
    if {![string compare $tcl_platform(platform) "macintosh"]} {
      switch -- $data(-icon) {
          "error"     {set data(-icon) "stop"}
          "warning"   {set data(-icon) "caution"}
          "info"      {set data(-icon) "note"}
	}
    }

    if {![winfo exists $data(-parent)]} {
	error "bad window path name \"$data(-parent)\""
    }

    switch -- $data(-type) {
	abortretryignore {
	    set buttons {
		{abort  -width 6 -text Abort -under 0}
		{retry  -width 6 -text Retry -under 0}
		{ignore -width 6 -text Ignore -under 0}
	    }
	}
	ok {
	    set buttons {
		{ok -width 6 -text OK -under 0}
	    }
          if {![string compare $data(-default) ""]} {
		set data(-default) "ok"
	    }
	}
	okcancel {
	    set buttons {
		{ok     -width 6 -text OK     -under 0}
		{cancel -width 6 -text Cancel -under 0}
	    }
	}
	retrycancel {
	    set buttons {
		{retry  -width 6 -text Retry  -under 0}
		{cancel -width 6 -text Cancel -under 0}
	    }
	}
	yesno {
	    set buttons {
		{yes    -width 6 -text Yes -under 0}
		{no     -width 6 -text No  -under 0}
	    }
	}
	yesnocancel {
	    set buttons {
		{yes    -width 6 -text Yes -under 0}
		{no     -width 6 -text No  -under 0}
		{cancel -width 6 -text Cancel -under 0}
	    }
	}
	default {
#	    error "bad -type value \"$data(-type)\": must be abortretryignore, ok, okcancel, retrycancel, yesno, or yesnocancel"
	    foreach item $data(-type) {
		lappend buttons [list [string tolower $item] -text $item -under 0]
	    }
	}
    }

    if {[string compare $data(-default) ""]} {
	set valid 0
	foreach btn $buttons {
	    if {![string compare [lindex $btn 0] [string tolower $data(-default)]]} {
		set valid 1
		break
	    }
	}
	if {!$valid} {
	    error "invalid default button \"$data(-default)\""
	}
    }

    # 2. Set the dialog to be a child window of $parent
    #
    #
    if {[string compare $data(-parent) .]} {
	set w $data(-parent).__tk__messagebox
    } else {
	set w .__tk__messagebox
    }

    # 3. Create the top-level window and divide it into top
    # and bottom parts.

    catch {destroy $w}
    toplevel $w -class Dialog
    wm title $w $data(-title)
    wm iconname $w Dialog
    wm protocol $w WM_DELETE_WINDOW { }
    wm transient $w $data(-parent)
    if {![string compare $tcl_platform(platform) "macintosh"]} {
	unsupported1 style $w dBoxProc
    }

    frame $w.bot
    pack $w.bot -side bottom -fill both
    frame $w.top
    pack $w.top -side top -fill both -expand 1
    if {$data(-helplink) != ""} {
#	frame $w.help
#	pack $w.help -side top -fill both
	pack [button $w.top.1 -text Help -bg yellow \
		-command "MakeWWWHelp $data(-helplink)"] \
		-side right -anchor ne
	bind $w <Key-F1> "MakeWWWHelp $data(-helplink)"
    }
    if {[string compare $tcl_platform(platform) "macintosh"]} {
	$w.bot configure -relief raised -bd 1
	$w.top configure -relief raised -bd 1
    }

    # 4. Fill the top part with bitmap and message (use the option
    # database for -wraplength and -font so that they can be
    # overridden by the caller).

    option add *Dialog.msg.wrapLength 6i widgetDefault

    if {[string length $data(-message)] > 300} {
	if {![string compare $tcl_platform(platform) "macintosh"]} {
	    option add *Dialog.msg.t.font system widgetDefault
	} else {
	    option add *Dialog.msg.t.font {Times 18} widgetDefault
	}
	frame $w.msg
	grid [text  $w.msg.t  \
		-height 20 -width 55 -relief flat -wrap word \
		-yscrollcommand "$w.msg.rscr set" \
		] -row 1 -column 0 -sticky news
	grid [scrollbar $w.msg.rscr  -command "$w.msg.t yview" \
		] -row 1 -column 1 -sticky ns
	# give extra space to the text box
	grid columnconfigure $w.msg 0 -weight 1
	grid rowconfigure $w.msg 1 -weight 1
	$w.msg.t insert end $data(-message)
    } else {
	if {![string compare $tcl_platform(platform) "macintosh"]} {
	    option add *Dialog.msg.font system widgetDefault
	} else {
	    option add *Dialog.msg.font {Times 18} widgetDefault
	}
	label $w.msg -justify left -text $data(-message)
    }
    pack $w.msg -in $w.top -side right -expand 1 -fill both -padx 3m -pady 3m
    if {[string compare $data(-icon) ""]} {
	label $w.bitmap -bitmap $data(-icon)
	pack $w.bitmap -in $w.top -side left -padx 3m -pady 3m
    }

    # 5. Create a row of buttons at the bottom of the dialog.

    set i 0
    foreach but $buttons {
	set name [lindex $but 0]
	set opts [lrange $but 1 end]
      if {![llength $opts]} {
	    # Capitalize the first letter of $name
          set capName [string toupper \
		    [string index $name 0]][string range $name 1 end]
	    set opts [list -text $capName]
	}

      eval button [list $w.$name] $opts [list -command [list set tkPriv(button) $name]]

	if {![string compare $name [string tolower $data(-default)]]} {
	    $w.$name configure -default active
	}
      pack $w.$name -in $w.bot -side left -expand 1 -padx 3m -pady 2m

	# create the binding for the key accelerator, based on the underline
	#
	set underIdx [$w.$name cget -under]
	if {$underIdx >= 0} {
	    set key [string index [$w.$name cget -text] $underIdx]
          bind $w <Alt-[string tolower $key]>  [list $w.$name invoke]
          bind $w <Alt-[string toupper $key]>  [list $w.$name invoke]
	}
	incr i
    }

    # 6. Create a binding for <Return> on the dialog if there is a
    # default button.

    if {[string compare $data(-default) ""]} {
      bind $w <Return> [list $w.[string tolower $data(-default)] invoke]
    }

    # 7. Withdraw the window, then update all the geometry information
    # so we know how big it wants to be, then center the window in the
    # display and de-iconify it.

    wm withdraw $w
    update idletasks
    set wp $data(-parent)
    # center the new window in the middle of the parent
    set x [expr [winfo x $wp] + [winfo width $wp]/2 - \
	    [winfo reqwidth $w]/2 - [winfo vrootx $wp]]
    set y [expr [winfo y $wp] + [winfo height $wp]/2 - \
	    [winfo reqheight $w]/2 - [winfo vrooty $wp]]
    # make sure that we can see the entire window
    set xborder 10
    set yborder 25
    if {$x < 0} {set x 0}
    if {$x+[winfo reqwidth $w] +$xborder > [winfo screenwidth $w]} {
	incr x [expr \
		[winfo screenwidth $w] - ($x+[winfo reqwidth $w] + $xborder)]
    }
    if {$y < 0} {set y 0}
    if {$y+[winfo reqheight $w] +$yborder > [winfo screenheight $w]} {
	incr y [expr \
		[winfo screenheight $w] - ($y+[winfo reqheight $w] + $yborder)]
    }
    wm geom $w +$x+$y
    update
    wm deiconify $w

    # 8. Set a grab and claim the focus too.

    catch {set oldFocus [focus]}
    catch {set oldGrab [grab current $w]}
    catch {
	grab $w
	if {[string compare $data(-default) ""]} {
	    focus $w.[string tolower $data(-default)]
	} else {
	    focus $w
	}
    }

    # 9. Wait for the user to respond, then restore the focus and
    # return the index of the selected button.  Restore the focus
    # before deleting the window, since otherwise the window manager
    # may take the focus away so we can't redirect it.  Finally,
    # restore any grab that was in effect.

    tkwait variable tkPriv(button)
    catch {focus $oldFocus}
    destroy $w
    catch {grab $oldGrab}
    return $tkPriv(button)
}

# tell'em what is happening
proc pleasewait {{message {}} {statusvar {}} {parent .} {button ""}} {
    if {$parent == "."} {
	set root ""
    } else {
	set root $parent
    }
    set ::PleaseWaitWindow ${root}.msg
    catch {destroy $::PleaseWaitWindow}
    toplevel $::PleaseWaitWindow
    wm transient $::PleaseWaitWindow [winfo toplevel $parent]
    pack [frame $::PleaseWaitWindow.f -bd 4 -relief groove] -padx 5 -pady 5
    pack [message $::PleaseWaitWindow.f.m -text "Please wait $message"] -side top
    if {$statusvar != ""} {
	pack [label $::PleaseWaitWindow.f.status -textvariable $statusvar] -side top
    }
    if {$button != ""} {
	pack [button $::PleaseWaitWindow.f.button -text [lindex $button 0] \
		-command [lindex $button 1]] -side top
    }
    wm withdraw $::PleaseWaitWindow
    update idletasks
    # place the message on top of the parent window
    set x [expr [winfo x $parent] + [winfo width $parent]/2 - \
	    [winfo reqwidth $::PleaseWaitWindow]/2 - [winfo vrootx $parent]]
    if {$x < 0} {set x 0}
    set y [expr [winfo y $parent] + [winfo height $parent]/2 - \
	    [winfo reqheight $::PleaseWaitWindow]/2 - [winfo vrooty $parent]]
    if {$y < 0} {set y 0}
    wm geom $::PleaseWaitWindow +$x+$y
    update
    wm deiconify $::PleaseWaitWindow
    global makenew
    set makenew(OldGrab) ""
    set makenew(OldFocus) ""
    # save focus & grab
    catch {set makenew(OldFocus) [focus]}
    catch {set makenew(OldGrab) [grab current $::PleaseWaitWindow]}
    catch {grab $::PleaseWaitWindow}
    update
}

# clear the wait message
proc donewait {} {
    global makenew
    catch {destroy $::PleaseWaitWindow}
    # reset focus & grab
    catch {
	if {$makenew(OldFocus) != ""} {
	    focus $makenew(OldFocus)
	}
    }
    catch {
	if {$makenew(OldGrab) != ""} {
	    grab $makenew(OldGrab)
	}
    }
    catch {unset ::PleaseWaitWindow}
}

# this routine is used to fix up tk_optionMenu widgets that have too many
# entries for a single list -- by using cascades
proc FixBigOptionMenu {widget enum "cmd {}"} {
    # max entries
    set max 12
    set menu [winfo children $widget]
    $menu delete 0 end
    eval destroy [winfo children $menu]
    set var [$widget cget -textvariable]
    # do we need a cascade?
    if {[set n [llength $enum]] <= $max} {
	# no
	foreach l $enum {
	    $menu add radiobutton -value $l -label $l -variable $var \
		    -command $cmd
	}
	return
    }
    # yes
    set nmenus [expr int(($max + $n - 1 )/ (1.*$max))]
    set nper [expr 1 + $n/$nmenus]
    if {$nper > $max} {set nper $max}
    for {set i 0} {$i < $n} {incr i $nper} {
	set j [expr $i + $nper -1]
	set sublist [lrange $enum $i $j]
	$menu add cascade -label "[lindex $sublist 0]-[lindex $sublist end]" \
		-menu $menu.$i
	menu $menu.$i
	foreach l $sublist {
	    $menu.$i add radiobutton -value $l -label $l -variable $var \
		    -command $cmd
	}
    }
}

# this routine is used to add . and ? in a cascade for enum lists
proc AddSpecialEnumOpts {widget "cmd {}"} {
    set menu [winfo children $widget]
    set var [$widget cget -textvariable]

    # add the cascade and entries to it
    $menu add cascade -label "(special values)" -menu $menu.special
    menu $menu.special
    $menu.special add radiobutton -value . -command $cmd \
	    -label "Inapplicable (.)" -variable $var
    $menu.special add radiobutton -value ? -command $cmd \
	    -label "Unknown (?)" -variable $var
}

proc putontop {w "center 0"} {
    # center window $w above its parent and make it stay on top
    set wp [winfo parent $w]
    wm transient $w [winfo toplevel $wp]
    wm withdraw $w
    update idletasks
    if {$center} {
	set x [expr {[winfo screenwidth $w]/2 - [winfo reqwidth $w]/2 \
		- [winfo vrootx [winfo parent $w]]}]
	set y [expr {[winfo screenheight $w]/2 - [winfo reqheight $w]/2 \
		- [winfo vrooty [winfo parent $w]]}]
    } else {
	# center the new window in the middle of the parent
	set x [expr [winfo x $wp] + [winfo width $wp]/2 - \
		[winfo reqwidth $w]/2 - [winfo vrootx $wp]]
	if {$x < 0} {set x 0}
	set xborder 10
	if {$x+[winfo reqwidth $w] +$xborder > [winfo screenwidth $w]} {
	    incr x [expr [winfo screenwidth $w] - \
		    ($x+[winfo reqwidth $w] + $xborder)]
	}
	set y [expr [winfo y $wp] + [winfo height $wp]/2 - \
		[winfo reqheight $w]/2 - [winfo vrooty $wp]]
	if {$y < 0} {set y 0}
	set yborder 25
	if {$y+[winfo reqheight $w] +$yborder > [winfo screenheight $w]} {
	    incr y [expr [winfo screenheight $w] - \
		    ($y+[winfo reqheight $w] + $yborder)]
	}
    }
    wm geometry $w +$x+$y
    wm deiconify $w

    global makenew
    set makenew(OldGrab) ""
    set makenew(OldFocus) ""
    catch {set makenew(OldFocus) [focus]}
    catch {set makenew(OldGrab) [grab current $w]}
    catch {grab $w}
}

proc afterputontop {} {
    # restore focus
    global makenew
    # reset focus & grab
    catch {
	if {$makenew(OldFocus) != ""} {
	    focus $makenew(OldFocus)
	}
    }
    catch {
	if {$makenew(OldGrab) != ""} {
	    grab $makenew(OldGrab)
	}
    }
}

#------------------------------------------------------------------------------
# end of Misc Tcl/Tk utility routines
#------------------------------------------------------------------------------

#------------------------------------------------------------------------------
# ParseCIF reads and parses a CIF file putting the contents of
# each block into arrays block1, block2,... in the caller's level
#    the name of the block is saved as blockN(data_)
# data names items are saved as blockN(_data_name) = marker_number
#    where CIF data names are converted to lower case
#    and marker_number.l marker_number.r define the range of the value
# for looped data names, the data items are included in a list:
#    blockN(_cif_name) = {marker1 marker2 ...}
# the contents of each loop are saved as blockN(loop_M)
#
# if the filename is blank or not specified, the current contents
#    of the text widget, $txt, is parsed.
#
# The proc returns the number of blocks that have been read or a
#    null string if the file cannot be opened
#
# This parser does some error checking [errors are reported in blockN(error)]
#    but the parser could get confused if the CIF has invalid syntax
#
proc ParseCIF {txt "filename {}" "namespace {}"} {
    global CIF tcl_version
    global CIF_dataname_index
    # create a namespace, if one is needed
    if {$namespace != ""} {
	namespace eval $namespace {}
    }

    if {$tcl_version < 8.2} {
	tk_dialog .error {Old Tcl/Tk} \
                "Sorry, the CIF Browser requires version 8.2 or later of the Tcl/Tk package. This is $tcl_version" \
                warning 0 Sorry
	return
    }

    if {$filename != ""} {
	if [catch {
	    $txt configure -state normal
	    set fp [open $filename r]
	    $txt insert end [read $fp]
	    close $fp
	    $txt configure -state disabled
	}] {
	    return ""
	}
    }

    # maximum size of file
    set maxvalues 0
    catch {
	set maxvalues $CIF(maxvalues)
    }

    set CIF(undolist) {}
    set CIF(redolist) {}
    set pos 1.0
    set blocks 0
    set EOF 1
    set dataname {}
    set CIF(markcount) -1
    # this flags where we are w/r a loop_
    #    -1 not in a loop
    #     0 reading a loop header (data names)
    #     1 reading the data items in a loop
    set loopflag -1
    set loopnum -1
    # loop over tokens
    while {$EOF} {
	if {$CIF(QuitParse)} return
	if {$CIF(markcount) % 1000 == 0} {
	    $txt see $pos
	    set CIF(status) "($CIF(markcount) values read.)"
	    update
	    # are we over the limit?
	    if {$maxvalues > 0 && $CIF(markcount) > $maxvalues} {
		donewait
		set msg "Too many data values to parse; stopping at $CIF(markcount), line [lindex [split $pos .] 0].\n\nIf your computer has sufficient memory to read more, increase CIF(maxvalues) in cifedit.tcl"
		set ans [MyMessageBox -parent . -title "CIF Too big" \
			-message $msg -icon error -type "{Stop Parsing}" \
			-default "stop parsing"]
		
		return $blocks
	    }
	}
	# skip forward to the first non-blank character
	set npos [$txt search -regexp {[^[:space:]]} $pos end]
	# is this the end?
	if {$npos == "" || \
		[lindex [split $npos .] 0] < [lindex [split $pos .] 0] } {
	    set EOF 0
	    break
	} else {
	    set pos $npos
	}

	# is this a comment, if so skip to next line
	if {[$txt get $pos] == "#"} {
	    set pos [$txt index "$pos + 1 line linestart"]
	    continue
	}

	# find end of token
	set epos [$txt search -regexp {[[:space:]]} $pos "$pos lineend"]
	if {$epos == ""} {
	    set epos [$txt index "$pos lineend"]
	}

	set token [$txt get $pos $epos]

	if {[string tolower [string range $token 0 4]] == "data_"} {
	    # this is the beginning of a data block
	    incr blocks
	    set blockname [string range $token 5 end]
	    catch {unset ${namespace}::block$blocks}
	    set ${namespace}::block${blocks}(data_) $blockname
	    set loopnum -1
	    if {$dataname != ""} {
		# this is an error -- data_ block where a data item is expected
		append ${namespace}::block${blocks}(errors) "No data item was found for $dataname near line [lindex [split $pos .] 0]\n"
		set dataname {}
	    }
	    # move forward past current token
	    set pos [$txt index "$epos +1c"]
	    continue
	}
	
	if {[$txt get $pos] == "_"} {
	    # this is a cif data name
	    if {$dataname != ""} {
		# this is an error -- data name where a data item is expected
		append ${namespace}::block${blocks}(errors) "No data item was found for $dataname near line [lindex [split $pos .] 0]\n"
	    }
	    # convert it to lower case & save
	    set dataname [string tolower $token]

	    # are we in a loop header or loop body?
	    if {$loopflag == 0} {
		# in a loop header, save the names in the loop list
		lappend looplist $dataname
		# check the categories used in the loop
		set category {}
		catch {
		    set category [lindex \
			    [lindex $CIF_dataname_index($dataname) 1] 5]
		}
		# don't worry if we don't have a category
		if {$category != ""} {
		    if {$catlist == ""} {
			set catlist $category
		    } elseif {[lsearch $catlist $category] == -1} {
			# error two categories in a loop
			lappend catlist $category
			append ${namespace}::block${blocks}(errors) \
				"Multiple categories ($catlist) in a loop_ for $dataname at line [lindex [split $pos .] 0]\n"
		    }
		}
		
		if {$blocks == 0} {
		    # an error -- a loop_ before a data_ block start
		    set ${namespace}::block${blocks}(data_) undefined
		    append ${namespace}::block${blocks}(errors) \
			    "A loop_ begins before a data_ block is defined (line [lindex [split $pos .] 0])\n"
		}
		set ${namespace}::block${blocks}(loop_${loopnum}) $looplist
		# clear the array element for the data item 
		# -- should not be needed for a valid CIF but if a name is used
		# -- twice in the same block, want to wipe out the 1st data
		catch {
		    if {[set ${namespace}::block${blocks}($dataname)] != ""} {
			# this is an error -- repeated data name
			append ${namespace}::block${blocks}(errors) \
				"Data name $dataname is repeated near line [lindex [split $pos .] 0]\n"
		    }   
		    set ${namespace}::block${blocks}($dataname) {}
		}
		set dataname {}
	    } elseif {$loopflag > 0} {
		# in a loop body, so the loop is over
		set loopflag -1
	    }
	    # move forward past current token
	    set pos [$txt index "$epos +1c"]
	    continue
	}
	
	if {[string tolower [string range $token 0 4]] == "loop_"} {
	    set loopflag 0
	    incr loopnum
	    set looplist {}
	    set catlist {}
	    set ${namespace}::block${blocks}(loop_${loopnum}) {}
	    # move forward past current token
	    set pos [$txt index "$epos +1c"]
	    continue
	}

	# keywords not matched, must be some type of data item
	set item {}
	incr CIF(markcount)
	
	if {[$txt get "$pos linestart"] == ";" && \
		[$txt index $pos] == [$txt index "$pos linestart"]} {
	    # multiline entry with semicolon termination
	    set epos [$txt search -regexp {^;} "$pos + 1 line linestart"]
	    if {$epos == ""} {
		set epos end
		append ${namespace}::block${blocks}(errors) \
			"Unmatched semicolon for $dataname starting at line [lindex [split $pos .] 0]\n"
	    }

	    $txt mark set $CIF(markcount).l "$pos linestart"
	    $txt mark set $CIF(markcount).r "$epos + 1c"
	    $txt mark gravity $CIF(markcount).l left
	    $txt mark gravity $CIF(markcount).r right
	    set item [$txt get "$pos linestart" "$epos +1c"]
	    # move forward past current token
	    set pos [$txt index "$epos + 1c"]
	} elseif {[$txt get $pos] == "\""} {
	    # a quoted string -- find next quote
	    set epos [$txt search "\"" "$pos +1c" "$pos lineend"]
	    # skip over quotes followed by a non-blank
	    while {$epos != "" && \
		    [regexp {[^[:space:]]} [$txt get "$epos +1c"]] == 1} {
		set epos [$txt search "\"" "$epos +1c" "$pos lineend"]
	    }
	    # did we hit the end of line?
	    if {$epos == ""} {
		set epos [$txt index "$pos lineend"]
		append ${namespace}::block${blocks}(errors) "The quoted string on line [lindex [split $pos .] 0] does not have a close quote:\n\t[$txt get $pos $epos]\n"
	    }
	    $txt mark set $CIF(markcount).l "$pos"
	    $txt mark set $CIF(markcount).r "$epos + 1c"  
	    $txt mark gravity $CIF(markcount).l left
	    $txt mark gravity $CIF(markcount).r right
	    set item [$txt get  $pos "$epos +1c"]
	    # move forward past current token
	    set pos [$txt index "$epos +2c"]
	} elseif {[$txt get $pos] == {'}} {
	    # a quoted string -- find next quote
	    set epos [$txt search {'} "$pos +1c" "$pos lineend"]
	    # skip over quotes followed by a non-blank
	    while {$epos != "" && \
		    [regexp {[^[:space:]]} [$txt get "$epos +1c"]] == 1} {
		set epos [$txt search {'} "$epos +1c" "$pos lineend"]
	    }
	    # did we hit the end of line?
	    if {$epos == ""} {
		set epos [$txt index "$pos lineend"]
		append ${namespace}::block${blocks}(errors) "The quoted string on line [lindex [split $pos .] 0] does not have a close quote:\n\t[$txt get $pos $epos]\n"
	    }
	    $txt mark set $CIF(markcount).l "$pos"        
	    $txt mark set $CIF(markcount).r "$epos + 1c"  
	    $txt mark gravity $CIF(markcount).l left
	    $txt mark gravity $CIF(markcount).r right
	    set item [$txt get $pos "$epos +1c"]
	    # move forward past current token
	    set pos [$txt index "$epos + 2 c"]
	} elseif {[$txt get $pos] == {[}} {
	    # CIF v1.1 square bracket quotes
	    set count 1
	    set epos $pos
	    while {$count != 0} {
		set epos [$txt search -regexp {[\]\[]} "$epos +1c"]
		if {$epos == ""} {
		    # unmatched open square bracket
		    append ${namespace}::block${blocks}(errors) "No closing \] was found for open \] at line [lindex [split $pos .] 0]\n"
		    set count 0
		    set epos [$txt index end]
		} elseif {[$txt get $epos] == {]}} {
		    # close bracket -- decrement
		    incr count -1
		} else {
		    # open bracket -- increment
		    incr count
		}
	    }
	    $txt mark set $CIF(markcount).l "$pos"        
	    $txt mark set $CIF(markcount).r "$epos + 1c"  
	    $txt mark gravity $CIF(markcount).l left
	    $txt mark gravity $CIF(markcount).r right
	    set item [$txt get $pos "$epos +1c"]
	    # move forward past current token
	    set pos [$txt index "$epos + 2 c"]
	} else {
	    # must be a single space-delimited value
	    $txt mark set $CIF(markcount).l $pos
	    $txt mark set $CIF(markcount).r $epos
	    $txt mark gravity $CIF(markcount).l left
	    $txt mark gravity $CIF(markcount).r right
	    set item $token
	    set pos [$txt index "$epos + 1 c"]
	}
	# a data item has been read

	# store the data item
	if {$loopflag >= 0} {
	    # if in a loop, increment the loop element counter to select the
	    # appropriate array element
	    incr loopflag
	    set i [expr ($loopflag - 1) % [llength $looplist]]
	    lappend ${namespace}::block${blocks}([lindex $looplist $i]) $CIF(markcount)
	    set ${namespace}::block${blocks}(lastmark) $CIF(markcount)
	} elseif {$dataname == ""} {
	    # this is an error -- a data item where we do not expect one
	    append ${namespace}::block${blocks}(errors) "The string \"$item\" on line [lindex [split $pos .] 0] was unexpected\n"
	} else {
	    if {$blocks == 0} {
		# an error -- a data name before a data_ block start
		set ${namespace}::block${blocks}(data_) undefined
		append ${namespace}::block${blocks}(errors) \
			    "Data name $dataname appears before a data_ block is defined (line [lindex [split $pos .] 0])\n"
	    }
	    catch {
		if {[set ${namespace}::block${blocks}($dataname)] != ""} {
		    # this is an error -- repeated data name
		    append ${namespace}::block${blocks}(errors) \
			    "Data name $dataname is repeated near line [lindex [split $pos .] 0]\n"
		}
	    }
	    set ${namespace}::block${blocks}($dataname) $CIF(markcount)
	    set ${namespace}::block${blocks}(lastmark) $CIF(markcount)
	    set dataname ""
	}
    }
    $txt see 1.0
    return $blocks
}

#------------------------------------------------------------------------------
# Create a CIF browser/editor
#  $txt is a text widget with the entire CIF loaded
#  blocklist contains the list of defined blocks (by #)
#  selected is the list of blocks that will be expanded
#  frame gives the name of the toplevel window to hold the browser
proc BrowseCIF {txt blocklist "selected {}" "frame .cif"} {
    catch {destroy $frame}
    toplevel $frame 
    wm title $frame "CIF Browser"
    CIFOpenBrowser $frame
    CIFBrowser $txt $blocklist $selected $frame
    grid [button $frame.c -text Close -command "destroy $frame"] -column 0 -row 1
}

# Populate a hierarchical CIF browser
#    $txt is a text widget with the entire CIF loaded
#    blocklist contains the list of defined blocks (by #)
#    selected is the list of blocks that will be expanded
#    frame gives the name of the toplevel or frame to hold the browser
proc CIFBrowser {txt blocklist "selected {}" "frame .cif"} {
    global CIF CIFtreeindex CIF_dataname_index

    if {$selected == ""} {set selected $blocklist}

    # clear out old info, if any, from browser
    eval $CIF(tree) delete [$CIF(tree) nodes root]
    catch {unset CIFtreeindex}
    # remove the loop counter frame from window & edit buttons from that frame
    grid forget $CIF(LoopBar)
    pack forget $CIF(AddtoLoopButton) $CIF(DeleteLoopEntry)
    # delete old contents of frame
    set frame [$CIF(displayFrame) getframe]
    eval destroy [grid slaves $frame]
    set CIF(widgetlist) {}
    # reset the scrollbars
    $CIF(tree) see 0
    $CIF(displayFrame) xview moveto 0
    $CIF(displayFrame) yview moveto 0

    # Bwidget seems to have problems with the name "1", so avoid it
    set num 100
    foreach n $blocklist {
	global block$n
	# make a list of data names in loops
	set looplist {}
	foreach loop [array names block$n loop_*] {
	    eval lappend looplist [set block${n}($loop)]
	}
	# put the block name
	set blockname [set block${n}(data_)]
	set open 0
	if {[lsearch $selected $n] != -1} {set open 1}
	$CIF(tree) insert end root block$n -text "_data_$blockname" \
		-open $open -image [Bitmap::get folder]

	# show errors, if any
	foreach name [array names block$n errors] {
	    $CIF(tree) insert end block$n [incr num] -text "Parse-errors" \
		    -image [Bitmap::get undo] -data block$n
	}
	# loop over the names in each block 
	foreach name [lsort [array names block$n _*]] {
	    # don't include looped names
	    if {[lsearch $looplist $name] == -1} {
		$CIF(tree) insert end block$n [incr num] -text $name \
			-image [Bitmap::get file] -data block$n
		set CIFtreeindex(block${n}$name) $num
	    }
	}
	foreach loop [lsort [array names block$n loop_*]] {
	    # make a list of categories used in the loop
	    set catlist {}
	    foreach name [lsort [set block${n}($loop)]] {
		set category {}
		catch {
		    set category [lindex \
			    [lindex $CIF_dataname_index($name) 1] 5]
		}
		if {$category != "" && [lsearch $catlist $category] == -1} {
		    lappend catlist $category
		}
	    }

	    $CIF(tree) insert end block$n block${n}$loop \
		    -text "$loop ($catlist)" \
		    -image [Bitmap::get copy] -data "block$n loop"
	    set CIFtreeindex(block${n}$loop) block${n}$loop
	    foreach name [lsort [set block${n}($loop)]] {
		$CIF(tree) insert end block${n}$loop [incr num] -text $name \
			-image [Bitmap::get file] -data "block$n $loop"
		set CIFtreeindex(block${n}$name) $num
	    }
	}
    }
    $CIF(tree) bindImage <1> showCIFbyTreeID
    $CIF(tree) bindText <1>  showCIFbyTreeID
    set CIF(tree_lastindex) $num
}

# Create the widgets for a hierarchical CIF browser in $frame 
#   (where $frame is a frame or toplevel)
#   note that the BWidget package is required
proc CIFOpenBrowser {frame} {
    global CIF 
    if [catch {package require BWidget}] {
	tk_dialog .error {No BWidget} \
                "Sorry, the CIF Browser requires the BWidget package" \
                warning 0 Sorry
	return
    }

    set pw    [PanedWindow $frame.pw -side top]
    grid $pw -sticky news -column 0 -row 0 
    set CIF(LoopBar) [frame $frame.f]
    #grid $CIF(LoopBar) -sticky es -column 0 -row 1
    set width 900
    if {$width > [winfo screenwidth .]} {set width [winfo screenwidth .]}
    grid columnconfigure $frame 0 -weight 1 -minsize $width
    # shrink browser on small screens
    set h 250 
    if {[winfo screenheight .] < 500} {set h 180}
    grid rowconfigure $frame 0 -minsize $h -weight 1

    # create a left hand side pane for the hierarchical tree
    set pane  [$pw add -weight 1]
    set sw    [ScrolledWindow $pane.lf \
	    -relief sunken -borderwidth 2]
    set CIF(tree)  [Tree $sw.tree \
	    -relief flat -borderwidth 0 -width 15 -highlightthickness 0 \
	    -redraw 1]
    # get the size of the font and adjust the line spacing accordingly
    catch {
	set font [option get $CIF(tree) font Canvas]
	$CIF(tree) configure -deltay [font metrics $font -linespace]
    }
    bind $frame <KeyPress-Prior> "$CIF(tree) yview scroll -1 page"
    bind $frame <KeyPress-Next> "$CIF(tree) yview scroll 1 page"
#    bind $frame <KeyPress-Up> "$CIF(tree) yview scroll -1 unit"
#    bind $frame <KeyPress-Down> "$CIF(tree) yview scroll 1 unit"
    bind $frame <KeyPress-Home> "$CIF(tree) yview moveto 0"
    #bind $frame <KeyPress-End> "$CIF(tree) yview moveto end" -- does not work
    bind $frame <KeyPress-End> "$CIF(tree) yview scroll 99999999 page"
    grid $sw
    grid $sw -sticky news -column 0 -row 0 
    grid columnconfigure $pane 0 -minsize 275 -weight 1
    grid rowconfigure $pane 0 -weight 1
    $sw setwidget $CIF(tree)
    
    # create a right hand side pane to show the value
    set pane [$pw add -weight 4]
    set sw   [ScrolledWindow $pane.sw \
	    -relief sunken -borderwidth 2]
    pack $sw -fill both -expand yes -side top

    set CIF(AddtoLoopButton) [button $CIF(LoopBar).l -text "Add to loop"]
    set CIF(DeleteLoopEntry) [button $CIF(LoopBar).d \
	    -text "Delete loop entry" -command DeleteCIFRow]
    label $CIF(LoopBar).1 -text "Loop\nelement #"
    set CIF(LoopSpinBox) [SpinBox $CIF(LoopBar).2 -range "1 1 1"  -width 5]
    pack $CIF(LoopBar).2 $CIF(LoopBar).1 -side right
    set CIF(displayFrame) $sw.lb
    set lb [ScrollableFrame::create $CIF(displayFrame) -width 400]
    $sw setwidget $lb
}

# Warn to save changes that are not saved in a file
proc CheckForCIFEdits {} {
    #puts "CheckForCIFEdits [info level [expr [info level]-1]]"
    global CIF
    set errorlist {}
    set errorflag 0
    set msg "The following edits cannot be saved due to errors:\n"
    foreach widget $CIF(widgetlist) {
	CheckChanges $widget 1
	if {$CIF(errormsg) != ""} {
	    set errorflag 1
	    foreach err $CIF(errormsg) {
		append msg "  " $err \n
	    }
	}

    }
    if {$errorflag} {
	append msg \n {Do you want to make corrections, or discard these edits?}
	set ans [MyMessageBox -parent . -title "Invalid edits" \
		-message $msg -icon error -type "Correct Discard" \
		-default correct]
	if {$ans == "correct"} {
	    # if not, don't allow the mode/loop value to change
	    set CIF(editmode) 1
	    catch {
		$CIF(LoopSpinBox) setvalue @$CIF(lastLoopIndex)
	    }
	    return 1
	}
    }
    return 0
}

# showCIFbyTreeID is used in BrowseCIF to response to clicking on a tree widget
#   shows the contents data name or a loop
proc showCIFbyTreeID {name} {
    if {[CheckForCIFEdits]} return

    global CIF
    # code to allow multiple selection within loops
    #set loopname [lindex [$CIF(tree) itemcget $name -data] 1]
    #set addtolist 1
    #if {$loopname == "" || $loopname == "loop"} {set addtolist 0}
    #foreach n $CIF(treeSelectedList) {
	#if {$loopname != [lindex [$CIF(tree) itemcget $n -data] 1]} {
	#    set addtolist 0
	#    break
	#}
    #}
    #if {$addtolist} {
	#catch {$CIF(tree) itemconfigure $name -fill red}
	#lappend CIF(treeSelectedList) $name
    #} else {
	foreach n $CIF(treeSelectedList) {
	    catch {$CIF(tree) itemconfigure $n -fill black}
	}
	set CIF(treeSelectedList) $name
	# for some reason, BWidget sometimes has problems doing this: 
	# (but ignore the error)
	catch {$CIF(tree) itemconfigure $name -fill red}
	set CIF(lastShownTreeID) $name
	set pointer [$CIF(tree) itemcget $name -data]
	set dataname [lindex [$CIF(tree) itemcget $name -text] 0]
	showCIFbyDataname $pointer $dataname
    #}
}

proc showCIFbyDataname {pointer dataname "loopindex {}"} {
    global CIF CIFtreeindex
    set CIF(lastShownItem) [list $pointer $dataname]
    # remove the loop counter frame from window & edit buttons from that frame
    grid forget $CIF(LoopBar)
    pack forget $CIF(AddtoLoopButton) $CIF(DeleteLoopEntry)

    # delete old contents of frame
    set frame [$CIF(displayFrame) getframe]
    eval destroy [grid slaves $frame]
    # reset the scrollbars
    $CIF(displayFrame) xview moveto 0
    $CIF(displayFrame) yview moveto 0
    # leave room for a scrollbar
    grid columnconfig $frame 0 -minsize [expr \
	    [winfo width [winfo parent $frame]] - 20]
    if {$pointer == ""} {
	return
    }
    # create list of widgets defined here
    set CIF(widgetlist) {}

    # is this a looped data item?
    set block [lindex $pointer 0]
    if {[llength $pointer] == 2} {
	global $block
	# display contents of a rows of the loop
	if {[lindex $pointer 1] == "loop"} {
	    if {$CIF(editmode)} {
		pack $CIF(DeleteLoopEntry) -side right
		pack $CIF(AddtoLoopButton) -side right
		$CIF(AddtoLoopButton) config -command "AddToCIFloop ${block} $dataname"
	    }
	    set looplist [set ${block}($dataname)]
	    # get number of elements for first name
	    set names [llength [set ${block}([lindex $looplist 0])]]
	    # can't delete the only entry
	    if {$names == 1 && $CIF(editmode)} {
		$CIF(DeleteLoopEntry) configure -state disabled
	    } else {
		$CIF(DeleteLoopEntry) configure -state normal
	    }
	    $CIF(LoopSpinBox) configure -range "1 $names 1" \
		    -command    "ShowLoopVar ${block} $dataname" \
		    -modifycmd  "ShowLoopVar ${block} $dataname"
	    set CIF(lastLoopIndex) {}
	    if {$loopindex == ""} {
		$CIF(LoopSpinBox) setvalue first
	    } else {
		$CIF(LoopSpinBox) setvalue @$loopindex
	    }
	    # show the loop counter frame
	    grid $CIF(LoopBar) -sticky es -column 0 -row 1
	    set row 0
	    set i 0
	    ShowDictionaryDefinition $looplist
	    foreach var $looplist {
		incr i
		grid [TitleFrame $frame.$i -text $var -side left] \
			-column 0 -row $i -sticky ew
		set row $i
		set frame0 [$frame.$i getframe]
		DisplayCIFvalue $frame0.l $var 1 "" ${block}
		grid columnconfig $frame0 2 -weight 1
	    }
	    ShowLoopVar ${block} $dataname
	} else {
	    # look at a single looped variable
	    ShowDictionaryDefinition $dataname
	    grid [TitleFrame $frame.0 -text $dataname -side left] \
		    -column 0 -row 0 -sticky ew
	    set row 0
	    set i 0
	    set frame0 [$frame.0 getframe]
	    grid columnconfig $frame0 2 -weight 1
	    # maximum number of entries
	    set maxcols 100
	    catch {
		set maxcols $CIF(maxRows)
	    }
	    if {[set l [llength [set ${block}($dataname)]]] > $maxcols} {
		grid [label $frame0.a$i -justify left \
			-text "$dataname has $l entries, too many to display by column" \
			] -sticky w -column 0 -row $i
		return
	    }
	    foreach mark [set ${block}($dataname)] {
		incr i
		if {$i == 1} {$CIF(txt) see $mark.l}
		set value [StripQuotes [$CIF(txt) get $mark.l $mark.r]]	    
		grid [label $frame0.a$i -justify left -text $i]\
			-sticky w -column 0 -row $i
		DisplayCIFvalue $frame0.b$i $dataname $i $value ${block} $i
		#grid $frame0.b$i -sticky new -column 1 -row $i
	    }
	}
    } else {
	# unlooped data name
	global ${block}
	ShowDictionaryDefinition $dataname
	grid [TitleFrame $frame.0 -text $dataname -side left] \
		-column 0 -row 0 -sticky ew
	set row 0
	if {$dataname == "Parse-errors"} {
	    set value [set ${block}(errors)]
	} elseif {$dataname == "Validation-errors"} {
	    set value [set ${block}(validate)]
	} else {
	    set mark [set ${block}($dataname)]
	    set value [StripQuotes [$CIF(txt) get $mark.l $mark.r]]	    
	    $CIF(txt) see $mark.l
	}
	set frame0 [$frame.0 getframe]
	grid columnconfig $frame0 2 -weight 1
	DisplayCIFvalue $frame0.l $dataname "" $value $block
	#grid $frame0.l -sticky w -column 1 -row 0
    }
}

# redisplay the last entry shown in showCIFbyTreeID
# this is used if the edit mode ($CIF(editmode)) changes or if edits are saved
proc RepeatLastshowCIFvalue {} {
    global CIF
    if {[CheckForCIFEdits]} return
    set lastLoopIndex $CIF(lastLoopIndex)

    catch {
	eval showCIFbyDataname $CIF(lastShownItem)
	# if we are in a loop, display the element
	if {[lindex [lindex $CIF(lastShownItem) 0] 1] == "loop"} {
	    $CIF(LoopSpinBox) setvalue @$lastLoopIndex
	    ShowLoopVar [lindex [lindex $CIF(lastShownItem) 0] 0] \
		    [lindex $CIF(lastShownItem) 1]
	}
	
    }
}

# used in BrowseCIF in response to the spinbox
# show entries in a specific row of a loop
proc ShowLoopVar {array loop} {
    global $array CIF
    # check for unsaved changes here
    if {$CIF(lastLoopIndex) != ""} {
	if {[CheckForCIFEdits]} return
    }

    set looplist [set ${array}($loop)]
    set index [$CIF(LoopSpinBox) getvalue]
    if {$index < 0} {
	$CIF(LoopSpinBox) setvalue first
	set index [$CIF(LoopSpinBox) getvalue]
    } elseif {$index > [llength [set ${array}([lindex $looplist 0])]]} {
	$CIF(LoopSpinBox) setvalue last
	set index [$CIF(LoopSpinBox) getvalue]
    }
    set CIF(lastLoopIndex) $index
    set frame [$CIF(displayFrame) getframe]
    set i 0
    foreach var $looplist {
	incr i
	set mark [lindex [set ${array}($var)] $index]
	# ignore invalid entries -- should not happen
	if {$mark == ""} {
	    $CIF(LoopSpinBox) setvalue first
	    return
	}
	set value [StripQuotes [$CIF(txt) get $mark.l $mark.r]]	    
	if {$i == 1} {$CIF(txt) see $mark.l}
	if {$CIF(editmode)} {
	    global CIFeditArr CIFinfoArr
	    set widget [$frame.$i getframe].l
	    set CIFeditArr($widget) $value
	    switch [winfo class $widget] {
		Text {
		    $widget delete 0.0 end
		    $widget insert end $value
		}
		Entry {
		    $widget config -fg black
		}
	    }
	    set CIFinfoArr($widget) [lreplace $CIFinfoArr($widget) 2 2 $index]
	} else {
	    [$frame.$i getframe].l config -text $value
	}
    }
}

# scan a number in crystallographic uncertainty representation
# i.e.: 1.234(12), 1234(23), 1.234e-2(14),  -1.234-08(14), etc.
proc ParseSU {num} {
    # is there an error on this value?
    if {![regexp {([-+eEdD.0-9]+)\(([0-9]+)\)} $num x a err]} {
	set a $num
	set err {}
    }
    # parse off an exponent, if present
    if {[regexp {([-+.0-9]+)[EeDd]([-+0-9]+)} $a x a1 exp]} {
	# [+-]###.###e+## or [+-]###.###D-## etc.
	set a $a1
	# remove leading zeros from exponent
	regsub {([+-]?)0*([0-9]+)} $exp {\1\2} exp
    } elseif {[regexp {([-+.0-9]+)([-+][0-9]+)} $a x a1 exp]} {
	# [+-]###.###+## or [+-]###.###-## etc. [no 
	set a $a1
	# remove leading zeros from exponent
	regsub {([+-]?)0*([0-9]+)} $exp {\1\2} exp
    } else {
	set exp 0
    }
    # now parse the main number and count the digits after the decimal
    set a2 {}
    set a3 {}
    regexp {^([-+0-9]*)\.?([0-9]*)$} $a x a2 a3
    set l [string length $a3]

    set val .
    set error {}
    if {[catch {
	set val [expr ${a2}.${a3} * pow(10,$exp)]
	if {$err != ""} {
	    set error [expr $err*pow(10,$exp-$l)]
	}
    }]} {
	# something above was invalid
	if {$err != ""} {
	    return "$val ."
	} else {
	    return $val
	}
    }
    if {$error == ""} {
	return $val
    } else {
	return [list $val $error]
    }
}

# a stand-alone routine for testing: Select, read and browse a CIF
proc Read_BrowseCIF {} {
    global tcl_platform
    if {$tcl_platform(platform) == "windows"} {
	set filetypelist {
	    {"CIF files" .CIF} {"All files" *}
	}
    } else {
	set filetypelist {
	    {"CIF files" .CIF} {"CIF files" .cif} {"All files" *}
	}
    }    
    set file [tk_getOpenFile -parent . -filetypes $filetypelist]
    if {$file == ""} return
    if {![file exists $file]} return
    pleasewait "Reading CIF from file"
    set blocks [ParseCIF $file]
    if {$blocks == ""} {
	donewait
	MessageBox -parent . -type ok -icon warning \
		-message "Note: no valid CIF blocks were read from file $filename"
	return
    }
    catch {donewait}
    set allblocks {}
    for {set i 1} {$i <= $blocks} {incr i} {
	lappend allblocks $i
    }
    if {$allblocks != ""} {
	BrowseCIF $allblocks "" .cif
	# wait for the window to close
	tkwait window .cif
    } else {
	puts "no blocks read"
    }
    # clean up -- get rid of the CIF arrays
    for {set i 1} {$i <= $blocks} {incr i} {
	global block$i
	catch {unset block$i}
    }
}

# this takes a block of text, strips off the quotes ("", '', [] or ;;)
proc StripQuotes {value} {
    set value [string trim $value]
    if {[string range $value end-1 end] == "\n;" && \
	    [string range $value 0 0] == ";"} {
	return [string range $value 1 end-2]
    } elseif {[string range $value end end] == "\"" && \
	    [string range $value 0 0] == "\""} {
	set value [string range $value 1 end-1]
    } elseif {[string range $value end end] == "'" && \
	    [string range $value 0 0] == "'"} {
	set value [string range $value 1 end-1]
    } elseif {[string range $value end end] == {]} && \
	    [string range $value 0 0] == {[}} {
	set value [string range $value 1 end-1]
    }
    return $value
}

# replace a CIF value in with a new value.
# add newlines as needed to make sure the new value does not 
# exceed CIF(maxlinelength) [defaults to 80] characters/line
proc ReplaceMarkedText {txt mark value} {
    $txt configure -state normal
    # is this a multi-line string?
    set num [string first \n $value]
    set l [string length $value]
    # are there spaces in the string?
    set spaces [string first " " $value]
    # if no, are there any square brackets? -- treat them as requiring quotes
    if {$spaces == -1} {set spaces [string first {[} $value]}
    # are there any reserved strings inside $value? If so, it must be quoted
    if {$spaces == -1} {
	set tmp [string toupper $value]
	foreach s {DATA_ LOOP_ SAVE_ STOP_ GLOBAL_} {
	    if {[set spaces [string first $s $tmp]] != -1} break
	}
    }
    # are there quotes inside the string?
    set doublequote [string first "\"" $value]
    set singlequote [string first {'} $value]
    # if we have either type of quotes, use semicolon quoting
    if {$singlequote != -1 && $doublequote != -1} {set num $l}

    # lines longer than 78 characters with spaces need to be treated 
    # as multiline
    if {$num == -1 && $l > 77 && $spaces != -1} {
	set num $l
    }
    if {$num != -1} {
	set tmp {}
	if {[lindex [split [$txt index $mark.l] .] 1] != 0} {
	    append tmp \n
	}
	append tmp ";"
	if {$num > 78} {
	    append tmp \n
	} else {
	    append tmp " "
	}
	append tmp $value "\n;"
	# is there something else on the line?
	set restofline [$txt get $mark.r [lindex [split [$txt index $mark.r] .] 0].end]
	if {[string trim $restofline] != ""} {
	    append tmp \n
	}
	$txt delete ${mark}.l ${mark}.r
	$txt insert ${mark}.l $tmp
	$txt configure -state disabled
	return
    } elseif {($spaces != -1 || [string trim $value] == "") \
	    && $doublequote == -1} {
	# use doublequotes, unless doublequotes are present inside the string
	set tmp "\""
	append tmp $value "\""
    } elseif {$spaces != -1 || [string trim $value] == ""} {
	# use single quotes, since doublequotes are present inside the string
	set tmp {'}
	append tmp $value {'}
    } else {
	# no quotes needed
	set tmp $value
    }
    # is there room on the beginning of the line to add the string?
    set l [string length $tmp]
    set pos [lindex [split [$txt index $mark.l] .] 0]
    if {$l + [string length [$txt get $pos.0 $mark.l]] <= 79} {
	# will fit
	$txt delete ${mark}.l ${mark}.r
	$txt insert ${mark}.l $tmp
    } else {
	# no, stick a CR in front of string
	$txt delete ${mark}.l ${mark}.r
	$txt insert ${mark}.l \n$tmp
    }
    # is rest of the line after the inserted string still too long?
    set pos [lindex [split [$txt index $mark.r] .] 0]
    if {[string length [$txt get $pos.0 $pos.end]] > 79} {
	$txt insert $mark.r \n
    }
    $txt configure -state disabled
}

# return the dictionary definition for a list of CIF data names
proc GetCIFDefinitions {datanamelist} {
    global CIF_dataname_index
    set l {}
    # compile a list of definition pointers
    foreach dataname $datanamelist {
	set pointer {}
	catch {
	    set pointer [lindex $CIF_dataname_index($dataname) 0]
	}
	lappend l [list $dataname $pointer]
    }
    set l [lsort -index 1 $l]
    set pp {}
    set dictdefs {}
    set def {start}
    set nlist {}
    # merge items with duplicate definitions
    foreach item $l {
	# is this the first loop through?
	foreach {dataname pointer} $item {}
	if {$def == "start"} {
	    foreach {nlist pp} $item {}
	    set def [ReadCIFDefinition $pp]
	} elseif {$pp == $pointer} {
	    # same as last
	    lappend nlist $dataname
	} else {
	    # add the last entry to the list
	    set file [lindex $pp 0]
	    set pp $pointer
	    lappend dictdefs [list $nlist $def $file]
	    set nlist $dataname
	    if {$pointer == ""} {
		set def { Undefined dataname}
	    } else {
		# lookup name
		set def [ReadCIFDefinition $pointer]
	    }
	}
    }
    set file [lindex $pointer 0]
    lappend dictdefs [list $nlist $def $file]
    return $dictdefs
}

# read the CIF definition for a dataname. The pointer contains 3 values
# a filename, the number of characters from the start of the file and
# the length of the definition.
proc ReadCIFDefinition {pointer} {
    global CIF CIF_file_paths
    set file {}
    set loc {}
    set line {}
    foreach {file loc len} $pointer {}
    if {$file != "" && $loc != "" && $loc != ""} {
	set fp {}
	if {[array names CIF_file_paths $file] != ""} {
	    catch {set fp [open $CIF_file_paths($file) r]}
	    if {$fp == ""} return
	} elseif {[array names CIF_file_paths] != ""} {
	    return
	} else {
	    # support legacy applications using CIF(cif_path)
	    foreach path $CIF(cif_path) {
		catch {set fp [open [file join $path $file] r]}
		if {$fp != ""} break
	    }
	}
	if {$fp == ""} return
	fconfigure $fp -translation binary
	catch {
	    seek $fp $loc
	    set line [read $fp $len]
	    close $fp
	    # remove line ends & superfluous spaces
	    regsub -all {\n} [StripQuotes $line] { } line
	    regsub -all {\r} $line { } line
	    regsub -all {  +} $line { } line
#	    regsub -all {  +} [StripQuotes $line] { } line
	}
    }
    return $line
}

proc ValidateCIFName {dataname} {
    global CIF_dataname_index
    if {[
	catch {
	    set CIF_dataname_index($dataname)
	}
    ]} {return "warning: dataname $dataname not defined"}
}

# validates that a CIF value is valid for a specific dataname
proc ValidateCIFItem {dataname item} {
    global CIF_dataname_index CIF
    # maximum line length
    set maxlinelength 80
    catch {set maxlinelength $CIF(maxlinelength)}
    if {[catch {
	foreach {type range elist esd units category loopallow} [lindex $CIF_dataname_index($dataname) 1] {}
    }]} {return}
    if {$type == "c"} {
	# string type constant
	set item [StripQuotes $item]
	# is it enumerated?
	if {$elist != ""} {
	    # check it against the list of values
	    foreach i [concat $elist . ?] {
		if {[string tolower $item] == [string tolower [lindex $i 0]]} {return}
	    }
	    return "error: value \"$item\" is not an allowed option for $dataname"
	} else {
	    # check it for line lengths
	    set l 0
	    set err {}
	    foreach line [split $item \n] {
		incr l
		if {[string length $line] > $maxlinelength} {lappend err $l}
	    }
	    if {$err != ""} {return "error: line(s) $err are too long"}
	}
	return
    } elseif {$type == ""} {
	return "error: dataname $dataname is not used for CIF data items"
    } elseif {$type == "n"} {
	# validate numbers
	set unquoted [StripQuotes $item]
	if {$unquoted == "?" || $unquoted == "."} return
	if {$unquoted != $item} {
	    set err "\nwarning: number $item is quoted for $dataname"
	    set item $unquoted
	} else {
	    set err {}
	}
	set v $item
	# remove s.u., if allowed & present
	set vals [ParseSU $item]
	if {[set v [lindex $vals 0]] == "."} {
	    return "error: value \"$item\" is not a valid number for $dataname$err"
	}
	if {$esd} {
	    if {[lindex $vals 1] == "."} {
		return "error: value \"$item\" for $dataname has an invalid uncertainty (esd)$err"
	    }
	} elseif {[llength $vals] == 2} {
	    return "error: \"$item\" is invalid for $dataname, an uncertainty (esd) is not allowed$err"
	}

	# now validate the range
	if {$range != ""} {
	    # is there a decimal point in the range?
	    set integer 0
	    if {[string first . $range] == -1} {set integer 1}
	    # pull out the range
	    foreach {min max} [split $range :] {}
	    if {$integer && int($v) != $v} {
		return "warning: value \"$item\" is expected to be an integer for $dataname$err"
	    }
	    if {$min != ""} {
		if {$v < $min} {
		    return "error: value \"$item\" is too small for $dataname (allowed range $range)$err"
		}
	    }
	    if {$max != ""} {
		if {$v > $max} {
		    return "error: value \"$item\" is too big for $dataname(allowed range $range)$err"
		}
	    }
	}
	return $err
    }
    return {}
}

# displays the dictionary definitions in variable defs into a text widget
proc ShowDictionaryDefinition {defs} {
    global CIF
    set deflist [GetCIFDefinitions $defs]
    catch {
	$CIF(defBox) delete 1.0 end
	foreach d $deflist {
	    foreach {namelist definition file} $d {}
	    foreach n $namelist {
		$CIF(defBox) insert end $n dataname
		$CIF(defBox) insert end \n
	    }
	    $CIF(defBox) insert end \n
	    if {$definition == ""} {
		$CIF(defBox) insert end "No definition found\n\n"
	    } else {
		$CIF(defBox) insert end $definition
		$CIF(defBox) insert end "\n\[$file\]\n\n"
	    }

	}
	$CIF(defBox) tag config dataname -background yellow
    }
}

# create a widget to display a CIF value
proc DisplayCIFvalue {widget dataname loopval value block "row 0"} {
    global CIFeditArr CIFinfoArr
    global CIF CIF_dataname_index
    if {[
	catch {
	    foreach {type range elist esd units category loopallow} [lindex $CIF_dataname_index($dataname) 1] {}
	}
    ]} {
	set type c
	set elist {}
    }

    lappend CIF(widgetlist) $widget
    set CIFinfoArr($widget) {}

    if $CIF(editmode) {
	if {$loopval != ""} {
	    set widgetinfo [list $dataname $block [expr $loopval -1]]
	} else {
	    set widgetinfo [list $dataname $block 0]
	}
	set CIFeditArr($widget) $value
	set CIFinfoArr($widget) $widgetinfo

	if {$type == "n"} {
	    entry $widget -justify left -textvariable CIFeditArr($widget)
	    bind $widget <Leave> "CheckChanges $widget"
	    grid $widget -sticky nsw -column 1 -row $row
	    if {$units != ""} {
		set ws "${widget}u"
		label $ws -text "($units)" -bg yellow
		grid $ws -sticky nsw -column 2 -row $row
	    }
	} elseif {$elist != ""} {
	    set enum {}
	    foreach e $elist {
		lappend enum [lindex $e 0]
	    }
	    tk_optionMenu $widget CIFeditArr($widget) ""
	    FixBigOptionMenu $widget $enum "CheckChanges $widget"
	    AddSpecialEnumOpts $widget "CheckChanges $widget"
	    grid $widget -sticky nsw -column 1 -row $row
	} else {
	    # count the number of lines in the text
	    set nlines [llength [split $value \n]]
	    if {$nlines < 1} {
		set nlines 1
	    } elseif {$nlines > 10} {
		set nlines 10
	    }
	    set ws "${widget}s"
	    text $widget -height $nlines -width 80 -yscrollcommand "$ws set"
	    scrollbar $ws -command "$widget yview" -width 10 -bd 1
	    $widget insert end $value
	    bind $widget <Leave> "CheckChanges $widget"
	    if {$nlines > 1} {
		grid $ws -sticky nsew -column 1 -row $row
		grid $widget -sticky nsew -column 2 -row $row
	    } else {
		grid $widget -sticky nsew -column 1 -columnspan 2 -row $row
	    }
	}
    } else {
	label $widget -bd 2 -relief groove \
		-justify left -anchor w -text $value
	grid $widget -sticky nsw -column 1 -row $row
	if {$type == "n" && $units != ""} {
	    set ws "${widget}u"
	    label $ws -text "($units)" -bg yellow
	    grid $ws -sticky nsw -column 2 -row $row
	}
    }
}

# this is called to see if the user has changed the value for a CIF
# data item and to validate it.
#   save the change if $save is 1
#   return 1 if the widget contents has changed
proc CheckChanges {widget "save 0"} {
    global CIFeditArr CIFinfoArr CIF
    # maximum line length
    set maxlinelength 80
    catch {set maxlinelength $CIF(maxlinelength)}

    set CIF(errormsg) {}

    if {![winfo exists $widget]} return

    set dataname {}
    catch {
	foreach {dataname block index} $CIFinfoArr($widget) {}
    }
    # if this widget is a label, the info above will not be defined & checks are not needed
    if {$dataname == ""} {return 0}
    if {$dataname == "Parse-errors"} {return 0}
    if {$dataname == "Validation-errors"} {return 0}

    global ${block}
    set mark [lindex [set ${block}($dataname)] $index]
    if {$mark == ""} return
    set orig [StripQuotes [$CIF(txt) get $mark.l $mark.r]]

    # validate the entry
    set error {}
    set err {}
    switch [winfo class $widget] {
	Text {
	    set current [string trim [$widget get 1.0 end]]
	    set l 0
	    foreach line [set linelist [split $current \n]] {
		incr l
		if {[string length $line] > $maxlinelength} {
		    lappend err $l
		    lappend error "Error: line $l for $dataname is >$maxlinelength characters"
		}
	    }
	    if {$err != ""} {
		foreach l $err {
		    $widget tag add error $l.0 $l.end
		}
		$widget tag config error -foreground red
	    } else {
		$widget tag delete error
	    }
	    # see if box should expand
	    set clines [$widget cget -height]
	    if {$clines <= 2 && \
		    [string trim $orig] != [string trim $current]} {
		# count the number of lines in the text
		set nlines [llength $linelist]
		if {[lindex $linelist end] == ""} {incr nlines -1}
		if {$nlines == 2} {
		    $widget config -height 2
		} elseif {$nlines > 2} {
		    set i [lsearch [set s [grid info $widget]] -row]
		    set row [lindex $s [expr 1+$i]]
		    $widget config -height 3
		    set ws "${widget}s"
		    grid $ws -sticky nsew -column 1 -row $row
		    grid $widget -sticky nsew -column 2 -row $row
		}
	    }
	}
	Entry {
	    set current [string trim [$widget get]]
	    set err [ValidateCIFItem [lindex $CIFinfoArr($widget) 0] $current]
	    if {$err != "" && \
		    [string tolower [lindex $err 0]] != "warning:"} {
		lappend error $err
		$widget config -fg red
	    } else {
		$widget config -fg black
	    }
	}
	Menubutton {
	    set current $CIFeditArr($widget)
	}
	Label {
	    return 0
	}
    }
    if {[string trim $orig] != [string trim $current]} {
	if {$err != ""} {
	    set CIF(errormsg) $error
	} elseif {$save} {
	    SaveCIFedits $widget
	    return 0
	}
	return 1
    }
    return 0
}

# save the CIF edits into the CIF text widget
proc SaveCIFedits {widget} {
    global CIFeditArr CIFinfoArr CIF

    foreach {dataname block index} $CIFinfoArr($widget) {}
    global ${block}
    set mark [lindex [set ${block}($dataname)] $index]
    set orig [StripQuotes [$CIF(txt) get $mark.l $mark.r]]
    switch [winfo class $widget] {
	Text {
	    set current [string trim [$widget get 1.0 end]]
	}
	Entry {
	    set current [string trim [$widget get]]
	}
	Menubutton {
	    set current $CIFeditArr($widget)
	}
    }
    # save for undo & clear the redo list
    set CIF(redolist) {}
    if {[lindex [lindex $CIF(lastShownItem) 0] 1] == "loop"} {
	lappend CIF(undolist) [list $mark $orig \
		$CIF(lastShownItem) $CIF(lastShownTreeID) $CIF(lastLoopIndex)]
    } else {
	lappend CIF(undolist) [list $mark $orig \
		$CIF(lastShownItem) $CIF(lastShownTreeID)]
    }
    # count it
    incr CIF(changes)
    # make the change
    ReplaceMarkedText $CIF(txt) $mark $current
}

# add a new "row" to a CIF loop. At least for now, we only add at the end.
proc AddToCIFloop {block loop} {
    global $block CIF
    # check for unsaved changes here
    if {[CheckForCIFEdits]} return

    $CIF(txt) configure -state normal
    set looplist [set ${block}($loop)]
    set length [llength [set ${block}([lindex $looplist 0])]]
    # find the line following the last entry in the list
    set var [lindex $looplist end]
    set line [lindex [split [\
	    $CIF(txt) index [lindex [set ${block}($var)] end].r \
	    ] .] 0]
    incr line
    set epos $line.0
    $CIF(txt) insert $epos \n

    # insert a ? token for each entry & add to marker list for each variable
    set addlist {}
    foreach var $looplist {
	# go to next line?
	if {[string length \
		[$CIF(txt) get "$epos linestart" "$epos lineend"]\
		] > 78} {
	    $CIF(txt) insert $epos \n
	    set epos [$CIF(txt) index "$epos + 1c"]
	}
	$CIF(txt) insert $epos "? "
	incr CIF(markcount)
	$CIF(txt) mark set $CIF(markcount).l "$epos"
	$CIF(txt) mark set $CIF(markcount).r "$epos + 1c"
	$CIF(txt) mark gravity $CIF(markcount).l left
	$CIF(txt) mark gravity $CIF(markcount).r right
	set epos [$CIF(txt) index "$epos + 2c"]
	set index [llength [set ${block}($var)]]
	lappend ${block}($var) $CIF(markcount)
	lappend addlist [list $CIF(markcount) $var $index $block]
    }
    incr CIF(changes)
    lappend CIF(undolist) [list "loop add" $addlist \
	    $CIF(lastShownItem) $CIF(lastShownTreeID) $CIF(lastLoopIndex)]
    set CIF(redolist) {}

    # now show the value we have added
    set frame [$CIF(displayFrame) getframe]
    set max [lindex [$CIF(LoopSpinBox) cget -range] 1]
    incr max
    $CIF(LoopSpinBox) configure -range "1 $max 1"
    $CIF(LoopSpinBox) setvalue last
    ShowLoopVar $block $loop
    $CIF(txt) configure -state disabled
    $CIF(DeleteLoopEntry) configure -state normal
}

proc DeleteCIFRow {} {
    global CIF
    global CIFinfoArr CIFeditArr

    set delrow [$CIF(LoopSpinBox) getvalue]

    set msg {Are you sure you want to delete the following loop entries}
    append msg " (row number [expr 1+$delrow])?\n"
    set widget ""
    foreach widget $CIF(widgetlist) {
	set var [lindex $CIFinfoArr($widget) 0]
	append msg "\n$var\n\t"
	# get the value
	switch [winfo class $widget] {
	    Text {
		set value [string trim [$widget get 1.0 end]]
	    }
	    Entry {
		set value [string trim [$widget get]]
	    }
	    Menubutton {
		set value $CIFeditArr($widget)
	    }
	}
	append msg $value \n
    }
    if {$widget == ""} {
	error "this should not happen"
    }
    foreach {dataname block index} $CIFinfoArr($widget) {}
    global $block
    if {[llength [set ${block}($dataname)]] == 1} {
	MyMessageBox -parent . -title "Not only row" \
		-message {Sorry, this program is unable to delete all entries from a loop.} \
		-icon warning -type {Ignore} -default Ignore
	return
    }

    set ans [MyMessageBox -parent . -title "Delete Row?" \
		-message $msg \
		-icon question -type {Keep Delete} -default Keep]
    if {$ans == "keep"} {return}

    $CIF(txt) configure -state normal
    set deletelist {}
    foreach widget $CIF(widgetlist) {
	foreach {dataname block index} $CIFinfoArr($widget) {}
	global $block
	set mark [lindex [set ${block}($dataname)] $index]
	set orig [StripQuotes [$CIF(txt) get $mark.l $mark.r]]
	lappend deletelist [list $mark $dataname $index $block $orig]
	$CIF(txt) delete $mark.l $mark.r
	set ${block}($dataname) [lreplace [set ${block}($dataname)] $index $index]
    }
    set CIF(redolist) {}
    lappend CIF(undolist) [list "loop delete" $deletelist \
	    $CIF(lastShownItem) $CIF(lastShownTreeID) $CIF(lastLoopIndex)]
    # count it
    incr CIF(changes)

    $CIF(txt) configure -state disabled

    set max [lindex [$CIF(LoopSpinBox) cget -range] 1]
    incr max -1
    $CIF(LoopSpinBox) configure -range "1 $max 1"
    if {$index >= $max} {set index $max; incr index -1}
    $CIF(LoopSpinBox) setvalue @$index
    if {$max == 1} {$CIF(DeleteLoopEntry) configure -state disabled}
    # don't check for changes
    set CIF(lastLoopIndex) {}
    ShowLoopVar $block [lindex $CIF(lastShownItem) 1]
}

# display & highlight a line in the CIF text viewer
proc MarkGotoLine {line} {
    global CIF
    $CIF(txt) tag delete currentline
    $CIF(txt) tag add currentline $line.0 $line.end
    $CIF(txt) tag configure currentline -foreground blue
    $CIF(txt) see $line.0
}

# Extract a value from a CIF in the  CIF text viewer
proc ValueFromCIF {block item} {
    global $block CIF
    set val {}
    catch {
	set mark [set ${block}($item)]
	if {[llength $mark] == 1} {
	    set val [string trim [StripQuotes [$CIF(txt) get $mark.l $mark.r]]]
	} else {
	    foreach m $mark {
		lappend val [string trim [StripQuotes [$CIF(txt) get $m.l $m.r]]]
	    }
	}
    }
    return $val
}

proc UndoChanges {} {
    global CIF
    # save any current changes, if possible
    if {[CheckForCIFEdits]} return
    # are there edits to undo?
    if {[llength $CIF(undolist)] == 0} return

    foreach {mark orig lastShownItem lastShownTreeID lastLoopIndex} \
	    [lindex $CIF(undolist) end] {} 

    if {[llength $mark] == 1} {
	# get the edited value
	set edited [StripQuotes [$CIF(txt) get $mark.l $mark.r]]
	# make the change back
	ReplaceMarkedText $CIF(txt) $mark $orig
	# add this undo to the redo list
	lappend CIF(redolist) [list $mark $edited $lastShownItem \
		$lastShownTreeID $lastLoopIndex]
    } elseif {[lindex $mark 1] == "add"} {
	set deletelist {}
	$CIF(txt) configure -state normal
	foreach m $orig {
	    foreach {mark dataname index block} $m {}
	    # get the inserted value
	    set edited [StripQuotes [$CIF(txt) get $mark.l $mark.r]]	
	    $CIF(txt) delete $mark.l $mark.r
	    lappend deletelist [list $mark $dataname $index $block $edited]
	    global $block
	    set ${block}($dataname) [lreplace [set ${block}($dataname)] $index $index]
	}
	$CIF(txt) configure -state disabled
	# add this action to the redo list
	lappend CIF(redolist) [list "loop delete" $deletelist \
		$lastShownItem $lastShownTreeID $lastLoopIndex]
    } elseif {[lindex $mark 1] == "delete"} {
	set addlist {}
	foreach m $orig {
	    foreach {mark dataname index block orig} $m {}
	    # make the change back
	    ReplaceMarkedText $CIF(txt) $mark $orig
	    lappend addlist [list $mark $dataname $index $block]
	    global $block
	    set ${block}($dataname) [linsert [set ${block}($dataname)] $index $mark]
	}
	# show the entry that was added
	set lastLoopIndex $index
	# add this last entry to the redo list
	lappend CIF(redolist) [list "loop add" $addlist \
		$lastShownItem $lastShownTreeID $lastLoopIndex]
    }

    # drop the action from the undo list
    set CIF(undolist) [lreplace $CIF(undolist) end end]
    # count back
    incr CIF(changes) -1
    # scroll on the tree
    $CIF(tree) see $lastShownTreeID
    eval showCIFbyDataname $lastShownItem

    # if we are in a loop, display the element
    if {[lindex [lindex $lastShownItem 0] 1] == "loop"} {
	$CIF(LoopSpinBox) setvalue @$lastLoopIndex
	ShowLoopVar [lindex [lindex $lastShownItem 0] 0] \
		[lindex $lastShownItem 1]
    }
}


proc RedoChanges {} {
    global CIF
    # save any current changes, if possible
    if {[CheckForCIFEdits]} return
    # are there edits to redo?
    if {[llength $CIF(redolist)] == 0} return

    foreach {mark edited lastShownItem lastShownTreeID lastLoopIndex} \
	    [lindex $CIF(redolist) end] {} 

    if {[llength $mark] == 1} {
	# get the edited value
	set orig [StripQuotes [$CIF(txt) get $mark.l $mark.r]]
	# make the change back
	ReplaceMarkedText $CIF(txt) $mark $edited
	# add this action back to the undo list
	lappend CIF(undolist) [list $mark $orig $lastShownItem \
		$lastShownTreeID $lastLoopIndex]
	# count up
	incr CIF(changes)
    } elseif {[lindex $mark 1] == "add"} {
	set deletelist {}
	$CIF(txt) configure -state normal
	foreach m $edited {
	    foreach {mark dataname index block} $m {}
	    # get the inserted value
	    set edited [StripQuotes [$CIF(txt) get $mark.l $mark.r]]	
	    $CIF(txt) delete $mark.l $mark.r
	    lappend deletelist [list $mark $dataname $index $block $edited]
	    global $block
	    set ${block}($dataname) [lreplace [set ${block}($dataname)] $index $index]
	}
	$CIF(txt) configure -state disabled
	# add this action back to the undo list
	lappend CIF(undolist) [list "loop delete" $deletelist \
		$lastShownItem $lastShownTreeID $lastLoopIndex]
	# count up
	incr CIF(changes)
    } elseif {[lindex $mark 1] == "delete"} {
	set addlist {}
	foreach m $edited {
	    foreach {mark dataname index block orig} $m {}
	    # make the change back
	    ReplaceMarkedText $CIF(txt) $mark $orig
	    lappend addlist [list $mark $dataname $index $block]
	    global $block
	    set ${block}($dataname) [linsert [set ${block}($dataname)] $index $mark]
	}
	# show the entry that was added
	set lastLoopIndex $index
	# add this action back to the undo list
	lappend CIF(undolist) [list "loop add" $addlist \
		$lastShownItem $lastShownTreeID $lastLoopIndex]
	# count up
	incr CIF(changes)
    }
    
    # drop the action from the redo list
    set CIF(redolist) [lreplace $CIF(redolist) end end]
    # scroll on the tree
    $CIF(tree) see $lastShownTreeID
    eval showCIFbyDataname $lastShownItem
    
    # if we are in a loop, display the element
    if {[lindex [lindex $lastShownItem 0] 1] == "loop"} {
	$CIF(LoopSpinBox) setvalue @$lastLoopIndex
	ShowLoopVar [lindex [lindex $lastShownItem 0] 0] \
		[lindex $lastShownItem 1]
    }
}

# create a category browser to select a single CIF item (mode=single) 
# or to populate a loop_ (mode=multiple)
proc CatBrowserWindow {parent "mode multiple"} {
    global CIF CIF_dataname_index
    global catlist
    if {$mode == "multiple"} {
	set CIF(catselectmode) 1
    } else {
	set CIF(catselectmode) 0
    }
    set CIF(CategoryBrowserWin) [set frame $parent.catselect]
    if {[winfo exists $frame]} {
	set CIF(searchtext) ""
	# the window exists so go ahead and use it
	set CIF(SelCat) {}
	set CIF(CatSelList) {}
	set CIF(CatSelItems) {}
	wm deiconify $frame
	$CIF(cattree) selection clear
	tkwait variable CIF(CatSelectDone)
	wm withdraw $frame
	return
    }
    catch {unset catlist}
    set CIF(searchtext) ""
    pleasewait "building category window" "" $parent
    # create an index by category
    foreach name [lsort [array names CIF_dataname_index]] {
	set category [lindex [lindex $CIF_dataname_index($name) 1] 5]
	lappend catlist($category) $name
    }
    catch {destroy $frame}
    toplevel $frame
    wm withdraw $frame
    wm title $frame "CIF Category Browser"
    wm protocol $frame WM_DELETE_WINDOW "set CIF(CatSelItems) {}; set CIF(CatSelectDone) Q"
    if {$CIF(catselectmode)} {
	set text "Select one or more data names in a\nsingle category to create a new loop"
    } else {
	set text "Select a single data name to add to the CIF"
    }
    grid [frame $frame.top -bg beige] -sticky news -column 0 -row 0
    grid columnconfigure $frame.top 0 -weight 1
    grid columnconfigure $frame.top 1 -pad 10
    grid [label $frame.top.1 -text $text -bg beige] \
	    -sticky news -column 0 -row 0 
    grid [set CIF(usebutton) [button $frame.top.use -text "Insert" \
	    -command "set CIF(CatSelectDone) done" \
	    -state disabled]] -column 1 -row 0
    grid [frame $frame.bot] -sticky news -column 0 -row 2
    grid [label $frame.bot.txt -text "Enter search text:"] \
	    -column 0 -row 1
    grid [entry $frame.bot.e -textvariable CIF(searchtext)] \
	    -column 1 -row 1
    bind $frame.bot.e <Return> CatLookupName
    grid [button $frame.bot.src -text "Search" \
	    -command CatLookupName] -column 2 -row 1
    grid [button $frame.bot.next -text "Next" -command ShowNextcatSearch] \
	    -column 3 -row 1
    grid [button $frame.bot.q -text Quit \
	    -command "set CIF(CatSelItems) {}; set CIF(CatSelectDone) Q"\
	    ] -column 5 -row 1
    set sw    [ScrolledWindow $frame.lf]
    $frame.lf configure -relief sunken -borderwidth 2
    set CIF(cattree) [Tree $sw.tree -relief flat -borderwidth 0 -width 45 \
	    -highlightthickness 0 -redraw 1 -height 20]
    # get the size of the font and adjust the line spacing accordingly
    catch {
	set font [option get $CIF(cattree) font Canvas]
	$CIF(cattree) configure -deltay [font metrics $font -linespace]
    }
    grid $sw -sticky news -column 0 -row 1 
    grid columnconfigure $frame 0 -minsize 275 -weight 1
    grid rowconfigure $frame 1 -weight 1
    $sw setwidget $CIF(cattree)
    
    bind $frame <KeyPress-Prior> "$CIF(cattree) yview scroll -1 page"
    bind $frame <KeyPress-Next> "$CIF(cattree) yview scroll 1 page"
    bind $frame <KeyPress-Up> "$CIF(cattree) yview scroll -1 unit"
    bind $frame <KeyPress-Down> "$CIF(cattree) yview scroll 1 unit"
    bind $frame <KeyPress-Home> "$CIF(cattree) yview moveto 0"
    #bind $frame <KeyPress-End> "$CIF(cattree) yview moveto end"
    # -- does not work
    bind $frame <KeyPress-End> "$CIF(cattree) yview scroll 99999999 page"
    $CIF(cattree) see 0

    # Bwidget seems to have problems with the name "1", so avoid it
    set num 100
    set n 0
    global catCIFindex
    catch {unset catCIFindex}
    set normalfont [option get [winfo toplevel $CIF(cattree)] font Canvas]
    set italic "$font italic"
    foreach cat [lsort [array names catlist]] {
	if {$cat == ""} continue
	$CIF(cattree) insert end root cat$n -text $cat \
		-open 0 -image [Bitmap::get folder]
	foreach item [lsort $catlist($cat)] {
	    set loop [lindex [lindex $CIF_dataname_index($item) 1] 6]
	    if {$loop || !$CIF(catselectmode)} {
		set font $normalfont
		set sel 1
	    } else {
		set font $italic
		set sel 0
	    }
	    $CIF(cattree) insert end cat$n [incr num] -text $item \
		    -image [Bitmap::get file] -selectable $sel -font $font
	    set catCIFindex($item) $num
	}
	incr n
    }
    # set code to respond to mouse clicks
    $CIF(cattree) bindImage <1> selectCat
    $CIF(cattree) bindText <1>  selectCat
    $CIF(cattree) bindImage <Control-1> {}
    $CIF(cattree) bindText <Control-1>  {}
    
    set CIF(SelCat) {}
    set CIF(CatSelList) {}
    set CIF(CatSelItems) {}
    donewait
    wm deiconify $frame
    tkwait variable CIF(CatSelectDone)
    wm withdraw $frame
}

# respond to a selection event in CatBrowserWindow
proc selectCat {item} {
    global CIF
    # ignore selected category items
    if {[string first cat $item] == 0} {return}
    set name [$CIF(cattree) itemcget $item -text]
    set category [$CIF(cattree) itemcget [$CIF(cattree) parent $item] -text]
    if {!$CIF(catselectmode)} {
	# single selection mode
	set CIF(SelCat) $category
	set CIF(CatSelList) $item
    } elseif {$CIF(SelCat) != $category} {
	# new category
	set CIF(SelCat) $category
	set CIF(CatSelList) $item
    } elseif {[set ind [lsearch $CIF(CatSelList) $item]] >= 0} {
	# toggle 
	set CIF(CatSelList) [lreplace $CIF(CatSelList) $ind $ind]
    } else {
	# add to category
	lappend CIF(CatSelList) $item
    }
    if {[llength $CIF(CatSelList)] == 0} {
	$CIF(cattree) selection clear
    } else {
	eval $CIF(cattree) selection set $CIF(CatSelList)
    }
    set CIF(CatSelItems) {}
    foreach node $CIF(CatSelList) {
	lappend CIF(CatSelItems) [$CIF(cattree) itemcget $node -text]
    }
    if {$CIF(CatSelItems) != ""} {
	ShowDictionaryDefinition $CIF(CatSelItems)
	$CIF(usebutton) configure -state normal
    } else {
	$CIF(usebutton) configure -state disabled
    }
}

# search through the category browser for a string
proc CatLookupName {} {
    global CIF catCIFindex
    pleasewait "performing search" "" [winfo toplevel $CIF(cattree)]

    set str $CIF(searchtext)
    # close all nodes
    foreach node [$CIF(cattree) nodes root] {
	$CIF(cattree) closetree $node
    }
    set catsearchlist {}
    set namelist [array names catCIFindex *[string tolower $str]*]
    if {[llength $namelist] == 0} {
	MyMessageBox -parent [winfo toplevel $CIF(cattree)] \
		-title "Not found" \
		-message "String not found" -icon warning -type OK \
		-default ok
    }
    foreach name $namelist {
	set node $catCIFindex($name)
	lappend catsearchlist $node
	set pnode [$CIF(cattree) parent $node]
	$CIF(cattree) opentree $pnode
    }
    set CIF(catsearchlist) [lsort -integer $catsearchlist]
    set CIF(catsearchnum) -1
    donewait
    # find 1st element
    ShowNextcatSearch
}

# successively display located data items in the category browser
proc ShowNextcatSearch {} {
    global CIF
    $CIF(usebutton) configure -state disabled
    set node [lindex $CIF(catsearchlist) [incr CIF(catsearchnum)]]
    if {$node == ""} {
	set CIF(catsearchnum) 0
	set node [lindex $CIF(catsearchlist) 0]
    }
    if {$node == ""} {
	$CIF(cattree) selection set
	return
    }
    ShowDictionaryDefinition [$CIF(cattree) itemcget $node -text]
    $CIF(cattree) see $node
    $CIF(cattree) selection set $node
}

# create a data item browser to select a single CIF item
#
proc CatListWindow {parent} {
    global CIF CIF_dataname_index
    global catlist
    set CIF(searchtext) ""
    set frame $parent.catselect
    catch {destroy $frame}
    toplevel $frame
    wm title $frame "CIF Data Name Browser"
    grid [label $frame.top -text "Select a CIF data name to add" \
	    -bd 2 -bg beige -relief raised] \
	    -sticky news -column 0 -row 0  -columnspan 3
    grid [label $frame.top1 -text "Dictionary" -bg beige -anchor w] \
	    -sticky news -column 0 -row 1  -columnspan 2
    grid [label $frame.top2 -text "Data name" -bg beige -anchor w] \
	    -sticky news -column 2 -row 1 
    grid [frame $frame.bot] -sticky news -column 0 -row 3 -columnspan 3
    grid [label $frame.bot.txt -text "Enter search text:"] \
	    -column 0 -row 1
    grid [entry $frame.bot.e -textvariable CIF(searchtext)] \
	    -column 1 -row 1
    bind $frame.bot.e <Return> CatFindMatchingNames
    grid [button $frame.bot.src -text "Search" \
	    -command CatFindMatchingNames] -column 2 -row 1
    grid [checkbutton $frame.bot.sort -text "Sort by dict." \
	    -variable CIF(sortbydict) \
	    -command CatFindMatchingNames] -column 3 -row 1
    grid [set CIF(usebutton) [button $frame.bot.use -text "Insert" \
	    -command "destroy $frame"]] -column 4 -row 1
    grid [button $frame.bot.q -text Quit \
	    -command "set CIF(CatSelItems) {}; destroy $frame"] -column 5 -row 1
    grid [set CIF(catlist) [listbox $frame.list -width 55 \
	    -height 20 -exportselection 0 \
	    -yscrollcommand "syncLists $frame.list $frame.dict $frame.ys yview"\
	    ]] -column 2 -row 2 -sticky nsew
    grid [set CIF(dictlist) [listbox $frame.dict -width 12 \
	    -height 20 -exportselection 0 \
	    -yscrollcommand "syncLists $frame.dict $frame.list $frame.ys yview"\
	    ]] -column 0 -row 2 -sticky nsew
    grid [scrollbar $frame.ys -width 15 -bd 2 \
	    -command "moveLists \[list $frame.list $frame.dict] yview" \
	    ] -column 1 -row 2  -sticky ns

    bind $CIF(catlist) <<ListboxSelect>> \
	    "ListSelectedCmd $CIF(catlist) $CIF(dictlist); SetSelectedCmd $CIF(catlist)"
    bind $CIF(dictlist) <<ListboxSelect>> \
	    "ListSelectedCmd $CIF(dictlist) $CIF(catlist); SetSelectedCmd $CIF(catlist)"
    grid columnconfigure $frame 2 -minsize 275 -weight 1
    grid rowconfigure $frame 2 -weight 1
    
    bind $frame <KeyPress-Prior> "$CIF(catlist) yview scroll -1 page"
    bind $frame <KeyPress-Next> "$CIF(catlist) yview scroll 1 page"
    bind $frame <KeyPress-Up> "$CIF(catlist) yview scroll -1 unit"
    bind $frame <KeyPress-Down> "$CIF(catlist) yview scroll 1 unit"
    bind $frame <KeyPress-Home> "$CIF(catlist) yview moveto 0"
    bind $frame <KeyPress-End> "$CIF(catlist) yview moveto end"
    $CIF(catlist) see 0

    CatFindMatchingNames
    tkwait window $frame
}

# 
# populate the data item browser created in CatListWindow
proc CatFindMatchingNames {} {
    global CIF CIF_dataname_index
    set str $CIF(searchtext)
    set searchlist {}
    foreach name [array names CIF_dataname_index *[string tolower $str]*] {
	lappend searchlist [list $name [lindex [lindex $CIF_dataname_index($name) 0] 0]]
    }
    $CIF(catlist) delete 0 end
    $CIF(dictlist) delete 0 end
    set searchlist [lsort -index 0 $searchlist]
    if {$CIF(sortbydict)} {set searchlist [lsort -index 1 $searchlist]}
    foreach item $searchlist {
	foreach {name dict} $item {}
	$CIF(catlist) insert end $name
	$CIF(dictlist) insert end $dict
    }
    $CIF(usebutton) configure -state disabled
}

# replicate selection between list boxes
# list must be config'ed -exportselection 0
proc ListSelectedCmd {master slaves} {
    global CIF
    foreach slave $slaves {
	$slave selection clear 0 end
	$slave selection set [$master curselection]
    }
    $CIF(usebutton) configure -state normal
}

proc SetSelectedCmd {itemlist} {
    global CIF
    set CIF(CatSelItems) [$itemlist get [$itemlist curselection]]
    ShowDictionaryDefinition $CIF(CatSelItems)
}

# sync one or more slaved listboxes to a master
# cmd is xview or yview
proc syncLists {master slaves scroll cmd args} {
    foreach slave $slaves {
	$slave $cmd moveto [lindex [$master $cmd] 0]
    }
    eval $scroll set $args
}

# move multiple listboxes based on a single scrollbar
# cmd is xview or yview
proc moveLists {listlist cmd args} {
    foreach list $listlist { 
	eval $list $cmd $args
    }
}

# insert a data item into block $blk
proc InsertDataItem {dataname blk "value ?"} {
    global CIF
    global $blk

    # find the last data item in the CIF 
    set txt $CIF(txt)
    set last [set ${blk}(lastmark)]
    set i [$txt index $last.r]
    # insert the new dataname right after the last data item
    $txt config -state normal
    $txt insert $i "\n$dataname        " x $value y
    # reposition the mark for the original last data item in case it moved
    $txt mark set $last.r $i
    $txt mark gravity $last.r right
    # convert the tags around $value to marks
    foreach {pos epos} [$txt tag range y] {}
    $txt tag delete x y
    incr CIF(markcount)
    $txt mark set $CIF(markcount).l $pos
    $txt mark set $CIF(markcount).r $epos
    $txt mark gravity $CIF(markcount).l left
    $txt mark gravity $CIF(markcount).r right
    $txt config -state disabled
    set ${blk}($dataname) $CIF(markcount)
    # this is now the last data item in block
    set ${blk}(lastmark)  $CIF(markcount)
    # show the data item in the CIF text
    $txt see $CIF(markcount).r
    # add & show the data item in the tree; open for editing
    set num [incr CIF(tree_lastindex)]
    $CIF(tree) insert end $blk $num -text $dataname \
	    -image [Bitmap::get file] -data $blk
    $CIF(tree) see $num
    set CIF(editmode) 1
    showCIFbyTreeID $num
    # register this as a change
    incr CIF(changes)
    # can't undo this so clear the undo status
    set CIF(undolist) {}
    set CIF(redolist) {}
}

# insert a loop into CIF block $blk
proc InsertDataLoop {namelist blk} {
    global CIF CIF_dataname_index
    global $blk

    # find the last data item in the CIF 
    set txt $CIF(txt)
    set last [set ${blk}(lastmark)]
    set i [$txt index $last.r]
    # insert the new dataname right after the last data item
    $txt config -state normal
    # get the last loop number
    regsub -all "loop_" [array names $blk loop*] "" l
    set n [lindex [lsort -integer $l] end]
    incr n
    # insert the loop into the CIF
    $txt insert $i "\nloop_" x
    foreach name $namelist {
	set epos [lindex [$txt tag range x] end]
	$txt tag delete x
	$txt insert $epos "\n   $name" x
	lappend ${blk}(loop_$n) $name
	set ${blk}($name) {}
    }
    set epos [lindex [$txt tag range x] end]
    $txt tag delete x
    $txt insert $epos "\n     " x
    set epos [lindex [$txt tag range x] end]
    $txt tag delete x
    set catlist {}
    # insert a value for each data name
    foreach name $namelist {
	set epos [$txt index "$epos lineend"] 
	if {[lindex [split $epos .] 1] > 70} {
	    $txt insert $epos "\n     " x
	    set epos [lindex [$txt tag range x] end]
	    $txt tag delete x
	    set epos [$txt index "$epos lineend"] 
	}
	$txt insert $epos ? y " " x
	# convert the tags around the "?" to marks
	foreach {pos epos} [$txt tag range y] {}
	$txt tag delete x y
	incr CIF(markcount)
	$txt mark set $CIF(markcount).l $pos
	$txt mark set $CIF(markcount).r $epos
	$txt mark gravity $CIF(markcount).l left
	$txt mark gravity $CIF(markcount).r right
	lappend ${blk}($name) $CIF(markcount)
	# get the category
	set category {}
	catch {
	    set category [lindex \
		    [lindex $CIF_dataname_index($name) 1] 5]
	}
	if {$category != "" && [lsearch $catlist $category] == -1} {
	    lappend catlist $category
	}
    }
    # this is now the last data item in block
    set ${blk}(lastmark)  $CIF(markcount)
    # reposition the mark for the original last data item in case it moved
    $txt mark set $last.r $i
    $txt mark gravity $last.r right
    $txt config -state disabled
    # show the data item in the CIF text
    $txt see $CIF(markcount).r
    # add & show the data item in the tree; open for editing
    $CIF(tree) insert end $blk ${blk}loop_$n \
	    -text "loop_$n ($catlist)" -open 1 \
	    -image [Bitmap::get copy] -data "$blk loop"
    # insert a value for each data name
    foreach name $namelist {
	$CIF(tree) insert end ${blk}loop_$n [incr CIF(tree_lastindex)] \
		-text $name \
		-image [Bitmap::get file] -data $blk
    }
    $CIF(tree) see $CIF(tree_lastindex)
    set CIF(editmode) 1
    showCIFbyTreeID ${blk}loop_$n
    # register this as a change
    incr CIF(changes)
    # can't undo this so clear the undo status
    set CIF(undolist) {}
    set CIF(redolist) {}
}

# add an item to a CIF 
proc AddDataItem2CIF {mode parent} {
    global CIF
    if {[llength $CIF(blocklist)] == 1} {
	set block block$CIF(blocklist)
    } else {
	# select a block here
	set frame $parent.blksel
	catch {destroy $frame}
	toplevel $frame
	wm title $frame "Select a block"
	grid [label $frame.top -text "Select the data block where\nitems will be added" \
	    -bd 2 -bg beige -relief raised] \
	    -sticky news -column 0 -row 0  -columnspan 3
	grid [listbox $frame.list -width 30 \
		-height 20 -exportselection 0 \
		-yscrollcommand "$frame.ys set"] -column 0 -row 2 -sticky nsew
	grid [scrollbar $frame.ys -width 15 -bd 2 \
		-command "$frame.list yview"] -column 1 -row 2  -sticky ns
	grid [frame $frame.bot] -sticky news -column 0 -row 3 -columnspan 3
	grid [button $frame.bot.use -text Use -state disabled \
	    -command "destroy $frame"] -column 4 -row 1
	grid [button $frame.bot.q -text Quit \
		-command "set CIF(selectedBlock) {}; destroy $frame"\
		] -column 5 -row 1
	foreach n $CIF(blocklist) {
	    global block${n}
	    set blockname [set block${n}(data_)]
	    $frame.list insert end "($n) $blockname"
	}
	bind $frame.list <<ListboxSelect>> \
	    "BlockSelectedCmd $frame.list $frame.bot.use"
	bind $frame.list <Double-1> "destroy $frame"
	putontop $frame
	tkwait window $frame
	afterputontop
	if {$CIF(selectedBlock) == ""} return
	set block block$CIF(selectedBlock)
    }
    if {$mode == "loop"} {
	# open a browser window
	CatBrowserWindow $parent
	if {$CIF(CatSelItems) == ""} return
	InsertDataLoop $CIF(CatSelItems) $block
    } elseif {$mode == "category"} {
	# open a browser window to select a single data item
	CatBrowserWindow $parent single
	if {[llength $CIF(CatSelItems)] != 1} return
	InsertDataItem $CIF(CatSelItems) $block
    } else {
	CatListWindow $parent
	if {[llength $CIF(CatSelItems)] != 1} return
	InsertDataItem $CIF(CatSelItems) $block
    }
}

# respond to selection of a block, when needed
proc BlockSelectedCmd {listbox usebutton} {
    global CIF
    set selected [$listbox curselection]
    if {[llength $selected] == 1} {
	$usebutton configure -state normal
	set CIF(selectedBlock) [lindex [split [$listbox get $selected] "()"] 1]
    } else {
	$usebutton configure -state disabled
	set CIF(selectedBlock) {}
    }
}
#----------------------------------------------------------------------
#----------------------------------------------------------------------
# index and manage dictionaries
#----------------------------------------------------------------------

# parse a CIF dictionary & save pertinent bits (more for DDL1 than DDL2)
proc MakeCIFdictIndex {f message} {
    global CIF
    set top1 .mkDictIndexTop
    set stat .mkDictIndexStat
    # create an invisible window for parsing a dictionary
    catch {destroy $top1}
    toplevel $top1
    set txt $top1.t
    grid [text $txt -width 80 -yscrollcommand "$top1.s set"] -column 0 -row 0
    grid [scrollbar $top1.s -command "$txt yview"] -column 1 -row 0 -sticky ns
    wm withdraw $top1
    # create a status window
    catch {destroy $stat}
    toplevel $stat
    wm title $stat "Dictionary Parse Status"
    if {$message != ""} {
	grid [label $stat.l0 -text $message] -column 0 -columnspan 2 -row 0
    }
    grid [label $stat.l1 -text "Definitions Processed"] -column 0 -row 1
    grid [label $stat.l2 -textvariable parsestatus] -column 1 -row 1
    putontop $stat 1
    update

    set counter 0

    set file [file tail $f]
    global parsestatus
    set parsestatus "$counter (reading $file)" 
    update

    if {[catch {
	set inp [open $f r]
	fconfigure $inp -translation binary
    } errmsg]} {
	catch {close $inp}
	destroy $stat $top1
	return [list 1 $errmsg]
    }

    # input file is open, can we write to the index?
    set errorstat 0
    if {[catch {
	set fp [open ${f}_index w]
	puts $fp "set CIF_file_name [list $file]"
	puts $fp "set CIF_file_size [file size $f]"
	puts $fp "set CIF_index_version $CIF(indexversion)"
    } errmsg]} {
	set errorstat 2
	catch {close $fp}
	catch {file delete -force ${f}_index}
	set ::CIF_file_paths($file) $f
    }
    
    set text [read $inp]
    close $inp
    # is this a DDL2 dictionary (with save frames)?
    if {[string match -nocase "*save_*" $text]} {
	set DDL2 1
	regsub -all "save__" $text "data__" text
	regsub -all "save_" $text "####_" text
    } else {
	set DDL2 0
    }
    $txt insert end $text
    # free up some memory
    unset text

    set parsestatus "$counter (starting parse)" 
    update


    set blocks [ParseCIF $txt {} CIFdict]
    set allblocks {}
    set prevpos 1.0
    set prevbytes 0
    set parsestatus "$counter (parse complete)" 
    update

    if {$errorstat == 0} {
	puts $fp "set CIF_file_mtime [file mtime $f]"
	puts $fp "array set CIF_dataname_index \{"
    }
    set definednames {}
    for {set i 1} {$i <= $blocks} {incr i} {
	incr counter
	if {$counter % 10 == 0} {
	    set parsestatus $counter
	    update
	}
	lappend allblocks $i
	if {![catch {set CIFdict::block${i}(errors)}]} {
	    puts stderr "Block $i ([set CIFdict::block${i}(data_)]) errors:"
	    puts stderr "[set CIFdict::block${i}(errors)]"
	}
	# list of positions for dataname
	set list {}
	catch {set list [set CIFdict::block${i}(_name)]}
	if {$list == "" && $DDL2} { 
	    catch {set list [set CIFdict::block${i}(_item.name)]}
	}
	# definition entry
	set def {}
	catch {set def  [set CIFdict::block${i}(_definition)]}
	if {$def == "" && $DDL2} { 
	    catch {set def  [set CIFdict::block${i}(_item_description.description)]}
	} 
	if {$def == ""} continue
	if {[llength $def] != 1} {puts stderr "problem with [set CIFdict::block${i}(data_)]"}
	# count the number of bytes from the previous position
	# (much faster than counting from the beginning each time)
	#set defpos [string length [$txt get 1.0 $def.l]]
	set defpos [string length [$txt get $prevpos $def.l]]
	incr defpos $prevbytes
	set prevpos $def.l
	set prevbytes $defpos
	set deflen [string length [$txt get $def.l $def.r]]
	# item type (numb/char/null)
	set type {}
	catch {set type [set CIFdict::block${i}(_type)]}
	if {$type == "" && $DDL2} {
	    catch {set type [set CIFdict::block${i}(_item_type.code)]}
	    if {[llength $type] != 1} {
		set typeval "?"
	    } else {
		set typeval [StripQuotes [$txt get $type.l $type.r]]
	    }
	    # mmCIF uses: atcode, code, float, int, line, symop, text
	    #             uchar1, uchar3, ucode, uline, yyyy-mm-dd
	    # treat everything but float & int as character
	    if {$typeval == "float" || $typeval == "int"} {
		set typeval "n"
	    } else {
		set typeval "c"
	    }
	} elseif {[llength $type] != 1} {
	    puts stderr "type problem for [set CIFdict::block${i}(data_)]"
	    set typeval "?"
	} else {
	    set typeval [StripQuotes [$txt get $type.l $type.r]]
	    if {$typeval == "numb"} {
		set typeval "n"
	    } elseif {$typeval == "char"} {
		set typeval "c"
	    } elseif {$typeval == "null"} {
		set typeval ""
	    } else {
		puts stderr "Block [set CIFdict::block${i}(data_)] has invalid _type ($typeval)"
		set typeval "?"
	    }
	}
	# flag if esd's are allowed
	set pos {}
	catch {set pos [set CIFdict::block${i}(_type_conditions)]}
	if {$pos == "" && $DDL2} { 
	    catch {set pos [set CIFdict::block${i}(_item_type_conditions.code)]}
	}
	if {[llength $pos] != 1} {
	    set esd 0
	} else {
	    if {"esd" == [string tolower \
		    [StripQuotes [$txt get $pos.l $pos.r]]]} {set esd 1}
	}
	# units (_units_details overrides _units)
	set pos {}
	catch {set pos [set CIFdict::block${i}(_units)]}
	if {$pos == "" && $DDL2} {
	    catch {set pos [set CIFdict::block${i}(_item_units.code)]}
	} else {
	    catch {set pos [set CIFdict::block${i}(_units_details)]}
	}
	if {[llength $pos] != 1} {
	    set units {}
	} else {
	    set units [StripQuotes [$txt get $pos.l $pos.r]]
	}
	# parse out _enumeration _enumeration_detail & _enumeration_range
	set elist ""
	set enumlist {}
	set enumdetaillist {}
	if {$DDL2} {
	    catch {
		set enumlist [set CIFdict::block${i}(_item_enumeration.value)]
		set enumdetaillist [set CIFdict::block${i}(_item_enumeration.detail)]
	    }
	} else {
	    catch {
		set enumlist [set CIFdict::block${i}(_enumeration)]
		set enumdetaillist [set CIFdict::block${i}(_enumeration_detail)]
	    }
	}
	catch {
	    foreach m1 $enumlist \
		    m2 $enumdetaillist {
		if {$m2 != ""} {
		    set detail [StripQuotes [$txt get $m2.l $m2.r]]]
		    # condense multiple spaces out
		    regsub -all {  +} $detail { } detail
		} else {
		    set detail {}
		}
		lappend elist [list [StripQuotes [$txt get $m1.l $m1.r]] $detail]
	    }
	}
	# mmCIF ranges are too complex to do here
	set range ""
	catch {
	    set mark [set CIFdict::block${i}(_enumeration_range)] 
	    lappend range [StripQuotes [$txt get $mark.l $mark.r]]
	}

	# category names
	set pos ""
	catch {set pos [set CIFdict::block${i}(_category)]}
	if {$pos == "" && $DDL2} {
	    catch {set pos [set CIFdict::block${i}(_item.category_id)]}
	}
	if {[llength $pos] != 1} {
	    set category {}
	} else {
	    set category [StripQuotes [$txt get $pos.l $pos.r]]
	}
	# loop is 1 if loops are allowed
	if {$DDL2} {
	    # at least for now, don't worry about DDL2 dictionaries
	    set loop 1
	} else {
	    set loop 0
	    catch {
		set pos [set CIFdict::block${i}(_list)]
		set val [string tolower [StripQuotes [$txt get $pos.l $pos.r]]]
		if {$val == "yes" || $val == "both"} {set loop 1}
	    }
	}
	foreach mark $list {
	    set dataname [string tolower [StripQuotes [$txt get $mark.l $mark.r]]]
	    lappend definednames $dataname
	    # note that this list must match foreach "type range elist... uses
	    set value 	[list [list $file $defpos $deflen] \
			[list $typeval $range $elist $esd $units $category $loop]]
	    if {$errorstat == 0} {
		puts $fp "\t$dataname \t[list $value]"
	    } else {
		set ::CIF_dataname_index($dataname) $value
	    }
	}
    }
    set parsestatus "$counter (close file)"
    update

    if {$errorstat == 0} {
	puts $fp "\}"
	puts $fp "set definednames \{"
	foreach name [lsort $definednames] {
	    puts $fp "\t[list $name]"
	}
	puts $fp "\}"
    }
    catch {close $fp}
    afterputontop
    destroy $top1
    destroy $stat
    namespace delete CIFdict
    if {$errorstat == 0} {
	return {}
    } else {
	return [list $errorstat $errmsg]
    }
}

# load indices to the dictionaries in CIF(dictfilelist), unless
# the variable does not exist or is empty
proc LoadDictIndices {} {
    global scriptdir CIF CIF_file_paths
    global CIF_dataname_index 
    # clear out any previous dictionary entries
    catch {unset CIF_dataname_index}
    # clear out array of file paths
    catch {unset CIF_file_paths}
    # clear out error listings
    set CIF(overloaded) 0
    set CIF(overloadlist) {}
    set CIF(dictwriteerrorlist) {}
    set CIF(dictwriteerrors) {}
    # clear out an old category browser window
    catch {destroy $CIF(CategoryBrowserWin)}
    
    # is there a defined list of dictionary files?
    set flag 0
    if {[catch {set CIF(dictfilelist)}]} {
	set flag 1
    } elseif {[llength $CIF(dictfilelist)] == 0} {
	set flag 1
    }
    # if no files are present in the dictionary list, look 
    # in the standard places for them
    if {$flag} {
	# get a list of dictionary files
	#    CIFTOOLS location:
	set dictfilelist [glob -nocomplain [file join $scriptdir dict *.dic]]
	#
	foreach file $dictfilelist {
	    lappend CIF(dictfilelist) $file
	    set CIF(dict_$file) 1
	}
    }

    if {[catch {set CIF(dictfilelist)}]} {
	set CIF(dictfilelist) {}
    }
    # load the dictionaries
    foreach file $CIF(dictfilelist) {
	if {!$CIF(dict_$file)} continue
	if {![file exists $file]} continue
	IndexLoadDict $file
    }
    if {[llength $CIF(dictwriteerrorlist)] >0} {
	set msg "Error: unable to writing index files for dictionary:"
	foreach dict $CIF(dictwriteerrorlist) {
	    append msg "\n\t[file tail $dict]"
	}
	append msg "\n\nDo you have write permission?"
	set ans [MyMessageBox -parent . -title "CIF index error" \
		-message $msg \
		-icon error -type {Continue "See List"} -default continue]
	if {$ans != "continue"} {
	    MyMessageBox -parent . -title "Error(s)" \
		    -message $CIF(dictwriteerrors) \
		    -icon warning -type Continue -default continue
	}
    }
    if {$CIF(overloaded) != 0 && $CIF(ShowDictDups)} {
	set ans [MyMessageBox -parent . -title "Definitions overridden" \
		-message "Loading CIF dictionaries.\nNote: $CIF(overloaded) datanames appeared in more than one dictionary -- only the last reference is used." \
		-icon warning -type {Continue "See List"} -default continue]
	if {$ans != "continue"} {
	    MyMessageBox -parent . -title "List of overridden definitions" \
		    -message $CIF(overloadlist) \
		    -icon warning -type Continue -default continue
	}
    }
}

# load an index to a dictionary file, create the index if needed.
# save the index to CIF dictionary named XXXXX.dic as XXXXX.dic_index
# if the file cannot be written, create an error message and just load
# it anyway.
proc IndexLoadDict {file} {
    global CIF 
    global CIF_dataname_index CIF_file_paths
    # save the array contents
    set orignamelist [array names CIF_dataname_index]

    set flag 0
    if {![file exists ${file}_index]} {
	set flag 1
    } elseif {[file mtime $file] > [file mtime ${file}_index]} {
	set flag 1
    }
    if {$flag} {
	set stat [MakeCIFdictIndex $file "Please wait, indexing file $file"]
	if {[lindex $stat 0] != ""} {
	    lappend CIF(dictwriteerrorlist) $file
	    append CIF(dictwriteerrors) "=================================\n"
	    append CIF(dictwriteerrors) "Error indexing file $file:\n"
	    append CIF(dictwriteerrors) "=================================\n"
	    append CIF(dictwriteerrors) [lindex $stat 1]
	    append CIF(dictwriteerrors) "\n\n"
	    return 1
	}
    }

    set CIF_index_version 0
    set redo 0
    if {[catch {
	source ${file}_index
    } errmsg]} {
	set stat [MakeCIFdictIndex $file \
		"Please wait, reindexing $file, Error reading file index."]
#	MyMessageBox -parent . -title "CIF index error" \
#		-message "Error reading file ${file}_index -- this should not happen:\n$errmsg" \
#		-icon error -type {"Oh darn"} -default "oh darn"
	set redo 1
    }
    if {$CIF_index_version < $CIF(indexversion)} {
	set redo 1
	set stat [MakeCIFdictIndex $file \
		"Please wait, reindexing $file, index is out of date."]
    } elseif {[file size $file] != $CIF_file_size} {
	set redo 1
	set stat [MakeCIFdictIndex $file \
		"Please wait, reindexing $file, file size has changed"]
    }
    if {$redo} {
	if {[lindex $stat 0] != ""} {
	    lappend CIF(dictwriteerrorlist) $file
	    append CIF(dictwriteerrors) "=================================\n"
	    append CIF(dictwriteerrors) "Error indexing file $file:\n"
	    append CIF(dictwriteerrors) "=================================\n"
	    append CIF(dictwriteerrors) [lindex $stat 1]
	    append CIF(dictwriteerrors) "\n\n"
	    return 1
	}
	if {[catch {
	    source ${file}_index
	} errmsg]} {
	    MyMessageBox -parent . -title "CIF index error" \
		    -message "Error reading file ${file}_index -- this should not happen:\n$errmsg" \
		    -icon error -type {"Oh darn"} -default "oh darn"
	    return 1
	}
    }
    if {[array names CIF_file_paths $CIF_file_name] != ""} {
	MyMessageBox -parent . -title "Duplicate dictionary name" \
		-message "Note: you are using two dictionaries with the same name ($CIF_file_name). The locations are:\n$CIF_file_paths($CIF_file_name)\n$file\n\nOnly the latter file will be accessed." \
		-icon warning -type {"Oh well"} -default "oh well"
    }
    set CIF_file_paths($CIF_file_name) $file
    # now check for overridden names
    set errorlist {}
    foreach name $definednames {
	if {[lsearch -exact $orignamelist $name] != -1} {
	    incr CIF(overloaded) 
	    append errorlist "\t$name\n"
	}
    }
    if {$errorlist != ""} {
	append CIF(overloadlist) "\ndictionary $file overrides definitions for datanames:\n" $errorlist
    }
    return
}

# make a window for selecting dictionaries
proc MakeDictSelect {parent} {
    global CIF
    global CIF_dataname_index 
    #global icon
    set icon(up) [image create bitmap -data {
	#define up_width 24
	#define up_height 24
	static unsigned char up_bits[] = {
	    0x00, 0x18, 0x00, 0x00, 0x18, 0x00, 
	    0x00, 0x3c, 0x00, 0x00, 0x3c, 0x00,
	    0x00, 0x7e, 0x00, 0x00, 0x7e, 0x00, 
	    0x00, 0xff, 0x00, 0x00, 0xff, 0x00,
	    0x80, 0xff, 0x01, 0x80, 0xff, 0x01, 
	    0xc0, 0xff, 0x03, 0xc0, 0xff, 0x03,
	    0xe0, 0xff, 0x07, 0xe0, 0xff, 0x07, 
	    0xf0, 0xff, 0x0f, 0xf0, 0xff, 0x0f,
	    0xf8, 0xff, 0x1f, 0xf8, 0xff, 0x1f, 
	    0xfc, 0xff, 0x3f, 0xfc, 0xff, 0x3f,
	    0xfe, 0xff, 0x7f, 0xfe, 0xff, 0x7f, 
	    0xff, 0xff, 0xff, 0xff, 0xff, 0xff};
    }]

    set icon(down) [image create bitmap -data {
	#define down_width 24
	#define down_height 24
	static unsigned char down_bits[] = {
	    0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 
	    0xfe, 0xff, 0x7f, 0xfe, 0xff, 0x7f,
	    0xfc, 0xff, 0x3f, 0xfc, 0xff, 0x3f, 
	    0xf8, 0xff, 0x1f, 0xf8, 0xff, 0x1f,
	    0xf0, 0xff, 0x0f, 0xf0, 0xff, 0x0f,
	    0xe0, 0xff, 0x07, 0xe0, 0xff, 0x07,
	    0xc0, 0xff, 0x03, 0xc0, 0xff, 0x03,
	    0x80, 0xff, 0x01, 0x80, 0xff, 0x01,
	    0x00, 0xff, 0x00, 0x00, 0xff, 0x00,
	    0x00, 0x7e, 0x00, 0x00, 0x7e, 0x00,
	    0x00, 0x3c, 0x00, 0x00, 0x3c, 0x00,
	    0x00, 0x18, 0x00, 0x00, 0x18, 0x00};
    }]

    set win $parent.dictselect
    catch {destroy $win}
    toplevel $win
    wm title $win "Select CIF dictionaries"
    grid [canvas $win.canvas \
	    -scrollregion {0 0 5000 500} -width 0 -height 200 \
	    -xscrollcommand "$win.xscroll set" \
	    -yscrollcommand "$win.scroll set"] \
	    -column 0 -row 2 -sticky nsew
    grid columnconfigure $win 0 -weight 1
    grid rowconfigure $win 2 -weight 1
    scrollbar $win.scroll \
	    -command "$win.canvas yview"
    scrollbar $win.xscroll -orient horizontal \
	    -command "$win.canvas xview"
    frame [set CIF(dictlistbox) $win.canvas.fr]
    $win.canvas create window 0 0 -anchor nw -window $CIF(dictlistbox)
    grid [label $win.top -text "Select dictionaries to be loaded" -bg beige] \
	    -column 0 -columnspan 99 -row 0 -sticky ew
    grid [label $win.top1 \
	    -text "(Dictionaries are loaded in the order listed)" -bg beige] \
	    -column 0 -columnspan 99 -row 1 -sticky ew
    catch {$win.top1 config -font "[$win.top1 cget -font] italic"}
    grid [frame  $win.bot] \
	    -column 0 -columnspan 99 -row 99 -sticky ew
    set col 0
    grid [button $win.bot.add -text "Add Dictionary" \
	    -command "OpenLoadDict $win"] \
	    -column $col -row 0
    grid [button $win.bot.save -text "Save current settings" \
	    -command "SaveOptions"] \
	    -column [incr col] -row 0
    grid [button $win.bot.up -image $icon(up) -width 35\
	    -command ShiftDictUp] \
	    -column [incr col] -row 0
    grid [button $win.bot.down -image $icon(down) -width 35 \
	    -command ShiftDictDown] \
	    -column [incr col] -row 0

    grid [button $win.bot.cancel -text Close -command "destroy $win; LoadDictIndices"] \
	    -column [incr col] -row 0
    wm protocol $win WM_DELETE_WINDOW "$win.bot.cancel invoke"

    FillDictSelect

    update
    #putontop $win
    #tkwait window $win
    #afterputontop
}


# respond to a dictionary selection
proc SelectDict {row} {
    global CIF
    set widget $CIF(dictlistbox)
    if {$CIF(selected_dict) != ""} {
	${widget}.c$CIF(selected_dict) config -bg \
		[option get [winfo toplevel $widget] background Frame]
    }
    set CIF(selected_dict) $row
    ${widget}.c$row config -bg black
}

# shift the selected dictionary up in the list
proc ShiftDictUp {} {
    global CIF
    if {$CIF(selected_dict) == ""} {
	bell
	return
    }
    if {$CIF(selected_dict) == 0} {
	return
    }
    set prev [set pos $CIF(selected_dict)]
    incr prev -1
    set CIF(dictfilelist) [lreplace $CIF(dictfilelist) $prev $pos \
	    [lindex $CIF(dictfilelist) $pos] \
	    [lindex $CIF(dictfilelist) $prev]]
    FillDictSelect
    SelectDict $prev
}

# shift the selected dictionary down in the list
proc ShiftDictDown {} {
    global CIF
    if {$CIF(selected_dict) == ""} {
	bell
	return
    }
    if {$CIF(selected_dict) == [llength  $CIF(dictfilelist)]-1} {
	return
    }
    set next [set pos $CIF(selected_dict)]
    incr next 1
    set CIF(dictfilelist) [lreplace $CIF(dictfilelist) $pos $next \
	    [lindex $CIF(dictfilelist) $next] \
	    [lindex $CIF(dictfilelist) $pos]]
    FillDictSelect
    SelectDict $next
}

# place the dictionary list into the window
proc FillDictSelect {} {
    global CIF

    set win [winfo toplevel $CIF(dictlistbox)]
    eval destroy [winfo children $CIF(dictlistbox)]
    set CIF(dictlistboxRow) -1
    foreach file $CIF(dictfilelist) {
	set lbl $file
	if {![file exists $file]} {
	    set lbl "$file (not found)"
	    set CIF(dict_$file) 0
	}
	set row [incr CIF(dictlistboxRow)]
	grid [frame $CIF(dictlistbox).c$row -bd 3] -column 0 -row $row -sticky w
	grid [checkbutton $CIF(dictlistbox).c$row.c -text $lbl \
		-command "SelectDict $row" \
		-variable CIF(dict_$file)] \
		-column 0 -row 0 -sticky w
	if {![file exists $file]} {
	    $CIF(dictlistbox).c$row.c config -state disabled
	}
    }
    set CIF(selected_dict) {}
    # resize the list
    update
    set sizes [grid bbox $win.canvas.fr]
    $win.canvas config -scrollregion $sizes -width [lindex $sizes 2]
    # use the scroll for BIG lists
    if {[lindex $sizes 3] > [winfo height $win.canvas]} {
	grid $win.scroll -sticky ns -column 1 -row 2
    } else {
	grid forget $win.scroll 
    }
    if {[lindex $sizes 2] > [winfo width $win.canvas]} {
	grid $win.xscroll -sticky ew -column 0 -row 3
    } else {
	grid forget $win.xscroll 
    }
}

# open a new dictionary and add it to the list
proc OpenLoadDict {win} {
    global CIF
    set file [tk_getOpenFile -title "Select CIF" -parent $win \
	    -defaultextension .dic -filetypes {{"CIF dictionary" ".dic"}}]
    if {$file == ""} {return}
    if {![file exists $file]} {
	MyMessageBox -parent . -title "CIF error" \
		-message "Error file $file does not exist -- this should not happen" \
		-icon error -type {"Oh darn"} -default "oh darn"
    }
    if {[IndexLoadDict $file] == 1} return
    set CIF(dict_$file) 1
    lappend CIF(dictfilelist) $file

    FillDictSelect

    $win.canvas xview moveto 0
}

# a dummy routine -- each program should have its own SaveOptions routine
proc SaveOptions {} {
    MyMessageBox -parent . -title "Not saved" \
	    -message "SaveOptions is not implemented in this program" \
	    -icon "info" -type OK -default OK
}

#----------------------------------------------------------------------
# initialize misc variables
set CIF(QuitParse) 0
set CIF(changes) 0
set CIF(widgetlist) {}
set CIF(lastShownItem) {}
set CIF(lastLoopIndex) {}
set CIF(editmode) 0
set CIF(undolist) {}
set CIF(redolist) {}
set CIF(treeSelectedList) {}
set CIF(catsearchnum) -1
set CIF(catsearchlist) {}
# version of the dictionary that is needed by the current program
set CIF(indexversion) 1.1
# make sure this variable is defined
if {[catch {set CIF(ShowDictDups)}]} {set CIF(ShowDictDups) 0}

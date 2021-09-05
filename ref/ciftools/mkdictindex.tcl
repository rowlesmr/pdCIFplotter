#!/bin/sh
# the next line restarts this script using wish found in the path\
exec wish "$0" "$@"
# If this does not work, change the #!/usr/bin/wish line below
# to reflect the actual wish location and delete all preceeding lines
#
# (delete here and above)
#------------------------------------------------------------------------------
#------------------------------------------------------------------------------
# load the CIF dictionaries; this forces the creation of dictionary index files
#------------------------------------------------------------------------------
#------------------------------------------------------------------------------

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

source [file join $scriptdir browsecif.tcl]

# load the initial CIF dictionaries
LoadDictIndices

exit

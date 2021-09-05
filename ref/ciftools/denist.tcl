# remove the http://www.nist.gov/cgi-bin/exit_nist.cgi?url= redirectory
# from the distributed version of the documentation
foreach file $argv {
    set fp [open $file r]
    set text [read $fp]
    close $fp
    while {[set pos1 [ \
	    string first {http://www.nist.gov/cgi-bin/exit_nist.cgi?url=} \
	    [string tolower $text] ]] > 0} {
	set pos2 [expr {$pos1 + 45}]
	set text [string replace $text $pos1 $pos2]
    }
    set fp [open $file w]
    puts -nonewline $fp $text
    close $fp
}

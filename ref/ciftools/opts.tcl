# $Id: opts.tcl,v 1.2 2003/12/29 22:49:41 toby Exp toby $
proc SetTkDefaultOptions {"basefont 14"} { 

    set Opt(prio)    10
    set Opt(font)         "Helvetica -$basefont"
    set Opt(bold_font)    "Helvetica -$basefont bold"
    set Opt(menu_font)    "Helvetica -$basefont bold"
    set Opt(italic_font)  "Helvetica -$basefont bold italic"
    #set Opt(fixed_font)   -*-courier-medium-r-*-*-14-*-*-*-*-*-*-*
    incr basefont -2
    set Opt(graph_font)    "Helvetica -$basefont"
    set Opt(small_bold_font)    "Helvetica -$basefont bold"
    set Opt(small_font)    "Helvetica -$basefont"
    set Opt(coord_font)    "Courier -$basefont bold"

    option add *Font		$Opt(font) $Opt(prio)
    option add *font		$Opt(font) $Opt(prio)
    option add *Graph*Font	$Opt(graph_font) $Opt(prio)
    option add *Graph.font	$Opt(graph_font) $Opt(prio)
    option add *Graph*plotBackground  white  $Opt(prio)
    option add *Canvas.font	$Opt(bold_font) $Opt(prio)
    option add *Button.font	$Opt(font) $Opt(prio)
    option add *Menu.font	$Opt(menu_font) $Opt(prio)
    option add *Menubutton.font	$Opt(menu_font) $Opt(prio)
    option add *Label.font      $Opt(bold_font) $Opt(prio)
    option add *Scale.font	$Opt(italic_font) $Opt(prio)
    option add *TitleFrame.font $Opt(italic_font) $Opt(prio)
    option add *SmallFont.Label.font	$Opt(small_bold_font) $Opt(prio)
    option add *SmallFont.Checkbutton.font	$Opt(small_font) $Opt(prio)
    option add *SmallFont.Button.font	$Opt(small_font) $Opt(prio)
    option add *Coord.Listbox.font	$Opt(coord_font) $Opt(prio)
    option add *HistList.Listbox.font	$Opt(coord_font) $Opt(prio)
    option add *MonoSpc.Label.font	$Opt(coord_font) $Opt(prio)

    set Opt(bg)           lightgray
    set Opt(fg)           black

    set Opt(dark1_bg)     gray86
    set Opt(dark1_fg)     black
    #set Opt(dark2_bg)     gray77
    #set Opt(dark2_fg)     black
    set Opt(inactive_bg)  gray77
    set Opt(inactive_fg)  black

    set Opt(light1_bg)    gray92
    #set Opt(light1_fg)    white
    #set Opt(light2_bg)    gray95
    #set Opt(light2_fg)    white

    set Opt(active_bg)    $Opt(dark1_bg)
    set Opt(active_fg)    $Opt(fg)
    set Opt(disabled_fg)  gray55

    set Opt(input1_bg)    gray95
    set Opt(input2_bg)    gray95
    set Opt(output1_bg)   $Opt(dark1_bg)
    set Opt(output2_bg)   $Opt(bg)

    set Opt(select_fg)    black
    set Opt(select_bg)    lightblue

    set Opt(selector)	yellow

    option add *background 		$Opt(bg) 10
    option add *Background		$Opt(bg) $Opt(prio)
    option add *background		$Opt(bg) $Opt(prio)
    option add *Foreground		$Opt(fg) $Opt(prio)
    option add *foreground		$Opt(fg) $Opt(prio)
    option add *activeBackground	$Opt(active_bg) $Opt(prio)
    option add *activeForeground	$Opt(active_fg) $Opt(prio)
    option add *HighlightBackground	$Opt(bg) $Opt(prio)
    option add *selectBackground	$Opt(select_bg) $Opt(prio)
    option add *selectForeground	$Opt(select_fg) $Opt(prio)
    option add *selectBorderWidth	0 $Opt(prio)
    option add *Menu.selectColor	$Opt(selector) $Opt(prio)
    option add *Menubutton.padY		1p $Opt(prio)
    option add *Button.borderWidth	2 $Opt(prio)
    option add *Button.anchor		c $Opt(prio)
    option add *Checkbutton.selectColor	$Opt(selector) $Opt(prio)
    option add *Radiobutton.selectColor	$Opt(selector) $Opt(prio)
    option add *Entry.relief		sunken $Opt(prio)
    option add *Entry.highlightBacground	$Opt(bg) $Opt(prio)
    option add *Entry.background	$Opt(input1_bg) $Opt(prio)
    option add *Entry.foreground	black $Opt(prio)
    option add *Entry.insertBackground	black $Opt(prio)
    #option add *Label.anchor		w $Opt(prio)
    option add *Label.borderWidth	0 $Opt(prio)
    option add *Listbox.background	$Opt(light1_bg) $Opt(prio)
    option add *Listbox.relief		sunken $Opt(prio)
    option add *Scale.foreground	$Opt(fg) $Opt(prio)
    option add *Scale.activeForeground	$Opt(bg) $Opt(prio)
    option add *Scale.background	$Opt(bg) $Opt(prio)
    option add *Scale.sliderForeground	$Opt(bg) $Opt(prio)
    option add *Scale.sliderBackground	$Opt(light1_bg) $Opt(prio)
    option add *Scrollbar.background	$Opt(bg) $Opt(prio)
    option add *Scrollbar.troughColor	$Opt(light1_bg) $Opt(prio)
    option add *Scrollbar.relief	sunken $Opt(prio)
    option add *Scrollbar.borderWidth	1 $Opt(prio)
    option add *Scrollbar.width		15 $Opt(prio)
    option add *Text.background		$Opt(input1_bg) $Opt(prio)
    option add *Text.relief		sunken $Opt(prio)
    . config -background                $Opt(bg)
}
SetTkDefaultOptions

# recursive routine to set all 
proc ResizeFont {path} {
    foreach child [winfo children $path] {
        set childtype [winfo class $child]
	# class "FixedFont" should not be resized
	if {$childtype == "FixedFont"} continue
	set font [option get $child font $childtype]
	# handle BLT objects specially
	if {$childtype == "Graph"} {
	    foreach w {legend xaxis yaxis xaxis yaxis \
		    x2axis y2axis x2axis y2axis} \
		    o {-font -tickfont -tickfont -titlefont -titlefont \
		    -tickfont -tickfont -titlefont -titlefont} {
		catch {
		    $child $w configure $o $font
		}
	    }
	    # forces a redraw of the plot by changing the title to itself
	    catch {
		$child configure -title [$child cget -title]
	    }
	}
	# handle Tree objects specially
	if {$childtype == "Tree"} {
	    # get the size of the font and adjust the line spacing accordingly
	    catch {
		$child configure -deltay [font metrics $font -linespace]
	    }
	}
	if {$font != ""} {
	    catch {
		set curfont [$child cget -font]
		if {[string tolower [lindex $curfont 0]] == "symbol"} {
		    $child configure -font "Symbol [lrange $font 1 end]"
		} else {
		    $child configure -font $font
		}
	    }
	}
	ResizeFont $child
    }
}

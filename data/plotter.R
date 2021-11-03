library(tidyverse)
library(grid)
library(scales)
library(janitor)
library(tidylog)
library(ggtext)
library(directlabels)
library("glue")
library("viridis") 
library(patchwork)
#library(akima)
library(plotly)


setwd("C:\\Users\\184277j\\Documents\\GitHub\\pdCIFplotter\\data")

#read in data
diff_df <- read_delim("diff_data.txt", delim="\t") %>% janitor::clean_names()
hkl_df  <- read_delim("hkl_data.txt",  delim="\t") %>% janitor::clean_names()
phase_overlay_df <- read_delim("phase_overlay.txt",  delim="\t") %>% janitor::clean_names()
pattern_overlay_df <- read_delim("pattern_overlay.txt",  delim="\t") %>% janitor::clean_names()


#calculate d, q, diff
diff_df <- diff_df %>% mutate(pd_proc_d_spacing = diffrn_radiation_wavelength / (2 * sin(pd_meas_2theta_scan/2 * pi / 180)))
diff_df <- diff_df %>% mutate(pd_proc_recip_len_Q = 2 * pi / pd_proc_d_spacing)
diff_df <- diff_df %>% mutate(diff = pd_meas_intensity_total - pd_calc_intensity_total)
diff_offset <- max(diff_df$diff)

hkl_df <- hkl_df %>% mutate(refln_recip_len_Q = 2 * pi / refln_d_spacing)
hkl_df <- hkl_df %>% mutate(refln_2theta = 2* asin(diffrn_radiation_wavelength / (2 * refln_d_spacing))* 180 / pi)




##########################################
### normal plot
##########################################
pattern_to_plot <- "pattern_0" #this would get chosen by the user
diff_plt <- diff_df %>% filter(pd_block_id == pattern_to_plot)
hkl_plt  <- hkl_df  %>% filter(pd_block_id == pattern_to_plot)
lambda <- diff_plt$diffrn_radiation_wavelength[1]

#get offset posns of hkl ticks
hkl_tick_offset <- min(diff_df$diff)-diff_offset
hkl_tick_vspacing <- 400 # this needs to be automagically set
hkl_tick_alignment <- seq(from=hkl_tick_offset, by=-hkl_tick_vspacing, length.out=length(unique(hkl_plt$pd_refln_phase_id)))


normal_plot <- 
diff_plt %>% 
  ggplot(aes(x = pd_meas_2theta_scan))+
  geom_point(aes(y=pd_meas_intensity_total), colour="blue", shape="+", size = 1)+
  geom_line(aes(y=pd_calc_intensity_total), colour="red")+
  geom_line(aes(y=pd_proc_intensity_bkg_calc), colour="gray")+
  geom_hline(yintercept=-diff_offset)+
  geom_line(aes(y=diff-diff_offset), colour="gray")+
  geom_point(data=hkl_plt, aes(x=refln_2theta, y = stage(0, after_stat = y + hkl_tick_alignment[group]), colour = factor(pd_refln_phase_id)), shape=17)+
  labs(x = str_glue('\u00B0 2\u03B8 (\u03BB = {lambda} \u212b)'),
       y = "Intensity",
       colour = "Phases",
       title = "pattern_0")+
  #coord_cartesian(ylim=c(NA, 500))+
  theme_bw()

ggplotly(normal_plot)





##########################################
### stack plot
##########################################
stack_plt <- diff_df  
stack_plt <- stack_plt %>% mutate(pd_block_id = fct_inorder(pd_block_id)) # need this to keep the plots in the order in which they appeared
stack_plt_offset <- 0
stack_plt_vspacing <- 800 # this should probably be chosen by the user
stack_plt_alignment <- seq(from=stack_plt_offset, by=stack_plt_vspacing, length.out=length(unique(stack_plt$pd_block_id)))

stack_plot <- 
stack_plt %>% 
  ggplot(aes(x = pd_meas_2theta_scan, 
             y = stage(pd_meas_intensity_total, after_stat = y + stack_plt_alignment[group]),
             group = pd_block_id))+
  geom_line()+
  geom_text(data = filter(stack_plt, pd_meas_2theta_scan == last(pd_meas_2theta_scan)), aes(label = pd_block_id)) + 
  #geom_dl(aes(label = pd_block_id), method = "last.points", cex = 0.5) +
  #xlim(NA,70) +
  labs(x = str_glue('\u00B0 2\u03B8 (\u03BB = {lambda} \u212b)'),
       y = "Intensity (each pattern is vertically offset)")+
  theme_bw()

stack_plot

ggplotly(stack_plot)

##########################################
### surface plot
##########################################
#surf_plt <- diff_df %>% select(pd_block_id, pd_meas_2theta_scan, pd_meas_intensity_total,pd_proc_intensity_bkg_calc)
surf_plt <- diff_df %>% left_join(pattern_overlay_df)
surf_hkl <- hkl_df %>% left_join(pattern_overlay_df)
surf_wt <- phase_overlay_df



#this bit replaces the block_id with the pattern number
surf_plt <- surf_plt %>% mutate(pd_block_id = factor(pd_block_id))
surf_plt <- surf_plt %>% mutate(pd_block_id = fct_inorder(pd_block_id))
surf_plt <- surf_plt %>% mutate(pd_block_id = as.numeric(pd_block_id))

surf_hkl <- surf_hkl %>% mutate(pd_block_id = factor(pd_block_id))
surf_hkl <- surf_hkl %>% mutate(pd_block_id = fct_inorder(pd_block_id))
surf_hkl <- surf_hkl %>% mutate(pd_block_id = as.numeric(pd_block_id))

surf_wt <- surf_wt %>% mutate(pd_block_id = factor(pd_block_id))
surf_wt <- surf_wt %>% mutate(pd_block_id = fct_inorder(pd_block_id))
surf_wt <- surf_wt %>% mutate(pd_block_id = as.numeric(pd_block_id))


#pattern num
surface_plot <- 
surf_plt %>%
  ggplot(aes(x = pd_meas_2theta_scan, 
             y = pd_block_id, 
             z = pd_meas_intensity_total, 
             fill = sqrt(pd_meas_intensity_total))) +
  geom_raster(interpolate=TRUE) + 
  #geom_point(data=surf_hkl, aes(x = refln_2theta, y = pd_block_id, colour = factor(pd_refln_phase_id)), inherit.aes = FALSE, shape = "|", size = 3)+
  geom_path(data=surf_wt, aes(x = pd_phase_mass_percent*0.6 + 5, 
                              y = pd_block_id, 
                              colour = factor(pd_phase_id)), 
            inherit.aes = FALSE)+
  scale_x_continuous(expand=expansion(mult = 0, add = 0),
                     sec.axis = sec_axis(~.*10/6 - (25/3), name="Phase weight percent")) +
  scale_y_continuous(expand=expansion(mult = 0, add = 0)) +
  scale_fill_viridis(option="D") +  
  labs(x = str_glue('\u00B0 2\u03B8 (\u03BB = {lambda} \u212b)'),
       y = "Pattern number",
       fill = "Sqrt(intensity)",
       colour = "Phase wt%") +
  #coord_cartesian(xlim=c(20,22.5))+
  theme_bw()

surface_plot

ggplotly(surface_plot)  



#temperature
surf_plt %>%
  ggplot(aes(x = pd_meas_2theta_scan, 
             y = diffrn_ambient_temperature+273, 
             z = pd_meas_intensity_total, 
             fill = sqrt(pd_meas_intensity_total))) +
  geom_tile(interpolate=TRUE) + 
  geom_point(data=surf_hkl, aes(x = refln_2theta, y = diffrn_ambient_temperature+273, colour = factor(pd_refln_phase_id)), inherit.aes = FALSE, shape = "|", size = 3)+
  scale_x_continuous(expand=expansion(mult = 0, add = 0)) +
  scale_y_continuous(expand=expansion(mult = 0, add = 0)) +
  scale_fill_viridis(option="D") +  
  labs(x = str_glue('\u00B0 2\u03B8 (\u03BB = {lambda} \u212b)'),
       y = "Temperature (K)",
       fill = "Sqrt(intensity)",
       colour = "Phase") +
  coord_cartesian(xlim=c(15,15.25))+
  theme_bw()























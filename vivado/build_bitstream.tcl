#
# build_bitstream.tcl - Complete One-Click Bitstream Synthesis & Implementation
# Builds t9_base.bit and t9_base.hwh for Antminer T9+ Devboard
#

set script_dir [file normalize [file dirname [info script]]]
set repo_root  [file normalize [file join $script_dir ".."]]
set proj_file  [file normalize [file join $repo_root "build_vivado" "t9_pynq_base.xpr"]]

if {![file exists $proj_file]} {
    puts "==> Project not found. Running create_project.tcl first..."
    source [file join $script_dir "create_project.tcl"]
} else {
    puts "==> Opening existing project '$proj_file'..."
    open_project $proj_file
}

# Generate Block Design Targets
puts "==> Generating Block Design Output Products..."
generate_target all [get_files "design_1.bd"]
export_ip_user_files -of_objects [get_files "design_1.bd"] -no_script -sync -force -quiet

# Reset old runs if completed
reset_run synth_1 -quiet
reset_run impl_1 -quiet

# Launch Synthesis
puts "==> Launching Synthesis (synth_1)..."
launch_runs synth_1 -jobs 4
wait_on_run synth_1

if {[get_property PROGRESS [get_runs synth_1]] != "100%"} {
    puts "ERROR: Synthesis failed. Check synthesis log."
    exit 1
}

# Launch Implementation & Generate Bitstream
puts "==> Launching Implementation & Bitstream Generation (impl_1)..."
launch_runs impl_1 -to_step write_bitstream -jobs 4
wait_on_run impl_1

if {[get_property PROGRESS [get_runs impl_1]] != "100%"} {
    puts "ERROR: Implementation failed. Check implementation log."
    exit 1
}

# Locate output bitstream and HWH files
set impl_dir [get_property DIRECTORY [get_runs impl_1]]
set bit_file [file normalize [file join $impl_dir "design_1_wrapper.bit"]]
set hwh_file [file normalize [file join $repo_root "build_vivado" "t9_pynq_base.gen" "sources_1" "bd" "design_1" "hw_handoff" "design_1.hwh"]]

set dest_bit [file normalize [file join $repo_root "t9_base.bit"]]
set dest_hwh [file normalize [file join $repo_root "t9_base.hwh"]]

if {[file exists $bit_file]} {
    file copy -force $bit_file $dest_bit
    puts ""
    puts "=========================================================================="
    puts " SUCCESS: Bitstream generated successfully!"
    puts " Output Bitstream: $dest_bit ([file size $dest_bit] bytes)"
    if {[file exists $hwh_file]} {
        file copy -force $hwh_file $dest_hwh
        puts " Output HWH:       $dest_hwh"
    }
    puts "=========================================================================="
    puts " To load onto your board:"
    puts "   scp t9_base.bit xilinx@192.168.2.99:"
    puts "   ssh xilinx@192.168.2.99 'sudo load_bit t9_base.bit'"
    puts "=========================================================================="
} else {
    puts "ERROR: Bitstream file was not created."
    exit 1
}

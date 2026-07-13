# AnyKernel3 Tool Template
# Home: https://github.com/osm0sis/AnyKernel3

## AnyKernel setup
# global exports
properties() { '
kernel.string=SukiSU-Ultra Kernel for Redmi K20 (davinci)
do.devicecheck=1
do.modules=0
do.systemless=1
do.cleanup=1
do.cleanuponabort=1
device.name1=davinci
device.name2=Mi 9T
device.name3=Redmi K20
supported.versions=
supported.patchlevels=
'; } # end properties

# shell variables
block=/dev/block/by-name/boot;
is_slot_device=0;
ramdisk_compression=auto;
patch_vbmeta_flag=auto;

## AnyKernel methods (do not change)
# import patch template functions
. tools/ak3-core.sh;

## AnyKernel install
dump_boot;

# write back picture/ramdisk changes
write_boot;
## end install

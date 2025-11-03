#
# SPDX-License-Identifier: BSD-2-Clause
#

carray-platform_override_modules-$(CONFIG_PLATFORM_ANDES_AE350) += andes_ae350
platform-objs-$(CONFIG_PLATFORM_ANDES_AE350) += andes/ae350.o andes/sleep.o

# AX65 platform override (matches DT compatible "agic,ax65")
carray-platform_override_modules-$(CONFIG_PLATFORM_ANDES_AX65) += andes_ax65
platform-objs-$(CONFIG_PLATFORM_ANDES_AX65) += andes/ax65.o

platform-objs-$(CONFIG_ANDES_PMA) += andes/andes_pma.o
platform-objs-$(CONFIG_ANDES_SBI) += andes/andes_sbi.o
platform-objs-$(CONFIG_ANDES_PMU) += andes/andes_pmu.o

# AX65 specific firmware configuration
ifeq ($(CONFIG_PLATFORM_ANDES_AX65),y)
  # Override FW_JUMP addresses for AX65 platform
  FW_JUMP_ADDR=0x42000000
  # FDT: Use passthrough mode (clear default OFFSET from generic/objects.mk)
  # DTB address will be passed through from previous bootloader via a1 register
  # Undefine these to enable passthrough mode
  override FW_JUMP_FDT_ADDR :=
  override FW_JUMP_FDT_OFFSET :=
  override FW_PAYLOAD_FDT_ADDR :=
  override FW_PAYLOAD_FDT_OFFSET :=
endif

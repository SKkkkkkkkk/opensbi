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

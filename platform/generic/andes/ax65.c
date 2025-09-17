/*
 * SPDX-License-Identifier: BSD-2-Clause
 *
 * Minimal AX65 platform override to allow S-mode access to CCTL CSRs.
 */

#include <platform_override.h>
#include <andes/andes.h>
#include <sbi_utils/fdt/fdt_helper.h>
#include <sbi/sbi_init.h>
#include <sbi/riscv_asm.h>

static int ax65_final_init(bool cold_boot)
{
	if (cold_boot) {
		/* Enable S/U access to ucctl* by setting MCACHE_CTL.CCTL_SUEN */
		unsigned long mcache_ctl = csr_read(CSR_MCACHE_CTL);
		mcache_ctl |= MCACHE_CTL_CCTL_SUEN_MASK;
		csr_write(CSR_MCACHE_CTL, mcache_ctl);
	}

	return generic_final_init(cold_boot);
}

static int ax65_platform_init(const void *fdt, int nodeoff,
				const struct fdt_match *match)
{
	/* Hook our final_init into the generic platform ops */
	generic_platform_ops.final_init = ax65_final_init;
	return 0;
}

static const struct fdt_match andes_ax65_match[] = {
	{ .compatible = "agic,ax65" },
	{ },
};

const struct fdt_driver andes_ax65 = {
	.match_table = andes_ax65_match,
	.init = ax65_platform_init,
};





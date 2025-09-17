static const char hello_str[] = "Hello World From Supervisor\n";

void __attribute__((naked)) after_opensbi(void)
{
    asm volatile(
        // 先在S模式打印
        "csrwi	ucctlcommand,6\n"
        "li a7, 0x4442434E\n"
        "li a6, 0\n"
        "li a0, %0\n"
        "la a1, %1\n"
        "li a2, 0\n"
        "ecall\n"
        
        // 切换到U模式
        "csrr t0, sstatus\n"
        "andi t0, t0, ~0x100\n"    // 清除SPP位(设为0=U模式)
        "csrw sstatus, t0\n"
        "la t0, user_code\n"
        "csrw sepc, t0\n"
        "sret\n"                   // 跳转到U模式
        
        "user_code:\n"
        // 现在在U模式，可以直接读写UART
        "li t0, 0x060000f8\n"      // UART基地址
        "lw t1, 0(t0)\n"           // 读取UART寄存器
        // ... 其他U模式代码
        
        "1: j 1b\n"
        :
        : "i" (sizeof(hello_str) - 1), "i" (hello_str)
        : "a0", "a1", "a2", "a6", "a7", "t0", "t1");
}
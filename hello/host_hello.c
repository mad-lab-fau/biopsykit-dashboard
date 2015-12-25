#include <stdlib.h>
#include <stdio.h>
#include <stdint.h>
#include "avrvm.h"

#include <windows.h>    // for Sleep
#include <conio.h>      // for _kbhit and _getch

static FILE *src;

static avrvm_ctx_t vm;
static uint8_t sram[1024 + 160];
static uint8_t io[61];

static uint16_t flash_reader(uint16_t word_idx)
{
    // wrap at 4k words to simulate behavior of atmega88 with 8k flash
    word_idx &= 0x0FFF;
    if (fseek(src, word_idx * 2, SEEK_SET) != 0)
    {
        printf("failed to seek");
        exit(-1);
    }

    uint16_t opcode;
    if (fread ( &opcode, 2, 1, src) != 1)
    {
        printf("failed to read");
        exit(-1);
    }

    return opcode;
}

static uint8_t sram_reader(uint16_t addr)
{
    return sram[addr];
}

static void sram_writer(uint16_t addr, uint8_t byte)
{
    sram[addr] = byte;
}

static uint8_t io_reader(uint8_t addr)
{
    return io[addr];
}

static void io_writer(uint8_t addr, uint8_t byte)
{
    io[addr] = byte;
}

static void exec_ext_call(int idx)
{
    switch (idx)
    {
    case 0:
        {
            char c;
            avrvm_unpack_args_gcc(&vm, "c", &c);
            printf("%c", c);
        }
        break;

    case 1:
        {
            uint32_t interval;
            avrvm_unpack_args_gcc(&vm, "I", &interval);
            Sleep(interval);
        }
        break;

    case 2:
        {
            uint16_t a;
            uint32_t b;
            uint32_t c;
            uint8_t d;
            uint16_t e;
            uint8_t f;
            uint8_t g;
            avrvm_unpack_args_gcc(&vm, "HIIBHBB", &a, &b, &c, &d, &e, &f, &g);

            printf("a = %d "
                   "b = %d "
                   "c = %d "
                   "d = %d "
                   "e = %d "
                   "f = %d "
                   "g = %d \n", a, b, c, d, e, f, g);
        }
        break;

    case 3:
        {
            uint16_t a;
            uint32_t b;
            uint32_t c;
            uint8_t d;
            uint16_t e;
            uint8_t f;
            uint32_t g;
            uint16_t h;
            uint8_t i;
            uint8_t j;
            avrvm_unpack_args_gcc(&vm, "HIIBHBIHBB", &a, &b, &c, &d, &e, &f, &g, &h, &i, &j);

            printf("a = %d "
                   "b = %d "
                   "c = %d "
                   "d = %d "
                   "e = %d "
                   "f = %d "
                   "g = %d "
                   "h = 0x%x "
                   "i = %d"
                   "j = %d\n", a, b, c, d, e, f, g, h, i, j);
        }
        break;

    case 4:
        {
            static uint8_t cnt = 0;
            avrvm_pack_return_gcc(&vm, 'B', &cnt);
            cnt++;
        }
        break;

    case 5:
        {
            uint16_t p;
            avrvm_unpack_args_gcc(&vm, "P", &p);
            printf("%s", &sram[p]);
        }
        break;

//double (* const hostapi_mirror_d)(double) = (void *)(HOSTAPI_BASE + 13);
//int64_t (* const hostapi_mirror_q)(int64_t) = (void *)(HOSTAPI_BASE + 14);
//uint64_t (* const hostapi_mirror_Q)(uint64_t) = (void *)(HOSTAPI_BASE + 15);
//void * (* const hostapi_mirror_p)(void *) = (void *)(HOSTAPI_BASE + 15);


    case 6:
        {
            char c;
            avrvm_unpack_args_gcc(&vm, "c", &c);
            avrvm_pack_return_gcc(&vm, 'c', &c);
        }
        break;

    case 7:
        {
            int8_t b;
            avrvm_unpack_args_gcc(&vm, "b", &b);
            avrvm_pack_return_gcc(&vm, 'b', &b);
        }
        break;

    case 8:
        {
            uint8_t B;
            avrvm_unpack_args_gcc(&vm, "B", &B);
            avrvm_pack_return_gcc(&vm, 'B', &B);
        }
        break;

    case 9:
        {
            int16_t h;
            avrvm_unpack_args_gcc(&vm, "h", &h);
            avrvm_pack_return_gcc(&vm, 'h', &h);
        }
        break;

    case 10:
        {
            uint16_t H;
            avrvm_unpack_args_gcc(&vm, "H", &H);
            avrvm_pack_return_gcc(&vm, 'H', &H);
        }
        break;

    case 11:
        {
            int32_t i;
            avrvm_unpack_args_gcc(&vm, "i", &i);
            avrvm_pack_return_gcc(&vm, 'i', &i);
        }
        break;

    case 12:
        {
            uint32_t I;
            avrvm_unpack_args_gcc(&vm, "I", &I);
            avrvm_pack_return_gcc(&vm, 'I', &I);
        }
        break;

    case 13:
        {
            float d;
            avrvm_unpack_args_gcc(&vm, "f", &d);
            avrvm_pack_return_gcc(&vm, 'f', &d);
        }
        break;

    case 14:
        {
            int64_t q;
            avrvm_unpack_args_gcc(&vm, "q", &q);
            avrvm_pack_return_gcc(&vm, 'q', &q);
        }
        break;

    case 15:
        {
            uint32_t Q;
            avrvm_unpack_args_gcc(&vm, "Q", &Q);
            avrvm_pack_return_gcc(&vm, 'Q', &Q);
        }
        break;

    case 16:
        {
            uint16_t p;
            avrvm_unpack_args_gcc(&vm, "P", &p);
            avrvm_pack_return_gcc(&vm, 'P', &p);
        }
        break;


    default:
        #warning "special spoil"
        vm.regs[24] ^= 0xFF;
        vm.regs[25] ^= 0xFF;
        break;
    }
}

static void run_hello(const char *fname)
{
    avrvm_iface_t iface =
    {
        .flash_r = flash_reader,
        .sram_r = sram_reader,
        .sram_w = sram_writer,
        .io_r = io_reader,
        .io_w = io_writer,
    };

    avrvm_init(&vm, &iface, sizeof(sram));
    src = fopen(fname, "rb");
    if (!src)
    {
        printf("failed to open");
        return;
    }

    while (1)
    {
        if (_kbhit())
        {
            io[0] = _getch();   // move key code to 'KEYB_IO register'
        }

        int rc = avrvm_exec(&vm);
        if (rc == AVRVM_RC_OK)
            continue;

        if (rc >= 0)
        {
            exec_ext_call(rc);
        }
        else if (rc == AVRVM_RC_UNDEF_INSTR)
        {
            printf("bad instruction");
            exit(-1);
        }
        else if (rc == AVRVM_RC_BREAK)
        {
            printf("end of script");
            exit(0);
        }
        else if (rc == AVRVM_RC_SLEEP)
        {
            printf("sleep request");
        }
    }
}

int main(int argc, const char *argv[])
{
    if (argc < 2) return 0;
    run_hello(argv[1]);

    return 0;
}


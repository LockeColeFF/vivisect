import sys
import unittest
import vivisect
import envi.archs.ppc
import vivisect.symboliks.analysis as vs_anal

MARGIN_OF_ERROR = 200

class PpcInstructionSet(unittest.TestCase):
    def getVivEnv(self, arch='ppc'):
        vw = vivisect.VivWorkspace()
        vw.setMeta("Architecture", arch)
        vw.addMemoryMap(0, 7, 'firmware', '\xff' * 16384)
        vw.addMemoryMap(0xbfbff000, 7, 'firmware', '\xfe' * 0x1000)

        emu = vw.getEmulator()
        emu.setMeta('forrealz', True)
        emu.logread = emu.logwrite = True

        sctx = vs_anal.getSymbolikAnalysisContext(vw)
        return vw, emu, sctx

    def test_envi_ppcvle_disasm(self):
        test_pass = 0

        vw, emu, sctx = self.getVivEnv('vle')
        
        import ppc_vle_instructions
        for test_bytes, result_instr in ppc_vle_instructions.instructions:
            try:
                op = vw.arch.archParseOpcode(test_bytes.decode('hex'), 0)
                op_str = repr(op).strip()
                if op_str == result_instr:
                    test_pass += 1
                if result_instr != op_str:
                    print ('{}: ours: {} != {}'.format(test_bytes, op_str, result_instr))
            except Exception, e:
                print ('ERROR: {}: {}'.format(test_bytes, result_instr))
                sys.excepthook(*sys.exc_info())

        print "test_envi_ppcvle_disasm: %d of %d successes" % (test_pass, len(ppc_vle_instructions.instructions))
        self.assertAlmostEqual(test_pass, len(ppc_vle_instructions.instructions), delta=MARGIN_OF_ERROR)

    def test_envi_ppc_server_disasm(self):
        test_pass = 0

        vw, emu, sctx = self.getVivEnv('ppc-server')

        import ppc_server_instructions
        for test_bytes, result_instr in ppc_server_instructions.instructions:
            try:
                op = vw.arch.archParseOpcode(test_bytes.decode('hex'), 0)
                op_str = repr(op).strip()
                if op_str == result_instr:
                    test_pass += 1
                if result_instr != op_str:
                    print ('{}: ours: {} != {}'.format(test_bytes, op_str, result_instr))
            except Exception, e:
                print ('ERROR: {}: {}'.format(test_bytes, result_instr))
                sys.excepthook(*sys.exc_info())

        print "test_envi_ppc_server_disasm: %d of %d successes" % (test_pass, len(ppc_server_instructions.instructions))
        self.assertAlmostEqual(test_pass, len(ppc_server_instructions.instructions), delta=MARGIN_OF_ERROR)

    def test_MASK_and_ROTL32(self):
        import envi.archs.ppc.emu as eape
        import vivisect.symboliks.archs.ppc as vsap

        for x in range(64):
            for y in range(64):
                #mask = 
                emumask = eape.MASK(x, y)

                symmask = vsap.MASK(vsap.Const(x, 8), vsap.Const(y, 8))
                #print hex(emumask), repr(symmask), symmask


                self.assertEqual(emumask, symmask.solve(), 'MASK({}, {}): {} != {}'.format(x, y, emumask, symmask.solve()))

        for y in range(32):
            emurot32 = eape.ROTL32(0x31337040, y)
            symrot32 = vsap.ROTL32(vsap.Const(0x31337040, 8), vsap.Const(y, 8))
            self.assertEqual(emurot32, symrot32.solve(), 'ROTL32(0x31337040, {}): {} != {}   {}'.format(y, hex(emurot32), hex(symrot32.solve()), symrot32))

        for y in range(64):
            emurot64 = eape.ROTL64(0x31337040, y)
            symrot64 = vsap.ROTL64(vsap.Const(0x31337040, 8), vsap.Const(y, 8))
            self.assertEqual(emurot64, symrot64.solve(), 'ROTL64(0x31337040, {}): {} != {}   {}'.format(y, hex(emurot64), hex(symrot64.solve()), symrot64))

    def test_CR_and_XER(self):
        from envi.archs.ppc.regs import *
        from envi.archs.ppc.const import *
        vw, emu, sctx = self.getVivEnv(arch='ppc-server')

        # now compare the register and bitmap stuff to be the same
        emu.setRegister(REG_CR0, 0)
        emu.setRegister(REG_CR0_LT, 1)
        cr = emu.getRegister(REG_CR)
        self.assertEqual(("CR: ", hex(cr)), ("CR: ", hex(0x80000000L)))
        cr0 = emu.getRegister(REG_CR0)
        self.assertEqual(("CR0: ", hex(cr0)), ("CR0: ", hex(8L)))
        self.assertEqual((cr0) , FLAGS_LT)

        emu.setRegister(REG_CR0, 0)
        emu.setRegister(REG_CR0_GT, 1)
        cr = emu.getRegister(REG_CR)
        self.assertEqual(("CR: ", hex(cr)), ("CR: ", hex(0x40000000L)))
        cr0 = emu.getRegister(REG_CR0)
        self.assertEqual(("CR0: ", hex(cr0)), ("CR0: ", hex(4L)))
        self.assertEqual((cr0) , FLAGS_GT)

        emu.setRegister(REG_CR0, 0)
        emu.setRegister(REG_CR0_EQ, 1)
        cr = emu.getRegister(REG_CR)
        self.assertEqual(("CR: ", hex(cr)), ("CR: ", hex(0x20000000L)))
        cr0 = emu.getRegister(REG_CR0)
        self.assertEqual(("CR0: ", hex(cr0)), ("CR0: ", hex(2L)))
        self.assertEqual((cr0) , FLAGS_EQ)

        emu.setRegister(REG_CR0, 0)
        emu.setRegister(REG_CR0_SO, 1)
        cr = emu.getRegister(REG_CR)
        self.assertEqual(("CR: ", hex(cr)), ("CR: ", hex(0x10000000L)))
        cr0 = emu.getRegister(REG_CR0)
        self.assertEqual(("CR0: ", hex(cr0)), ("CR0: ", hex(1L)))
        self.assertEqual((cr0) , FLAGS_SO)

        emu.setRegister(REG_CR0, 0)
        emu.setRegister(REG_XER, 0)
        emu.setRegister(REG_CA, 1)
        xer = emu.getRegister(REG_XER)
        self.assertEqual(xer , XERFLAG_CA)
        self.assertEqual(xer>>29 , XERFLAG_CA_LOW)

        emu.setRegister(REG_CR0, 0)
        emu.setRegister(REG_XER, 0)
        emu.setRegister(REG_OV, 1)
        xer = emu.getRegister(REG_XER)
        self.assertEqual(xer , XERFLAG_OV)
        self.assertEqual(xer>>29 , XERFLAG_OV_LOW)

        emu.setRegister(REG_CR0, 0)
        emu.setRegister(REG_XER, 0)
        emu.setRegister(REG_SO, 1)
        xer = emu.getRegister(REG_XER)
        self.assertEqual(xer , XERFLAG_SO)
        self.assertEqual(xer>>29 , XERFLAG_SO_LOW)



    def test_emu_CR_and_XER(self):
        addco_tests = (
            {'cmd': 'addco.', 'inr1': 0x1, 'inr2': 0x2, 'inr3': 0x0, 'incr': 0x0, 'inxer': 0x0,     'expr3': 0x3,   'expcr': 0x40000000,    'expxer': 0x0,},
            {'cmd': 'addco.', 'inr1': 0x3fffffffffffffff, 'inr2': 0x3fffffffffffffff, 'inr3': 0x0, 'incr': 0x0, 'inxer': 0x0,       'expr3': 0x7ffffffffffffffe,    'expcr': 0x40000000,    'expxer': 0x0,},
            {'cmd': 'addco.', 'inr1': 0x4000000000000000, 'inr2': 0x4000000000000000, 'inr3': 0x0, 'incr': 0x0, 'inxer': 0xc0000000,        'expr3': 0x8000000000000000,    'expcr': 0x90000000,    'expxer': 0xc0000000,},
            {'cmd': 'addco.', 'inr1': 0x4000000000000000, 'inr2': 0x4000000000000000, 'inr3': 0x0, 'incr': 0x0, 'inxer': 0xc0000000,        'expr3': 0x8000000000000000,    'expcr': 0x90000000,    'expxer': 0xc0000000,},
            {'cmd': 'addco.', 'inr1': 0x7fffffffffffffff, 'inr2': 0x7fffffffffffffff, 'inr3': 0x0, 'incr': 0x0, 'inxer': 0xc0000000,        'expr3': 0xfffffffffffffffe,    'expcr': 0x90000000,    'expxer': 0xc0000000,},
            {'cmd': 'addco.', 'inr1': 0x8000000000000000, 'inr2': 0x8000000000000000, 'inr3': 0x0, 'incr': 0x0, 'inxer': 0xc0000000,        'expr3': 0x0,   'expcr': 0x30000000,    'expxer': 0xe0000000,},
            {'cmd': 'addco.', 'inr1': 0xffffffffffffffff, 'inr2': 0xffffffffffffffff, 'inr3': 0x0, 'incr': 0x0, 'inxer': 0xa0000000,        'expr3': 0xfffffffffffffffe,    'expcr': 0x90000000,    'expxer': 0xa0000000,},
            {'cmd': 'addco.', 'inr1': 0x1, 'inr2': 0x2, 'inr3': 0x0, 'incr': 0x0, 'inxer': 0xa0000000,      'expr3': 0x3,   'expcr': 0x50000000,    'expxer': 0x80000000,},
            {'cmd': 'addco.', 'inr1': 0x8000000000000000, 'inr2': 0x7fffffffffffffff, 'inr3': 0x0, 'incr': 0x0, 'inxer': 0x0,       'expr3': 0xffffffffffffffff,    'expcr': 0x80000000,    'expxer': 0x0,},
            {'cmd': 'addco.', 'inr1': 0x8000000000000000, 'inr2': 0x7fffffffffffffff, 'inr3': 0x0, 'incr': 0x0, 'inxer': 0x0,       'expr3': 0xffffffffffffffff,    'expcr': 0x80000000,    'expxer': 0x0,},
            {'cmd': 'addco.', 'inr1': 0x8000000000000000, 'inr2': 0x8000000000000000, 'inr3': 0x0, 'incr': 0x0, 'inxer': 0x0,       'expr3': 0x0,   'expcr': 0x30000000,    'expxer': 0xe0000000,},
            {'cmd': 'addco.', 'inr1': 0x7fffffffffffffff, 'inr2': 0x8000000000000000, 'inr3': 0x0, 'incr': 0x0, 'inxer': 0x0,       'expr3': 0xffffffffffffffff,    'expcr': 0x80000000,    'expxer': 0x0,},
            {'cmd': 'addco.', 'inr1': 0xcfffffffffffffff, 'inr2': 0x8000000000000000, 'inr3': 0x0, 'incr': 0x0, 'inxer': 0x0,       'expr3': 0x4fffffffffffffff,    'expcr': 0x50000000,    'expxer': 0xe0000000,},
        )

        OPCODE_ADDCO = '7C620C15'.decode('hex')

        vw, emu, sctx = self.getVivEnv(arch='ppc-server')
        ppcarch = vw.imem_archs[0]
        op = ppcarch.archParseOpcode(OPCODE_ADDCO)
        for test in addco_tests:
            self._do_CR_XER(op, emu, test['inr1'],  test['inr2'], test['inr3'], test['incr'], test['inxer'], test['expr3'], test['expcr'], test['expxer'])

        #self._do_CR_XER(op, emu, 1, 2, 0, 0, 0, 3, 0x40000000, 0)
        #self._do_CR_XER(op, emu, 0x3FFFFFFFFFFFFFFF, 0x3FFFFFFFFFFFFFFF, 0, 0, 0, 0x7ffffffffffffffeL, 0x40000000L, 0)
        #self._do_CR_XER(op, emu, 0x4000000000000000, 0x4000000000000000, 0, 0, 0xc0000000, 0x8000000000000000, 0x90000000L, 0xc0000000L)
        #self._do_CR_XER(op, emu, 0x4000000000000000, 0x4000000000000000, 0, 0, 0xc0000000, 0x8000000000000000, 0x90000000, 0xc0000000)
        #self._do_CR_XER(op, emu, 0x7FFFFFFFFFFFFFFF, 0x7FFFFFFFFFFFFFFF, 0, 0, 0xc0000000, 0xfffffffffffffffe, 0x90000000, 0xc0000000)
        #self._do_CR_XER(op, emu, 0x8000000000000000, 0x8000000000000000, 0, 0, 0xc0000000, 0, 0x30000000, 0xe0000000)
        #self._do_CR_XER(op, emu, 0xFFFFFFFFFFFFFFFF, 0xFFFFFFFFFFFFFFFF, 0, 0, 0xa0000000, 0xfffffffffffffffe, 0x90000000, 0xa0000000)
        #self._do_CR_XER(op, emu, 1, 2, 0, 0, 0xa0000000, 3, 0x50000000, 0x80000000)

    def _do_CR_XER(self, op, emu, r1, r2, r3, cr, xer, expr3, expcr, expxer):
        print "== %x %x %x  %x %x  %x %x %x" % (r1, r2, r3, cr, xer, expr3, expcr, expxer)
        emu.setRegisterByName('r1', r1)
        emu.setRegisterByName('r2', r2)
        emu.setRegisterByName('r3', r3)
        emu.setRegisterByName('CR', cr)
        emu.setRegisterByName('XER', xer)

        emu.executeOpcode(op)

        newcr = emu.getRegisterByName('CR')
        newxer = emu.getRegisterByName('XER')
        newr3 = emu.getRegisterByName('r3')

        self.assertEqual((repr(op), r1, r2, r3, cr, xer, newr3, newcr, newxer), (repr(op), r1, r2, r3, cr, xer, expr3, expcr, expxer))


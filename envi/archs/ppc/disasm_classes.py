import envi
import envi.bits as e_bits

from envi import IF_NOFALL, IF_BRANCH, IF_CALL, IF_RET, IF_PRIV, IF_COND

from regs import *
from const import *

def addrToName(mcanv, va):
    sym = mcanv.syms.getSymByAddr(va)
    if sym != None:
        return repr(sym)
    return "0x%.8x" % va


IF_CALLCC = (IF_CALL | IF_COND)

class PpcOpcode(envi.Opcode):
    def __init__(self, va, opcode, mnem, size, operands, iflags=0):
        envi.Opcode.__init__(self, va, opcode, mnem, 0, size, operands, iflags)

    def getBranches(self, emu=None):
        ret = []

        # To start with we have no flags.
        flags = 0
        addb = False

        # If we are a conditional branch, even our fallthrough
        # case is conditional...
        if self.iflags & (IF_BRANCH | IF_COND):
            flags |= envi.BR_COND
            addb = True

        # If we can fall through, reflect that...
        if not self.iflags & envi.IF_NOFALL:
            ret.append((self.va + self.size, flags|envi.BR_FALL))

        # In intel, if we have no operands, it has no
        # further branches...
        if len(self.opers) == 0:
            return ret

        # Check for a call...
        if self.iflags & IF_CALL:
            flags |= envi.BR_PROC
            addb = True

        # A conditional call?  really?  what compiler did you use? ;)
        elif (self.iflags & IF_CALLCC) == IF_CALLCC:
            flags |= (envi.BR_PROC | envi.BR_COND)
            addb = True

        elif self.iflags == IF_BRANCH:
            addb = True

        if addb:
            oper0 = self.opers[0]
            if oper0.isDeref():
                flags |= envi.BR_DEREF
                tova = oper0.getOperAddr(self, emu=emu)
            else:
                tova = oper0.getOperValue(self, emu=emu)

            ret.append((tova, flags))

        return ret

    def render(self, mcanv):
        """
        Render this opcode to the specified memory canvas
        """
        if self.prefixes:
            pfx = self._getPrefixName(self.prefixes)
            if pfx:
                mcanv.addNameText("%s: " % pfx, pfx)

        mcanv.addNameText(self.mnem, typename="mnemonic")
        mcanv.addText(" ")

        # Allow each of our operands to render
        imax = len(self.opers)
        lasti = imax - 1
        for i in xrange(imax):
            oper = self.opers[i]
            oper.render(mcanv, self, i)
            if i != lasti:
                mcanv.addText(",")


class PpcRegOper(envi.RegisterOper):
    ''' register operand.'''

    def __init__(self, reg, va=0):
        self.va = va
        self.reg = reg
        

    def __eq__(self, oper):
        if not isinstance(oper, self.__class__):
            return False
        if self.reg != oper.reg:
            return False
        return True
    
    def involvesPC(self):
        return self.reg == 15

    def isDeref(self):
        return False

    def getOperValue(self, op, emu=None):
        if self.reg == REG_PC:
            return self.va  # FIXME: is this modified?  or do we need to att # to this?

        if emu == None:
            return None
        return emu.getRegister(self.reg)

    def setOperValue(self, op, emu=None, val=None):
        if emu == None:
            return None
        emu.setRegister(self.reg, val)

    def render(self, mcanv, op, idx):
        rname = ppc_regs[self.reg][0]
        mcanv.addNameText(rname, typename='registers')


    def repr(self, op):
        rname = ppc_regs[self.reg][0]
        return rname

class PpcFRegOper(PpcRegOper):
    ''' Floating Point register operand.'''
    def __init__(self, reg, va=0):
        self.va = va
        self.reg = reg + REG_IDX_FP
        
class PpcVRegOper(PpcRegOper):
    ''' Vector register operand.'''
    def __init__(self, reg, va=0):
        self.va = va
        self.reg = reg      + REG_IDX_VECTOR
        
class PpcCRegOper(PpcRegOper):
    ''' CR register operand.'''
    def __init__(self, reg, va=0):
        self.va = va
        self.reg = reg
        
    def render(self, mcanv, op, idx):
        #rname = ppc_regs[self.reg][0]
        rname = "cr%d" % self.reg
        mcanv.addNameText(rname, typename='registers')

    def repr(self, op):
        #rname = ppc_regs[self.reg][0]
        rname = "cr%d" % self.reg
        return rname


class PpcImmOper(envi.ImmedOper):
    ''' Immediate operand. '''
    def __init__(self, val, va=0):
        self.val = val

    def __eq__(self, oper):
        if not isinstance(oper, self.__class__):
            return False

        if self.getOperValue(None) != oper.getOperValue(None):
            return False

        return True

    def involvesPC(self):
        return False

    def isDeref(self):
        return False

    def isDiscrete(self):
        return True

    def getOperValue(self, op, emu=None):
        return self.val

    def render(self, mcanv, op, idx):
        val = self.getOperValue(op)
        mcanv.addNameText('0x%.2x' % (val))

    def repr(self, op):
        val = self.getOperValue(op)
        return '0x%x' % (val)

class PpcSImmOper(PpcImmOper):
    ''' Unsigned Immediate operand. '''
    def __init__(self, val, va=0, bits=5):
        if val & 1<<(bits-1):
            val |= e_bits.b_masks[bits]

        self.val = e_bits.signed(val, 4)

class PpcSImm5Oper(PpcSImmOper):
    ''' Signed Immediate operand bit 5. '''
    def __init__(self, val, va=0):
        PpcSImmOper.__init__(self, val, va, 5)

class PpcSImm16Oper(PpcSImmOper):
    ''' Unsigned Immediate operand. '''
    def __init__(self, val, va=0):
        PpcSImmOper.__init__(self, val, va, 16)

class PpcUImmOper(PpcImmOper):
    ''' Unsigned Immediate operand. '''
    def __init__(self, val, va=0):
        self.val = val

class PpcUImm1Oper(PpcUImmOper):
    ''' Unsigned Immediate operand. '''
    def __init__(self, val, va=0):
        self.val = val * 8

class PpcUImm2Oper(PpcUImmOper):
    ''' Unsigned Immediate operand. '''
    def __init__(self, val, va=0):
        self.val = val * 2

class PpcUImm3Oper(PpcUImmOper):
    ''' Unsigned Immediate operand. '''
    def __init__(self, val, va=0):
        self.val = val * 4



class PpcMemOper(envi.DerefOper):
    ''' immediate offset operand.

    0xOFFSET (base_reg)

    '''
    def __init__(self, base_reg, offset, va):
        self.base_reg = base_reg
        self.offset = offset
        self.va = va

    def __eq__(self, oper):
        if not isinstance(oper, self.__class__):
            return False
        if self.base_reg != oper.base_reg:
            return False
        if self.offset != oper.offset:
            return False
        return True

    def involvesPC(self):
        return self.base_reg == REG_PC

    def isDeref(self):
        return True

    def setOperValue(self, op, emu=None, val=None):
        # can't survive without an emulator
        if emu == None:
            return None

        addr = self.getOperAddr(op, emu)

        fmt = ("<I", ">I")[emu.getEndian()]
        emu.writeMemoryFormat(addr, fmt, val)

    def getOperValue(self, op, emu=None):
        # can't survive without an emulator
        if emu == None:
            return None

        addr = self.getOperAddr(op, emu)

        fmt = ("<I", ">I")[emu.getEndian()]
        ret, = emu.readMemoryFormat(addr, fmt)
        return ret

    def getOperAddr(self, op, emu=None):
        # there are certain circumstances where we can survive without an emulator
        # if we don't have an emulator, we must be PC-based since we know it
        if self.base_reg == REG_PC:
            addr = self.va
        elif emu == None:
            return None
        else:
            addr = emu.getRegister(self.base_reg)

        addr += self.offset

        return addr

    def render(self, mcanv, op, idx):
        basereg = ppc_regs[self.base_reg][0]
        if self.base_reg == REG_PC:

            addr = self.getOperAddr(op, mcanv.mem)    # only works without an emulator because we've already verified base_reg is PC

            mcanv.addText('(')
            if mcanv.mem.isValidPointer(addr):
                name = addrToName(mcanv, addr)
                mcanv.addVaText(name, addr)
            else:
                mcanv.addVaText('#0x%.8x' % addr, addr)

            mcanv.addText(')')

            value = self.getOperValue(op, mcanv.mem)
            if value != None:
                mcanv.addText("\t; ")
                if mcanv.mem.isValidPointer(value):
                    name = addrToName(mcanv, value)
                    mcanv.addVaText(name, value)
                else:
                    mcanv.addNameText("0x%x" % value)

        else:
            mcanv.addNameText('0x%x' % (self.offset))

            mcanv.addText('(')
            mcanv.addNameText(basereg, typename='registers')
            mcanv.addText(')')

    def repr(self, op):
        basereg = ppc_regs[self.base_reg][0]
        if self.base_reg == REG_PC:
            addr = self.getOperAddr(op)    # only works without an emulator because we've already verified base_reg is PC

            tname = "(0x%x)" % addr
        else:
            tname = '0x%x(%s)' % (self.offset, basereg)
        return tname


OPERCLASSES = {
    FIELD_BD : PpcImmOper,
    FIELD_BH : PpcImmOper,
    FIELD_BI : PpcImmOper,
    FIELD_BO : PpcImmOper,
    FIELD_CRM : PpcImmOper,
    FIELD_CT : PpcImmOper,
    FIELD_D : PpcImmOper,
    FIELD_DCRN0_4 : PpcImmOper,
    FIELD_DCRN5_9 : PpcImmOper,
    FIELD_DCTL : PpcImmOper,
    FIELD_DS : PpcImmOper,
    FIELD_DUI : PpcImmOper,
    FIELD_E : PpcImmOper,
    FIELD_FM : PpcImmOper,
    FIELD_IMM : PpcImmOper,
    FIELD_IU : PpcImmOper,
    FIELD_L : PpcImmOper,
    FIELD_LEV : PpcImmOper,
    FIELD_LI : PpcImmOper,
    FIELD_MB : PpcImmOper,
    FIELD_ME : PpcImmOper,
    FIELD_MO : PpcImmOper,
    FIELD_OC : PpcImmOper,
    FIELD_OU : PpcImmOper,
    FIELD_PMRN0_4 : PpcImmOper,
    FIELD_PMRN5_9 : PpcImmOper,
    FIELD_SA : PpcImmOper,
    FIELD_SH : PpcImmOper,
    FIELD_SIMM : PpcImmOper,
    FIELD_SIMM16 : PpcSImm16Oper,
    FIELD_SIMM5 : PpcSImm5Oper,
    FIELD_SPRN0_4 : PpcImmOper,
    FIELD_SPRN5_9 : PpcImmOper,
    FIELD_SS : PpcImmOper,
    FIELD_STRM : PpcImmOper,
    FIELD_T : PpcImmOper,
    FIELD_TBRN0_4 : PpcImmOper,
    FIELD_TBRN5_9 : PpcImmOper,
    FIELD_TH : PpcImmOper,
    FIELD_TMRN0_4 : PpcImmOper,
    FIELD_TMRN5_9 : PpcImmOper,
    FIELD_TO : PpcImmOper,
    FIELD_UIMM : PpcImmOper,
    FIELD_UIMM1 : PpcImmOper,
    FIELD_UIMM2 : PpcImmOper,
    FIELD_UIMM3 : PpcImmOper,
    FIELD_W : PpcImmOper,
    FIELD_WC : PpcImmOper,
    FIELD_WH : PpcImmOper,
    FIELD_crD : PpcCRegOper,
    FIELD_crb : PpcImmOper,
    FIELD_crbA : PpcImmOper,
    FIELD_crbB : PpcImmOper,
    FIELD_crbC : PpcImmOper,
    FIELD_crbD : PpcImmOper,
    FIELD_crfS : PpcCRegOper,
    FIELD_frA : PpcFRegOper,
    FIELD_frB : PpcFRegOper,
    FIELD_frC : PpcFRegOper,
    FIELD_frD : PpcFRegOper,
    FIELD_frS : PpcFRegOper,
    FIELD_mb0 : PpcImmOper,
    FIELD_mb1_5 : PpcImmOper,
    FIELD_me0 : PpcImmOper,
    FIELD_me1_5 : PpcImmOper,
    FIELD_rA : PpcRegOper,
    FIELD_rB : PpcRegOper,
    FIELD_rC : PpcRegOper,
    FIELD_rD : PpcRegOper,
    FIELD_rS : PpcRegOper,
    FIELD_sh0 : PpcImmOper,
    FIELD_sh1_5 : PpcImmOper,
    FIELD_vA : PpcVRegOper,
    FIELD_vB : PpcVRegOper,
    FIELD_vC : PpcVRegOper,
    FIELD_vD : PpcVRegOper,
    FIELD_vS : PpcVRegOper,
}

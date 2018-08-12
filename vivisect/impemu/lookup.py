'''
Home for the registered emulators of different types...
'''
import vivisect.impemu.platarch.h8 as v_i_h8
import vivisect.impemu.platarch.arm as v_i_arm
import vivisect.impemu.platarch.ppc as v_i_ppc
import vivisect.impemu.platarch.i386 as v_i_i386
import vivisect.impemu.platarch.amd64 as v_i_amd64
import vivisect.impemu.platarch.msp430 as v_i_msp430
import vivisect.impemu.platarch.windows as v_i_windows
import vivisect.impemu.platarch.decree as v_i_decree

workspace_emus  = {
    'h8' :v_i_h8.H8WorkspaceEmulator,
    'arm' :v_i_arm.ArmWorkspaceEmulator,
    'ppc' :v_i_ppc.PpcWorkspaceEmulator,
    'i386'  :v_i_i386.i386WorkspaceEmulator,
    'amd64' :v_i_amd64.Amd64WorkspaceEmulator,
    'msp430' :v_i_msp430.Msp430WorkspaceEmulator,
    'thumb2' :v_i_arm.ThumbWorkspaceEmulator,
    ('windows','i386'):v_i_windows.Windowsi386Emulator,
    ('decree','i386'):v_i_decree.Decreei386WorkspaceEmulator,
}

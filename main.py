from lpd8.lpd8 import LPD8
from lpd8.programs import Programs
from lpd8.pads import Pad, Pads
from lpd8.knobs import Knobs
from osc import Osc_Interface
from actions import Actions
from time import sleep

lpd8 = LPD8()
osc = Osc_Interface()
actions = Actions(lpd8, osc)

def configure_lpd8():
    """
    Configure pads on LPD8 and starts controller
    As we play with kind of virtual banks, all stacked on PGM 4, knobs will be defined in Actions class
    """

    # Exit pad is PAD  (upper right)
    lpd8.set_pad_mode(Programs.PGM_4, Pads.PAD_8, Pad.PUSH_MODE)
    lpd8.subscribe(actions.exit_running, Programs.PGM_4, LPD8.NOTE_ON, Pads.PAD_8)

    # All actions are assigned to PGM 4 as this is the starting program on LPD8
    # PAD 5 will control oscillator 1, PAD 1 will control oscillator 2
    # When oscillators are not active, pads are lit otherwise they blink at the same rate as the oscillators
    lpd8.set_pad_mode(Programs.PGM_4, Pads.PAD_1, Pad.SWITCH_MODE)
    lpd8.set_pad_mode(Programs.PGM_4, Pads.PAD_5, Pad.SWITCH_MODE)
    lpd8.set_pad_switch_state(Programs.PGM_4, Pads.PAD_1, Pad.ON)
    lpd8.set_pad_switch_state(Programs.PGM_4, Pads.PAD_5, Pad.ON)
    lpd8.subscribe(actions.on_off, Programs.PGM_4, LPD8.NOTE_ON, Pads.PAD_1)
    lpd8.subscribe(actions.on_off, Programs.PGM_4, LPD8.NOTE_ON, Pads.PAD_5)

    # PAD 2 and PAD 2 activate bank 2 (oscillator 1) bank 3 (oscillator 2) control values and ranges
    lpd8.set_pad_mode(Programs.PGM_4, Pads.PAD_2, Pad.SWITCH_MODE)
    lpd8.set_pad_mode(Programs.PGM_4, Pads.PAD_6, Pad.SWITCH_MODE)
    lpd8.set_pad_switch_state(Programs.PGM_4, Pads.PAD_2, Pad.OFF)
    lpd8.set_pad_switch_state(Programs.PGM_4, Pads.PAD_6, Pad.OFF)
    lpd8.subscribe(actions.switch_bank, Programs.PGM_4, LPD8.NOTE_ON, Pads.PAD_2)
    lpd8.subscribe(actions.switch_bank, Programs.PGM_4, LPD8.NOTE_ON, Pads.PAD_6)

    # PAD 7 activates bank 3 control values and ranges
    lpd8.set_pad_mode(Programs.PGM_4, Pads.PAD_7, Pad.SWITCH_MODE)
    lpd8.set_pad_switch_state(Programs.PGM_4, Pads.PAD_7, Pad.OFF)
    lpd8.subscribe(actions.switch_bank, Programs.PGM_4, LPD8.NOTE_ON, Pads.PAD_7)

    # PAD 3 activates bank 4 control values and ranges
    lpd8.set_pad_mode(Programs.PGM_4, Pads.PAD_3, Pad.SWITCH_MODE)
    lpd8.set_pad_switch_state(Programs.PGM_4, Pads.PAD_3, Pad.OFF)
    lpd8.subscribe(actions.switch_bank, Programs.PGM_4, LPD8.NOTE_ON, Pads.PAD_3)

    # All knobs send control information to SuperCollider and are not sticky
    lpd8.subscribe(actions.control_osc, Programs.PGM_4, LPD8.CTRL, Knobs.ALL_KNOBS)
    lpd8.set_not_sticky_knob(Programs.PGM_4, Knobs.ALL_KNOBS)

    # Update pad states and start pad process
    lpd8.pad_update()
    lpd8.start()

def configure_osc():
    """
    Configure OSC handlers and starts OSC
    :return:
    """
    osc.add_handler('beat', actions.beats)
    osc.start()

if __name__ == '__main__':

    # Configure LPD8 controller and try to start it
    configure_lpd8()

    # We check if LPD8 controller could be started. Only then we will start the loop and initiate the OSC server
    # We also load initial bank for knobs interactions and initialize oscillators default values
    running = lpd8.is_running()
    if running:
        configure_osc()
        actions.load_bank(0)
        actions.send_init()

    # Runs the forever loop
    while running:

        # All we do in this loop is checking it still has to run and we then sleep for a little while
        running = actions.check_running()
        sleep(.01)

    # We shutdown any running oscillator on SuperCollider
    osc.send('off', 0)
    osc.send('off', 1)

    # We clean up pads state
    lpd8.set_pad_switch_state(Programs.PGM_4, Pads.PAD_1, Pad.OFF)
    lpd8.set_pad_switch_state(Programs.PGM_4, Pads.PAD_2, Pad.OFF)
    lpd8.set_pad_switch_state(Programs.PGM_4, Pads.PAD_3, Pad.OFF)
    lpd8.set_pad_switch_state(Programs.PGM_4, Pads.PAD_5, Pad.OFF)
    lpd8.set_pad_switch_state(Programs.PGM_4, Pads.PAD_6, Pad.OFF)
    lpd8.set_pad_switch_state(Programs.PGM_4, Pads.PAD_7, Pad.OFF)
    lpd8.pad_update()

    # As we exit the loop, we tidy up running threads
    osc.stop()
    lpd8.stop()
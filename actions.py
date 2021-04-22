from lpd8.programs import Programs
from lpd8.pads import Pad, Pads
from lpd8.knobs import Knobs

class Actions:
    """
    Class used to implement main logic related to LPD8 and SuperCollider interactions
    """

    _on = [False, False]    # Synths state in SuperCollider - both off when starting program
    _active_bank = 0        # Active virtual bank for knobs

    def __init__(self, lpd8, osc):
        """
        Class constructor
        :param lpd8: an instance of LPD8 controller
        :param osc: an instance of an OSC client / server implementation
        """
        self._lpd8 = lpd8
        self._osc = osc
        self._running = True    # This is the running flag checked in the main loop

    def exit_running(self, data):
        """
        Exit running state and by extension main loop / program
        """
        self._running = False

    def check_running(self):
        """
        Allow to check running state in the main loop
        """
        return self._running

    def beats(self, *args):
        """
        This is a trick to allow PAD 5 controlled by oscillator 1 and PAD 1 controlled by oscillator 2
        to blink at different bpms (actually the beat of each oscillator)
        The beat is looped back through OSC messages from SuperCollider. When value of beat event is 1,
        PAD 5 is blinked, when it is 2, PAD 1 is blinked. Blink mode is added to the related pad only during
        the update and then immediately reset to avoid both pads to blink at oscillator 1 or oscillator 2 loop back
        """
        if args[1] == 1:
            self._lpd8.set_pad_mode(Programs.PGM_4, Pads.PAD_5, Pad.SWITCH_MODE + Pad.BLINK_MODE)
        elif args[1] == 2:
            self._lpd8.set_pad_mode(Programs.PGM_4, Pads.PAD_1, Pad.SWITCH_MODE + Pad.BLINK_MODE)
        self._lpd8.pad_update()
        self._lpd8.set_pad_mode(Programs.PGM_4, Pads.PAD_1, Pad.SWITCH_MODE)
        self._lpd8.set_pad_mode(Programs.PGM_4, Pads.PAD_5, Pad.SWITCH_MODE)

    def on_off(self, data):
        if data[1] == Pads.PAD_5:
            index = 0
        else:
            index = 1
        if self._on[index]:
            self._osc.send('off', index)
        else:
            self._osc.send('on', index)
        self._on[index] = not self._on[index]
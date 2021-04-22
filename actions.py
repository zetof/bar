from lpd8.programs import Programs
from lpd8.pads import Pad, Pads

class Actions:

    _on = [False, False]

    def __init__(self, lpd8, osc):
        self._lpd8 = lpd8
        self._osc = osc
        self._running = True

    def exit_running(self, data):
        self._running = False

    def check_running(self):
        return self._running

    def beats(self, msg, val):
        if val == 1:
            self._lpd8.set_pad_mode(Programs.PGM_4, Pads.PAD_5, Pad.SWITCH_MODE + Pad.BLINK_MODE)
        elif val == 2:
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
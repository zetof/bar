from lpd8.programs import Programs
from lpd8.pads import Pad, Pads
from lpd8.knobs import Knobs


class Actions:
    """
    Class used to implement main logic related to LPD8 <> SuperCollider interactions
    """

    _pad_to_bank = {        # pads to banks translation dict
        Pads.PAD_6: 0,
        Pads.PAD_2: 1,
        Pads.PAD_7: 2,
        Pads.PAD_3: 3,
        Pads.PAD_8: 4
    }
    _on = [False, False]    # Synths state in SuperCollider - both off when starting program
    _active_bank = 0        # Active virtual bank for knobs
    _banks = [              # Banks to save knobs value
        {
            Knobs.KNOB_1: 48,     # osc1 - note
            Knobs.KNOB_2: 1,      # osc1 - harmonics
            Knobs.KNOB_3: 0.05,   # osc1 - attack
            Knobs.KNOB_4: 0,      # osc1 - sweep
            Knobs.KNOB_5: 0,      # osc1 - detune
            Knobs.KNOB_6: 0.5,    # osc1 - duty
            Knobs.KNOB_7: 1,      # osc1 - release
            Knobs.KNOB_8: 0       # osc1 - sweep_time
        },
        {
            Knobs.KNOB_1: 60,     # osc1 - note
            Knobs.KNOB_2: 1,      # osc1 - harmonics
            Knobs.KNOB_3: 0.05,   # osc1 - attack
            Knobs.KNOB_4: 0,      # osc1 - sweep
            Knobs.KNOB_5: 0,      # osc1 - detune
            Knobs.KNOB_6: 0.5,    # osc1 - duty
            Knobs.KNOB_7: 1,      # osc1 - release
            Knobs.KNOB_8: 0       # osc1 - sweep_time
        },
        {
            Knobs.KNOB_1: 0,      # osc1 - feedback
            Knobs.KNOB_2: 0.5,    # osc1 - volume
            Knobs.KNOB_3: 0.5,    # master volume
            Knobs.KNOB_4: 1,      # master tempo
            Knobs.KNOB_5: 0,      # osc2 - feedback
            Knobs.KNOB_6: 0.5,    # osc2 - volume
            Knobs.KNOB_7: 0,      # master balance
            Knobs.KNOB_8: 0       # ?
        },
        {
            Knobs.KNOB_1: 0,      # delay - delay
            Knobs.KNOB_2: 0,      # delay - decay
            Knobs.KNOB_3: 10,     # delay - low pass
            Knobs.KNOB_4: 10000,  # delay - high pass
            Knobs.KNOB_5: 0,      # ?
            Knobs.KNOB_6: 0,      # ?
            Knobs.KNOB_7: 0,      # ?
            Knobs.KNOB_8: 0       # ?
        }
    ]

    def __init__(self, lpd8, osc):
        """
        Class constructor
        :param lpd8: an instance of LPD8 controller
        :param osc: an instance of an OSC client / server implementation
        """
        self._lpd8 = lpd8
        self._osc = osc
        self._running = True    # This is the running flag checked in the main loop

    def switch_bank(self, data):
        """
        Switch from a bank to another
        :param data: the data received from LPD8 midi message (position 1 is pad index, translated to oscillator index)
        """

        # Retrieve bank index associated to PAD
        index = self._pad_to_bank[data[1]]

        # Only switch if needed
        if index != self._active_bank:

            # Unlit previous pad and switch banks
            pad_off = list(self._pad_to_bank.keys())[list(self._pad_to_bank.values()).index(self._active_bank)]
            self._lpd8.set_pad_switch_state(Programs.PGM_4, pad_off, Pad.OFF)
            self._lpd8.pad_update()
            self._active_bank = index
            self.load_bank(self._active_bank)

        # Otherwise just make sure this pad is still lit
        else:
            self._lpd8.set_pad_switch_state(Programs.PGM_4, data[1], Pad.ON)

    def load_bank(self, bank):
        """
        Loads a parameter bank. Each bank may contain up to 8 parameters
        :param bank: bank number (from 0 to 4)
        """

        # Set limits for bank 0 or bank 1 (oscillators parameters)
        if bank == 0 or bank == 1:
            self._lpd8.set_knob_limits(Programs.PGM_4, Knobs.KNOB_1, 36, 84)
            self._lpd8.set_knob_limits(Programs.PGM_4, Knobs.KNOB_2, 1, 50)
            self._lpd8.set_knob_limits(Programs.PGM_4, Knobs.KNOB_3, 0.05, 1, is_int=False)
            self._lpd8.set_knob_limits(Programs.PGM_4, Knobs.KNOB_4, 0, 0.5, is_int=False)
            self._lpd8.set_knob_limits(Programs.PGM_4, Knobs.KNOB_5, -0.05, 0.05, is_int=False)
            self._lpd8.set_knob_limits(Programs.PGM_4, Knobs.KNOB_6, 0.01, 0.5, is_int=False)
            self._lpd8.set_knob_limits(Programs.PGM_4, Knobs.KNOB_7, 0.1, 5, is_int=False)
            self._lpd8.set_knob_limits(Programs.PGM_4, Knobs.KNOB_8, 0, 1, is_int=False)
        # Set limits for bank 2
        elif bank == 2:
            self._lpd8.set_knob_limits(Programs.PGM_4, Knobs.KNOB_1, 0, 100, is_int=False)
            self._lpd8.set_knob_limits(Programs.PGM_4, Knobs.KNOB_2, 0, 2, is_int=False)
            self._lpd8.set_knob_limits(Programs.PGM_4, Knobs.KNOB_3, 0, 1, is_int=False)
            self._lpd8.set_knob_limits(Programs.PGM_4, Knobs.KNOB_4, 0.5, 5, is_int=False)
            self._lpd8.set_knob_limits(Programs.PGM_4, Knobs.KNOB_5, 0, 100, is_int=False)
            self._lpd8.set_knob_limits(Programs.PGM_4, Knobs.KNOB_6, 0, 2, is_int=False)
            self._lpd8.set_knob_limits(Programs.PGM_4, Knobs.KNOB_7, -1, 1, is_int=False)
        # Set limits for bank 3
        elif bank == 3:
            self._lpd8.set_knob_limits(Programs.PGM_4, Knobs.KNOB_1, 0, 0.5, is_int=False)
            self._lpd8.set_knob_limits(Programs.PGM_4, Knobs.KNOB_2, 1, 5, is_int=False)
            self._lpd8.set_knob_limits(Programs.PGM_4, Knobs.KNOB_3, 10, 10000, is_exp=True)
            self._lpd8.set_knob_limits(Programs.PGM_4, Knobs.KNOB_4, 10, 10000, is_exp=True)

        # Load saved values for current bank
            for knob in Knobs.ALL_KNOBS:
                self._lpd8.set_knob_value(Programs.PGM_4, knob, self._banks[bank][knob])

    def send_init(self):
        """
        Send all banks data to SuperCollider so it can initialize the oscillators with bank's default values
        Also lit PAD 6 as this is the default one
        :return:
        """
        self._lpd8.set_pad_switch_state(Programs.PGM_4, Pads.PAD_6, Pad.ON)
        self._lpd8.pad_update()
        for index, bank in enumerate(self._banks):
            for knob, value in bank.items():
                self._osc.send('control', [index, knob, value])

    def exit_running(self, *args):
        """
        Exit running state and by extension main loop / program
        """
        self._running = False

    def check_running(self):
        """
        Allow to check running state in the main loop
        """
        return self._running

    def control_osc(self, data):
        """
        Send a parameter change to SuperCollider
        :param data: the data received from LPD8 midi message (position 1 is knob number and position 2 the value)
        """
        self._banks[self._active_bank][data[1]] = data[2]
        self._osc.send('control', [self._active_bank, data[1], data[2]])

    def beats(self, *args):
        """
        This is a trick to allow PAD 5 controlled by oscillator 1 and PAD 1 controlled by oscillator 2
        to blink at different BPMs (actually the beat of each oscillator)
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
        """
        Starts or stops an oscillator in SuperCollider. It toggles the oscillator status based on class flags
        :param data: the data received from LPD8 midi message (position 1 is the oscillator index)
        :return:
        """
        if data[1] == Pads.PAD_5:
            index = 0
        else:
            index = 1
        if self._on[index]:
            self._osc.send('off', index)
        else:
            self._osc.send('on', index)
        self._on[index] = not self._on[index]

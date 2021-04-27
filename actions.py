from lpd8.programs import Programs
from lpd8.pads import Pad, Pads
from lpd8.knobs import Knobs

class Actions:
    """
    Class used to implement main logic related to LPD8 <> SuperCollider interactions
    """

    _on = [False, False]    # Synths state in SuperCollider - both off when starting program
    _active_bank = [0, 0]   # Active virtual bank for knobs
    _previous_bank = [0, 0] # Previous active bank
    _banks = [              # Banks to save knobs value
        {
            Knobs.KNOB_1: 60,    # osc1 - freq
            Knobs.KNOB_2: 0,     # osc1 - detune
            Knobs.KNOB_3: 25,    # osc1 - harmonics
            Knobs.KNOB_4: 0.255, # osc1 - duty
            Knobs.KNOB_5: 60,    # osc2 - freq
            Knobs.KNOB_6: 0,     # osc2 - detune
            Knobs.KNOB_7: 25,    # osc2 - harmonics
            Knobs.KNOB_8: 0.255, # osc2 - duty
        },
        {
            Knobs.KNOB_1: 0.496, # osc1 - attack
            Knobs.KNOB_2: 2.45,  # osc1 - release
            Knobs.KNOB_3: 0.25,  # osc1 - sweep
            Knobs.KNOB_4: 0.5,   # osc1 - sweep_time
            Knobs.KNOB_5: 0.496, # osc2 - attack
            Knobs.KNOB_6: 2.45,  # osc2 - release
            Knobs.KNOB_7: 0.25,  # osc2 - sweep
            Knobs.KNOB_8: 0.5    # osc2 - sweep_time
        },
        {
            Knobs.KNOB_1: 0,     # osc1 - feedback
            Knobs.KNOB_2: 0.5,   # osc1 - volume
            Knobs.KNOB_3: 0.5,   # master volume
            Knobs.KNOB_4: 1,     # master tempo
            Knobs.KNOB_5: 0,     # osc2 - feedback
            Knobs.KNOB_6: 0.5,   # osc2 - volume
            Knobs.KNOB_7: 0,     # master balance
            Knobs.KNOB_8: 0      # osc2 - ?
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
        Switch from a bank to another for a given oscillator (identified by pad number)
        :param data: the data received from LPD8 midi message (position 1 is pad index, translated to oscillator index)
        """
        index = 0

        # Banks 0 and 1 are split banks (4 knobs : oscillator)
        # Other banks are global to the synth (even if some knobs are still specific to a synth)
        if self._active_bank[0] < 2  and (data[1] == Pads.PAD_2 or data[1] == Pads.PAD_6):
            if data[1] == Pads.PAD_2:
                index = 1
            if self._active_bank[index] == 1:
                self._active_bank[index] = 0
            else:
                self._active_bank[index] = 1
            self.load_bank(self._active_bank[index], index)

        # Bank 3 saves current split mode states and restores them when leaving the bank
        # Note that pads 2 and 6 are de-activated while in this mode
        elif data[1] == Pads.PAD_7:
            if self._active_bank[index] == 0 or self._active_bank[index] == 1:
                self._previous_bank[0] = self._active_bank[0]
                self._previous_bank[1] = self._active_bank[1]
                self._active_bank[0] = 2
                self._active_bank[1] = 2
                self._lpd8.set_pad_switch_state(Programs.PGM_4, Pads.PAD_2, Pad.OFF)
                self._lpd8.set_pad_switch_state(Programs.PGM_4, Pads.PAD_6, Pad.OFF)
                self._lpd8.set_pad_mode(Programs.PGM_4, Pads.PAD_2, Pad.NO_MODE)
                self._lpd8.set_pad_mode(Programs.PGM_4, Pads.PAD_6, Pad.NO_MODE)
                self._lpd8.pad_update()
            else:
                self._active_bank[0] = self._previous_bank[0]
                self._active_bank[1] = self._previous_bank[1]
                self._lpd8.set_pad_mode(Programs.PGM_4, Pads.PAD_2, Pad.SWITCH_MODE)
                self._lpd8.set_pad_mode(Programs.PGM_4, Pads.PAD_6, Pad.SWITCH_MODE)
                if self._active_bank[0] == 1:
                    self._lpd8.set_pad_switch_state(Programs.PGM_4, Pads.PAD_6, Pad.ON)
                if self._active_bank[1] == 1:
                    self._lpd8.set_pad_switch_state(Programs.PGM_4, Pads.PAD_2, Pad.ON)
                self._lpd8.pad_update()
            self.load_bank(self._active_bank[0], 0)
            self.load_bank(self._active_bank[1], 1)

    def load_bank(self, bank, osc):
        """
        Loads a parameter bank for a given oscillator. A bank controls 4 parameters of an oscillator. The first four
        parameters are for oscillator 1, the next four for oscillator 2
        :param bank: the bank number (from 0 to 1)
        :param osc: the oscillator number (from 0 to 1)
        """

        # Set limits for bank 0
        if bank == 0:

            # Set limits for oscillator 1
            if osc == 0:
                self._lpd8.set_knob_limits(Programs.PGM_4, Knobs.KNOB_1, 36, 84)
                self._lpd8.set_knob_limits(Programs.PGM_4, Knobs.KNOB_2, -0.05, 0.05, is_int=False)
                self._lpd8.set_knob_limits(Programs.PGM_4, Knobs.KNOB_3, 1, 50)
                self._lpd8.set_knob_limits(Programs.PGM_4, Knobs.KNOB_4, 0.01, 0.5, is_int=False)

            # Set limits for oscillator 2
            elif osc == 1:
                self._lpd8.set_knob_limits(Programs.PGM_4, Knobs.KNOB_5, 36, 84)
                self._lpd8.set_knob_limits(Programs.PGM_4, Knobs.KNOB_6, -0.05, 0.05, is_int=False)
                self._lpd8.set_knob_limits(Programs.PGM_4, Knobs.KNOB_7, 1, 50)
                self._lpd8.set_knob_limits(Programs.PGM_4, Knobs.KNOB_8, 0.01, 0.5, is_int=False)

        # Set limits for bank 1
        elif bank == 1:
            # Set limits for oscillator 1
            if osc == 0:
                self._lpd8.set_knob_limits(Programs.PGM_4, Knobs.KNOB_1, 0.05, 1, is_int=False)
                self._lpd8.set_knob_limits(Programs.PGM_4, Knobs.KNOB_2, 0.1, 5, is_int=False)
                self._lpd8.set_knob_limits(Programs.PGM_4, Knobs.KNOB_3, 0, 0.5, is_int=False)
                self._lpd8.set_knob_limits(Programs.PGM_4, Knobs.KNOB_4, 0, 1, is_int=False)

            # Set limits for oscillator 2
            elif osc == 1:
                self._lpd8.set_knob_limits(Programs.PGM_4, Knobs.KNOB_5, 0.05, 1, is_int=False)
                self._lpd8.set_knob_limits(Programs.PGM_4, Knobs.KNOB_6, 0.1, 5, is_int=False)
                self._lpd8.set_knob_limits(Programs.PGM_4, Knobs.KNOB_7, 0, 0.5, is_int=False)
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

        # Load saved values for current bank for oscillator 1
        if osc == 0:
            self._lpd8.set_knob_value(Programs.PGM_4, Knobs.KNOB_1, self._banks[bank][Knobs.KNOB_1])
            self._lpd8.set_knob_value(Programs.PGM_4, Knobs.KNOB_2, self._banks[bank][Knobs.KNOB_2])
            self._lpd8.set_knob_value(Programs.PGM_4, Knobs.KNOB_3, self._banks[bank][Knobs.KNOB_3])
            self._lpd8.set_knob_value(Programs.PGM_4, Knobs.KNOB_4, self._banks[bank][Knobs.KNOB_4])
        # Load saved values for current bank for oscillator 2
        if osc == 1:
            self._lpd8.set_knob_value(Programs.PGM_4, Knobs.KNOB_5, self._banks[bank][Knobs.KNOB_5])
            self._lpd8.set_knob_value(Programs.PGM_4, Knobs.KNOB_6, self._banks[bank][Knobs.KNOB_6])
            self._lpd8.set_knob_value(Programs.PGM_4, Knobs.KNOB_7, self._banks[bank][Knobs.KNOB_7])
            self._lpd8.set_knob_value(Programs.PGM_4, Knobs.KNOB_8, self._banks[bank][Knobs.KNOB_8])

    def send_init(self):
        """
        Send all banks data to Supercollider so it can initialize the oscillators with bank's default values
        :return:
        """
        for index, bank in enumerate(self._banks):
            for knob, value in bank.items():
                self._osc.send('control', [index, knob, value])

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

    def control_osc(self, data):
        """
        Send a parameter change to SuperCollider
        :param data: the data received from LPD8 midi message (position 1 is knob number and position 2 the value)
        """
        if data[1] in [Knobs.KNOB_1, Knobs.KNOB_2, Knobs.KNOB_3, Knobs.KNOB_4]:
            index = 0
        else:
            index = 1
        self._banks[self._active_bank[index]][data[1]] = data[2]
        self._osc.send('control', [self._active_bank[index], data[1], data[2]])


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
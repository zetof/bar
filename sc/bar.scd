s.boot;
(
// A SynthDef that allows to grow an original sine wave to a full blown square wave with up to 50 harmonics
// This synth also allows to control the duty cycle of the formed square wave
// Parameters:
//   * note           : the midi note to play
//   * detune         : a percentage of detuning from original frequency
//   * vol            : a multiplier to adjust master volume
//   * harmonics      : the number of harmonics to add to travel from a sine wave (=1) to a full blown square wave (=50)
//   * duty           : the duty cycle of thee formed square ware (effective from harmonics > 1)
//   * attack         : the attack time of the evelope
//   * release        : the release time of the evelope
//   * sweep          : the percentage of played frequency that is added to the original freaquency to start a sweep
//   * swwep_time     : the percentage of total sound time used for the sweep
//   * feed_in        : channel number for incoming feedback signal
//   * feed_out       : channel number for outgoing feedback signal
//   * mod_index      : modulation index from incoming signal
//   * output_channel : output channel, sent to additional effects or audio output
//
SynthDef(\squared_sin, {
	arg note=60, detune=0, vol=1,
	harmonics=1, duty=0.5,
	attack=0.1, release=1,
	sweep=0, sweep_time=0,
	feed_in=nil, feed_out=nil, mod_index=0,
	output_channel=0;
	var modulator = 0;
	var sweep_line = Line.kr(1 + sweep, 1, sweep_time * (attack + release));
	var freq = (1 + detune) * note.midicps;
	var env = EnvGen.ar(Env.perc(attack, release), doneAction:Done.freeSelf);
	var signal;
	if(feed_in.notNil, modulator = mod_index * InFeedback.ar(feed_in, 1));
	signal = {
		(1..50).sum {
			arg i;
			SinOsc.ar(freq * (sweep_line * i + modulator)
				, -0.5pi, -2 * InRange.kr(i, 1, harmonics) * vol / (i * pi) * (pi * duty * i).sin);
		}
	};
	signal = env * (duty * vol + signal);
	Out.ar(feed_out, signal);
	Out.ar(output_channel, signal);
}).add;

// A SynthDef that allows filtering of the generated signal
// Parameters:
//   * input_channel  : the channel number of the input signal before filtering
//   * output_channel : the channel number of the output signal after filtering
//
SynthDef(\filter, {
	arg input_channel=10, output_channel=12;
	Out.ar(output_channel, In.ar(input_channel, 1));
}).add;

// A SynthDef that introduces a delay on the input signal
// Delay is split through a low pass filter and a high pass filter so effect can be controlled more accurately
// Parameters:
//   * input_channel  : the channel number of the input signal before delaying
//   * output_channel : the channel number of the output signal after delaying
//   * delay          : delay time in seconds - basically the time of one echo
//   * decay          : decay time in seconds - basically the time it takes for the sound to completely fade away
//   * low-freq       : low frequency cutoff limit for the low pass filter
//   * high-freq      : high frequency cutoff limit for the high pass filter
//
SynthDef(\delay, {
	arg input_channel=12, output_channel=20, delay=0.25, decay=2, low_freq=440, high_freq=1000;
	var sig = In.ar(input_channel, 1);
	var low_delay = CombN.ar(LPF.ar(sig, low_freq), delay, delay, decay);
	var high_delay = CombN.ar(HPF.ar(sig, high_freq), delay, delay, decay);
	Out.ar(output_channel, sig + low_delay + high_delay);
}).add;

// A SynthDef that ouputs final sound and allows master level and balance controls
// Parameters:
//   * input_channel : the channel number at the end of synth and effects chain
//   * vol           : master volume control
//   * bal           : master balance (-1: left, 1: right)
//
SynthDef(\mixer, {
	arg input_channel=20, vol=0.5, bal=0;
	Out.ar(0, Pan2.ar(vol * In.ar(input_channel, 1), bal));
}).add;

// Set groups and their precedence
~synthGroup = Group.new;
~filterGroup = Group.after(~synthGroup);
~delayGroup = Group.after(~filterGroup);
~outputGroup = Group.after(~delayGroup);

// Instanciate effects and mixer synths
~filter = Synth(\filter, target:~filterGroup);
~delay = Synth(\delay, target:~delayGroup);
~mixer = Synth(\mixer, target:~outputGroup);

// Master metronome
~metronome = TempoClock.new;

// Default params for mixer module
~master_volume = 0.5;
~master_balance = 0;

// Default params for the oscillator synths
~play = [false, false];
~note = [60, 60];
~detune = [0, 0];
~vol = [0.5, 0.5];
~harmonics = [25, 25];
~duty = [0.125, 0.5];
~attack = [0.01, 0.1];
~release = [1, 1];
~sweep = [0, 0];
~sweep_time = [0, 0];
~mod_index = [0, 0];

// Make two pulsating synths from synth definition, all elements are adjustable from the outside world
// Each pulsating synth send an OSC message at start time, to allow a synchronization with the outside world
~osc = [Pbind(
	\instrument, \squared_sin,
	\note, Pfunc({ ~note[0] }, inf),
	\detune,  Pfunc({ ~detune[0] }),
	\vol,  Pfunc({ ~vol[0] }),
	\harmonics, Pfunc({ ~harmonics[0] }),
	\duty, Pfunc({ ~duty[0] }),
	\attack, Pfunc({ ~attack[0] / ~metronome.tempo }),
	\release, Pfunc({ ~release[0] / ~metronome.tempo }),
	\sweep,  Pfunc({ ~sweep[0] }),
	\sweep_time, Pfunc({ ~sweep_time[0] / ~metronome.tempo }),
	\feed_in, 2,
	\feed_out, 3,
	\output_channel, 10,
	\group, ~synthGroup,
	\mod_index, Pfunc({ ~mod_index[0] }),
	\dur, Pfunc({ ~attack[0] + ~release[0] }),
	\osc, Pfunc({~oscServer.sendMsg("/beat", 1) })
).play(~metronome, quant:1),
Pbind(
	\instrument, \squared_sin,
	\note, Pfunc({ ~note[1] }, inf),
	\detune,  Pfunc({ ~detune[1] }),
	\vol,  Pfunc({ ~vol[1] }),
	\harmonics, Pfunc({ ~harmonics[1] }),
	\duty, Pfunc({ ~duty[1] }),
	\attack, Pfunc({ ~attack[1] / ~metronome.tempo }),
	\release, Pfunc({ ~release[1] / ~metronome.tempo }),
	\sweep,  Pfunc({ ~sweep[1] }),
	\sweep_time,  Pfunc({ ~sweep_time[1] / ~metronome.tempo }),
	\feed_in, 3,
	\feed_out, 2,
	\output_channel, 10,
	\group, ~synthGroup,
	\mod_index, Pfunc({ ~mod_index[1] }),
	\dur, Pfunc({ ~attack[1] + ~release[1] }),
	\osc, Pfunc({ ~oscServer.sendMsg("/beat", 2) })
).play(~metronome, quant:1)];
~osc[0].stop;
~osc[1].stop;

// OSC address of pilot program and OSC event driver
~oscServer = NetAddr("127.0.0.1", 57130);

// Starts a synth
OSCdef.new(\on, {
	arg msg;
	~osc[msg[1]].play;
}, '/on');

// Stops a synth
OSCdef.new(\off, {
	arg msg;
	~osc[msg[1]].stop;
}, '/off');

// All knobs controls, split into bank effects (see LPD8 python program for more explanations)
OSCdef.new(\control, {
	arg msg;
	// BANK 1 (split): note, harmonics, duty, vol
	if(msg[1] == 0 && msg[2] == 1, { ~note[0] = msg[3] });
	if(msg[1] == 0 && msg[2] == 2, { ~detune[0] = msg[3] });
	if(msg[1] == 0 && msg[2] == 3, { ~harmonics[0] = msg[3] });
	if(msg[1] == 0 && msg[2] == 4, { ~duty[0] = msg[3] });
	if(msg[1] == 0 && msg[2] == 5, { ~note[1] = msg[3] });
	if(msg[1] == 0 && msg[2] == 6, { ~detune[1] = msg[3] });
	if(msg[1] == 0 && msg[2] == 7, { ~harmonics[1] = msg[3] });
	if(msg[1] == 0 && msg[2] == 8, { ~duty[1] = msg[3] });
	// BANK 2 (split): attack, release, sweep, seep time
	if(msg[1] == 1 && msg[2] == 1, { ~attack[0] = msg[3] });
	if(msg[1] == 1 && msg[2] == 2, { ~release[0] = msg[3] });
	if(msg[1] == 1 && msg[2] == 3, { ~sweep[0] = msg[3] });
	if(msg[1] == 1 && msg[2] == 4, { ~sweep_time[0] = msg[3] });
	if(msg[1] == 1 && msg[2] == 5, { ~attack[1] = msg[3] });
	if(msg[1] == 1 && msg[2] == 6, { ~release[1] = msg[3] });
	if(msg[1] == 1 && msg[2] == 7, { ~sweep[1] = msg[3] });
	if(msg[1] == 1 && msg[2] == 8, { ~sweep_time[1] = msg[3] });
	// BANK 3 full): feedback, volume, master volume, master balance
	if(msg[1] == 2 && msg[2] == 1, { ~mod_index[0] = msg[3] });
	if(msg[1] == 2 && msg[2] == 2, { ~vol[0] = msg[3] });
	if(msg[1] == 2 && msg[2] == 3, { ~master_volume = msg[3]; ~mixer.set(\vol, ~master_volume) });
	if(msg[1] == 2 && msg[2] == 4, { ~metronome.tempo = msg[3] });
	if(msg[1] == 2 && msg[2] == 5, { ~mod_index[1] = msg[3] });
	if(msg[1] == 2 && msg[2] == 6, { ~vol[1] = msg[3] });
	if(msg[1] == 2 && msg[2] == 7, { ~master_balance = msg[3]; ~mixer.set(\bal, ~master_balance) });
}, '/control');
)
~delay.set(\delay, 0.2);
~delay.set(\decay, 3);
~delay.set(\low_freq, 10);
~delay.set(\high_freq, 10000);
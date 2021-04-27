s.boot;
(
// A synthdef that allows to grow an original sine wave to a full blown square wave with up to 50 harmonics
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

SynthDef(\filter, {
	arg input_channel=10, output_channel=11;
	Out.ar(output_channel, In.ar(input_channel, 1));
}).add;

SynthDef(\delay, {
	arg input_channel=11, output_channel=20;
	Out.ar(output_channel, In.ar(input_channel, 1));
}).add;

SynthDef(\mixer, {
	arg input_channel=20, bal=0;
	Out.ar(0, Pan2.ar(In.ar(input_channel, 1), bal));
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
	\attack, Pfunc({ ~attack[0] }),
	\release, Pfunc({ ~release[0] }),
	\sweep,  Pfunc({ ~sweep[0] }),
	\sweep_time, Pfunc({ ~sweep_time[0] }),
	\feed_in, 2,
	\feed_out, 3,
	\output_channel, 10,
	\group, ~synthGroup,
	\mod_index, Pfunc({ ~mod_index[0] }),
	\dur, Pfunc({ ~attack[0] + ~release[0] }),
	\osc, Pfunc({~oscServer.sendMsg("/beat", 1) })
).play(),
Pbind(
	\instrument, \squared_sin,
	\note, Pfunc({ ~note[1] }, inf),
	\detune,  Pfunc({ ~detune[1] }),
	\vol,  Pfunc({ ~vol[1] }),
	\harmonics, Pfunc({ ~harmonics[1] }),
	\duty, Pfunc({ ~duty[1] }),
	\attack, Pfunc({ ~attack[1] }),
	\release, Pfunc({ ~release[1] }),
	\sweep,  Pfunc({ ~sweep[1] }),
	\sweep_time,  Pfunc({ ~sweep_time[1] }),
	\feed_in, 3,
	\feed_out, 2,
	\output_channel, 10,
	\group, ~synthGroup,
	\mod_index, Pfunc({ ~mod_index[1] }),
	\dur, Pfunc({ ~attack[1] + ~release[1] }),
	\osc, Pfunc({ ~oscServer.sendMsg("/beat", 2) })
).play()];
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
	// BANK 3 full): feedback, volume
	if(msg[1] == 2 && msg[2] == 1, { ~mod_index[0] = msg[3] });
	if(msg[1] == 2 && msg[2] == 2, { ~vol[0] = msg[3] });
	if(msg[1] == 2 && msg[2] == 5, { ~mod_index[1] = msg[3] });
	if(msg[1] == 2 && msg[2] == 6, { ~vol[1] = msg[3] });
}, '/control');
)

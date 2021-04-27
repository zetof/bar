s.boot;
(
// A synthdef that allows to grow an original sine wave to a full blown square wave with up to 50 harmonics
// This synth also allows to control the duty cycle of the formed square wave
// Parameters:
//   * note       : the midi note to play
//   * detune     : a percentage of detuning from original frequency
//   * vol        : a multiplier to adjust master volume
//   * harmonics  : the number of harmonics to add to travel from a sine wave (=1) to a full blown square wave (=50)
//   * duty       : the duty cycle of thee formed square ware (effective from harmonics > 1)
//   * attack     : the attack time of the evelope
//   * release    : the release time of the evelope
//   * sweep      : the percentage of played frequency that is added to the original freaquency to start a sweep
//   * swwep_time : the percentage of total sound time used for the sweep
//
SynthDef(\squared_sin, {
	arg note=60, detune=0, vol=1,
	harmonics=1, duty=0.5,
	attack=0.1, release=1,
	sweep=0, sweep_time=0,
	feed_in=nil, feed_out=nil, mod_index=0;
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
	Out.ar(0, signal);
}).add;
)

// Default params
(
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
)

// Make some pulsating synth from synth definitions
(
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
	\feed_in, 10,
	\feed_out, 20,
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
	\feed_in, 20,
	\feed_out, 10,
	\mod_index, Pfunc({ ~mod_index[1] }),
	\dur, Pfunc({ ~attack[1] + ~release[1] }),
	\osc, Pfunc({ ~oscServer.sendMsg("/beat", 2) })
).play()];
~osc[0].stop;
~osc[1].stop;
)

// OSC Controls
(
// OSC address of pilot program and OSC event driver
~oscServer = NetAddr("127.0.0.1", 57130);
OSCdef.new(\on, {
	arg msg;
	~osc[msg[1]].play;
}, '/on');
OSCdef.new(\off, {
	arg msg;
	~osc[msg[1]].stop;
}, '/off');
OSCdef.new(\control, {
	arg msg;
	// BANK 1: note, harmonics, duty, vol
	if(msg[1] == 0 && msg[2] == 1, { ~note[0] = msg[3] });
	if(msg[1] == 0 && msg[2] == 2, { ~detune[0] = msg[3] });
	if(msg[1] == 0 && msg[2] == 3, { ~harmonics[0] = msg[3] });
	if(msg[1] == 0 && msg[2] == 4, { ~duty[0] = msg[3] });
	if(msg[1] == 0 && msg[2] == 5, { ~note[1] = msg[3] });
	if(msg[1] == 0 && msg[2] == 6, { ~detune[1] = msg[3] });
	if(msg[1] == 0 && msg[2] == 7, { ~harmonics[1] = msg[3] });
	if(msg[1] == 0 && msg[2] == 8, { ~duty[1] = msg[3] });
	// BANK 2: attack, release, sweep, seep time
	if(msg[1] == 1 && msg[2] == 1, { ~attack[0] = msg[3] });
	if(msg[1] == 1 && msg[2] == 2, { ~release[0] = msg[3] });
	if(msg[1] == 1 && msg[2] == 3, { ~sweep[0] = msg[3] });
	if(msg[1] == 1 && msg[2] == 4, { ~sweep_time[0] = msg[3] });
	if(msg[1] == 1 && msg[2] == 5, { ~attack[1] = msg[3] });
	if(msg[1] == 1 && msg[2] == 6, { ~release[1] = msg[3] });
	if(msg[1] == 1 && msg[2] == 7, { ~sweep[1] = msg[3] });
	if(msg[1] == 1 && msg[2] == 8, { ~sweep_time[1] = msg[3] });
	// BANK 3: feedback
	if(msg[1] == 2 && msg[2] == 1, { ~mod_index[0] = msg[3] });
	if(msg[1] == 2 && msg[2] == 5, { ~mod_index[1] = msg[3] });
}, '/control');
)
s.boot;
(
// A synthdef that allows to grow an original sine wave to a full blown square wave with up to 50 harmonics
// This synth also allows to control the duty cycle of the formed square wave
// Parameters:
//   * note      : the midi note to play
//   * vol       : a multiplier to adjust master volume
//   * harmonics : the number of harmonics to add to travel from a sine wave (=1) to a full blown square wave (=50)
//   * duty      : the duty cycle of thee formed square ware (effective from harmonics > 1)
//   * attack    : the attack time of the evelope
//   * release   : the release time of the evelope
//
SynthDef(\squared_sin, {
	arg note=60, vol=1, harmonics=1, duty=0.5, attack=0.1, release=1;
	var env = EnvGen.ar(Env.perc(attack, release), doneAction:Done.freeSelf);
	var signal = {
		(1..50).sum {
			arg i;
			SinOsc.ar(note.midicps * i, -0.5pi, -2 * InRange.kr(i, 1, harmonics) * vol / (i * pi) * (pi * duty * i).sin);
		}
	};
	Out.ar(0, env * (duty * vol + signal));
}).add;
)

// Default params
(
~play = [false, false];
~note = [60, 60];
~vol = [0.5, 0.5];
~harmonics = [25, 25];
~duty = [0.125, 0.5];
~attack = [0.01, 0.1];
~release = [1, 1];
)

// Make some pulsating synth from synth definitions
(
~osc = [Pbind(
	\instrument, \squared_sin,
	\note, Pfunc({ ~note[0] }, inf),
	\vol,  Pfunc({ ~vol[0] }),
	\harmonics, Pfunc({ ~harmonics[0] }),
	\duty, Pfunc({ ~duty[0] }),
	\attack, Pfunc({ ~attack[0] }),
	\release, Pfunc({ ~release[0] }),
	\dur, Pfunc({ ~attack[0] + ~release[0] }),
	\osc, Pfunc({~oscServer.sendMsg("/beat", 1)})
).play(),
Pbind(
	\instrument, \squared_sin,
	\note, Pfunc({ ~note[1] }, inf),
	\vol,  Pfunc({ ~vol[1] }),
	\harmonics, Pfunc({ ~harmonics[1] }),
	\duty, Pfunc({ ~duty[1] }),
	\attack, Pfunc({ ~attack[1] }),
	\release, Pfunc({ ~release[1] }),
	\dur, Pfunc({ ~attack[1] + ~release[1] }),
	\osc, Pfunc({~oscServer.sendMsg("/beat", 2)})
).play()];
~osc[0].stop;
~osc[1].stop;
)


// OOSC Controls
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
	if(msg[1] == 0 && msg[2] == 2, { ~harmonics[0] = msg[3] });
	if(msg[1] == 0 && msg[2] == 3, { ~duty[0] = msg[3] });
	if(msg[1] == 0 && msg[2] == 4, { ~vol[0] = msg[3] });
	if(msg[1] == 0 && msg[2] == 5, { ~note[1] = msg[3] });
	if(msg[1] == 0 && msg[2] == 6, { ~harmonics[1] = msg[3] });
	if(msg[1] == 0 && msg[2] == 7, { ~duty[1] = msg[3] });
	if(msg[1] == 0 && msg[2] == 8, { ~vol[1] = msg[3] });
	if(msg[1] == 1 && msg[2] == 1, { ~attack[0] = msg[3] });
	if(msg[1] == 1 && msg[2] == 2, { ~release[0] = msg[3] });
	if(msg[1] == 1 && msg[2] == 5, { ~attack[1] = msg[3] });
	if(msg[1] == 1 && msg[2] == 6, { ~release[1] = msg[3] });
}, '/control');
)
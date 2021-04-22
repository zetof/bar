s.boot;
(
// A synthdef that allows to grow an original sine wave to a full blown square wave with up to 50 harmonics
// This synth also allows to control the duty cycle of the formed square wave
// Parameters:
//   * freq: the frequency of the fundamental in Hz
//   * level: a multiplier to adjust overal level
//   * harmonics: the number of harmonics to add to travel from a sine wave (=1) to a full blown square wave (=50)
//   * duty: the duty cycle of thee formed square ware (effective from harmonics > 1)
//
SynthDef(\squared_sin, {
	arg note=69, level=1, harmonics=1, duty=0.5, attack=0.1, release=1;
	var env = EnvGen.ar(Env.perc(attack, release), doneAction:Done.freeSelf);
	var signal = {
		(1..50).sum {
			arg i;
			SinOsc.ar(note.midicps * i, -0.5pi, -2 * InRange.kr(i, 1, harmonics) * level / (i * pi) * (pi * duty * i).sin);
		}
	};
	Out.ar(0, env * (duty * level + signal));
}).add;
)

// Default params
(
~play = [false, false];
~note = [60, 69];
~harmonics = [5, 30];
~duty = [0.125, 0.5];
~attack = [0.01, 0.1];
~release = [1, 1];
)

// Make some pulsating synth from synth definitions
(
~osc = [Pbind(
	\instrument, \squared_sin,
	\note, Pfunc({ ~note[0] }, inf),
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
	arg message;
	~osc[message[1]].play;
}, '/on');
OSCdef.new(\off, {
	arg message;
	~osc[message[1]].stop;
}, '/off');
)


// Midi Controls
(
MIDIClient.init;
MIDIIn.connectAll;
MIDIOut.findPort("LPD8", "LPD8");

MIDIdef.cc(\lpd8_control, {
	arg val, chan, src;
	[src, chan, val].postln;
	if(src == 3 && chan == 1, { ~note[0] = val.linlin(1, 127, 36, 84) });
	if(src == 3 && chan == 2, { ~harmonics[0] = val.linlin(1, 127, 1, 50) });
	if(src == 3 && chan == 3, { ~duty[0] = val.linlin(1, 127, 0.01, 0.5) });
	if(src == 3 && chan == 4, { ~attack[0] = val.linlin(1, 127, 0.01, 1) });
	if(src == 3 && chan == 5, { ~release[0] = val.linlin(1, 127, 0.1, 3) });
	if(src == 3 && chan == 13, { if(~play[0], { ~osc[0].stop; ~play[0] = false } , { ~osc[0].play; ~play[0] = true })});
	if(src == 1 && chan == 1, { ~note[1] = val.linlin(1, 127, 36, 84) });
	if(src == 1 && chan == 2, { ~harmonics[1] = val.linlin(1, 127, 1, 50) });
	if(src == 1 && chan == 3, { ~duty[1] = val.linlin(1, 127, 0.01, 0.5) });
	if(src == 1 && chan == 4, { ~attack[1] = val.linlin(1, 127, 0.01, 1) });
	if(src == 1 && chan == 5, { ~release[1] = val.linlin(1, 127, 0.1, 3) });
	//if(src == 0 && chan == 9 && val != 0, { if(~play[1], { ~osc[1].stop } , { ~osc[1].play }); ~play[1] = ~play[1].not });
});
)

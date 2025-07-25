export function speak(text: string) {
  const synth = window.speechSynthesis;
  const voices = synth.getVoices();
  const spanish = voices.find(v => v.lang.toLowerCase().startsWith('es'));
  const utter = new SpeechSynthesisUtterance(text);
  if (spanish) utter.voice = spanish;
  utter.rate = 1;
  synth.speak(utter);
}

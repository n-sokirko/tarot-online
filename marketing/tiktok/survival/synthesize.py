from pathlib import Path
import wave,json
from piper import PiperVoice
from piper.config import SynthesisConfig
root=Path(__file__).resolve().parent
import os
v=PiperVoice.load(os.environ.get('PIPER_VOICE_MODEL', '/workspace/.local/voices/ru_RU-dmitri-medium.onnx'))
lines=[
 ('Ты проснулся в мире Таро.','ТЫ В МИРЕ ТАРО'),
 ('Перед тобой три двери. До рассвета откроется только одна.','ТРИ ДВЕРИ. ОДИН ВЫБОР.'),
 ('Солнце, Луна или Звезда? Какую выберешь?','СОЛНЦЕ · ЛУНА · ЗВЕЗДА'),
 ('А свой расклад открой в Телеграм.','ТВОЙ РАСКЛАД — В TELEGRAM'),
 ('Таро́т онла́йн бот.','@tarott_online_bot'),
]
meta=[]
for i,(line,title) in enumerate(lines):
 p=root/f'voice-{i+1:02d}.wav'
 with wave.open(str(p),'wb') as w:v.synthesize_wav(line,w,syn_config=SynthesisConfig(length_scale=.94,noise_scale=.5,noise_w_scale=.6))
 with wave.open(str(p),'rb') as w:dur=w.getnframes()/w.getframerate()
 meta.append({'file':p.name,'text':line,'caption':title,'duration':round(dur,3)})
print(json.dumps(meta,ensure_ascii=False,indent=2));(root/'voice.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2))

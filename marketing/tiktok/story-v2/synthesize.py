from pathlib import Path
import json,wave,torch,numpy as np
ROOT=Path(__file__).resolve().parent
torch.set_num_threads(4)
m=torch.package.PackageImporter('/workspace/.local/voices/v5_cis_base.pt').load_pickle('tts_models','model')
lines=[
('Не открывай дверь, за которой слышишь свой голос. Даже если он просит тебя о помощи.', 'НЕ ОТКРЫВАЙ ЭТУ ДВЕРЬ', 'doors'),
('Ты очнулся в пустом городе. Ни людей, ни звуков. Только три двери посреди площади: Солнце, Луна и Звезда.', 'ТРИ ДВЕРИ ПОСРЕДИ ПЛОЩАДИ', 'doors'),
('В руке у тебя фонарь. На стекле проступает надпись: когда погаснет огонь, исчезнет и дорога назад.', 'КОГДА ПОГАСНЕТ ФОНАРЬ…', 'lantern'),
('Солнечная дверь обещает вернуть всё, что ты потерял. Ты уже тянешься к ручке… но останавливаешься.', 'СОЛНЦЕ ОБЕЩАЕТ ВЕРНУТЬ ПРОШЛОЕ', 'sun'),
('Из-за лунной двери звучит твой собственный голос. Он говорит: я знаю короткий путь. Просто доверься мне.', 'ЛУНА ГОВОРИТ ТВОИМ ГОЛОСОМ', 'moon'),
('Ты вспоминаешь предупреждение. И поднимаешь фонарь. Первые две двери дрожат и растворяются, как отражения в воде.', 'ТЫ ПОДНИМАЕШЬ ФОНАРЬ', 'doors'),
('Остаётся только Звезда. Она ничего не обещала. Ты толкаешь дверь — и чувствуешь прохладный воздух.', 'ЗВЕЗДА НИЧЕГО НЕ ОБЕЩАЛА', 'exit'),
('За порогом узкий мост. На другом берегу начинается рассвет. А у твоих ног лежит карта Звезды.', 'ПО ТУ СТОРОНУ — РАССВЕТ', 'exit'),
('Выход был там, где тебя не пытались убедить. Но это лишь история. А какую дверь выбрал бы ты?', 'КАКУЮ ДВЕРЬ ВЫБРАЛ БЫ ТЫ?', 'exit'),
('Со своим вопросом загляни в Таро онлайн. Открой расклад в Телеграм: Тарот онлайн бот.', '@tarott_online_bot', 'app')
]
meta=[]
for i,(text,title,shot) in enumerate(lines):
 a=m.apply_tts(text=text,speaker='ru_dmitriy',sample_rate=48000)
 p=ROOT/f'voice-{i:02}.wav'
 with wave.open(str(p),'wb') as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(48000);w.writeframes((a.numpy().clip(-1,1)*32767).astype(np.int16).tobytes())
 meta.append(dict(text=text,title=title,shot=shot,file=p.name,duration=len(a)/48000))
 print(i,round(len(a)/48000,2),flush=True)
(ROOT/'script.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2))
print('Total speech:',sum(x['duration'] for x in meta))

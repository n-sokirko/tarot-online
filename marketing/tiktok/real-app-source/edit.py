from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parent
OUT=ROOT.parent
OUT.mkdir(parents=True,exist_ok=True)
font='/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf'
bold='/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf'

def text(name, value):
    p=ROOT/(name+'.txt');p.write_text(value);return str(p)

def label(name,value,y,size,start=0,end=99,color='0xf4ede1',weight=bold):
    return f"drawtext=fontfile={weight}:textfile={text(name,value)}:fontcolor={color}:fontsize={size}:x=(w-tw)/2:y={y}:enable='between(t,{start},{end})'"

# The recorder preserves the CSS viewport in the top-left of a larger canvas.
# Crop that padding; all visible app pixels come from the unmodified browser.
common="crop=390:780:0:0,fps=30,setsar=1,format=yuv420p"
clips=[(2.9,5.6),(9.8,3.6),(20.5,4.3),(24.6,4.0)]
filters=[f'[0:v]{common},split=4[s0][s1][s2][s3]']
for i,(start,duration) in enumerate(clips):
    if i==3:
        filters.append(f'[s{i}]trim=start={start}:end=26.5,setpts=PTS-STARTPTS,tpad=stop_mode=clone:stop_duration=3,trim=duration={duration},settb=AVTB,fps=30[c{i}]')
    else:
        filters.append(f'[s{i}]trim=start={start}:duration={duration},setpts=PTS-STARTPTS,settb=AVTB,fps=30[c{i}]')
filters+=['[c0][c1]xfade=transition=fade:duration=0.2:offset=5.4,fps=30[x1]',
          '[x1][c2]xfade=transition=fade:duration=0.2:offset=8.8,fps=30[x2]',
          '[x2][c3]xfade=transition=fade:duration=0.2:offset=12.9,scale=660:1320:flags=lanczos,setsar=1[app]',
          'color=c=0x0c0913:s=1080x1920:r=30:d=16.9[bg]',
          '[bg]drawbox=x=204:y=234:w=672:h=1332:color=0xd9b77b:t=2[frame]',
          '[frame][app]overlay=x=210:y=240:shortest=1[screen]']
labels=[
 label('brand','ТАРО В ТВОЁМ TELEGRAM',64,34,color='0xd9b77b'),
 label('hook1','Один вопрос. Три карты.',130,52,0,5.4),
 label('hook2','Открой свою карту дня',130,52,5.4,8.8),
 label('hook3','Выбери карту. Узнай значение.',130,44,8.8,12.9),
 label('hook4','Попробуй прямо в боте',130,52,12.9,17),
 'drawbox=x=135:y=1605:w=810:h=98:color=0xd9b77b:t=fill',
 label('cta','@tarott_online_bot',1623,56,color='0x130d20'),
 label('footer','Открой бота · запусти приложение',1730,30,color='0xc9c0d5',weight=font),
]
filters.append('[screen]'+','.join(labels)+',tpad=stop_mode=clone:stop_duration=2.2,trim=duration=17[out]')
(ROOT/'edit-filter.txt').write_text(';\n'.join(filters))
cmd=['ffmpeg','-hide_banner','-loglevel','error','-y','-i',str(ROOT/'app-real.webm'),'-filter_complex_script',str(ROOT/'edit-filter.txt'),'-map','[out]','-an','-c:v','libx264','-preset','fast','-crf','19','-pix_fmt','yuv420p','-movflags','+faststart',str(OUT/'tarot-bot-real-app.mp4')]
subprocess.run(cmd,check=True)
print(OUT/'tarot-bot-real-app.mp4')

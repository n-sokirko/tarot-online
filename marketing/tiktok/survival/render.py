"""Render a narrated POV concept from a generated keyframe and real app footage.

Uses ffmpeg, not a neural video generator. Paid motion, if supplied separately,
can be swapped in at the storyboard stage; this file renders the local preview.
"""
from pathlib import Path
import json
import subprocess

ROOT = Path(__file__).resolve().parent
FONT = '/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf'
REGULAR = '/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf'

def run(cmd):
    subprocess.run(cmd, check=True)

def label(name, value, y, size, start, end, color='0xfff0d6', font=FONT):
    p = ROOT / f'caption-{name}.txt'
    p.write_text(value)
    return (f"drawtext=fontfile={font}:textfile={p}:fontsize={size}:fontcolor={color}:"
            f"shadowcolor=black:shadowx=2:shadowy=3:x=(w-tw)/2:y={y}:"
            f"enable='between(t,{start:.3f},{end:.3f})'")

def main():
    meta = json.loads((ROOT / 'voice.json').read_text())
    # Deliberate short pauses after the story question, and a readable CTA hold.
    pauses = [.4, .4, 1.2, .25, 2.4]
    atempo = .85
    t = 0
    for i, (m, pause) in enumerate(zip(meta, pauses)):
        m['start'] = round(t, 3)
        t += m['duration'] / atempo + pause
        m['end'] = round(t, 3)
        run(['ffmpeg','-hide_banner','-loglevel','error','-y','-i',str(ROOT/m['file']),
             '-af',f'atempo={atempo},apad=pad_dur={pause}',
             '-ar','44100','-ac','1',str(ROOT/f'part-{i}.wav')])
    (ROOT / 'timing.json').write_text(json.dumps(meta, ensure_ascii=False, indent=2))
    (ROOT / 'voice-concat.txt').write_text(''.join(f"file 'part-{i}.wav'\n" for i in range(len(meta))))
    run(['ffmpeg','-hide_banner','-loglevel','error','-y','-f','concat','-safe','0',
         '-i',str(ROOT/'voice-concat.txt'),'-af','highpass=f=85,loudnorm=I=-16:TP=-1.5:LRA=9',
         '-ar','44100',str(ROOT/'narration.wav')])
    story_end = meta[3]['start']
    app_duration = round(t-story_end, 3)
    frames = round(story_end*30)
    filters = [
        # A high-resolution intermediate reduces stepping during the camera push.
        f"[0:v]scale=2160:3840,zoompan=z='1+0.0005*on':x='iw/2-iw/zoom/2':y='ih/2-ih/zoom/2':d={frames}:s=1080x1920:fps=30,trim=duration={story_end},setpts=PTS-STARTPTS,setsar=1,format=yuv420p[story]",
        f'[1:v]trim=start=20.8:duration={app_duration},setpts=PTS-STARTPTS,crop=390:780:0:0,scale=660:1320:flags=lanczos,fps=30,setsar=1,format=yuv420p[app]',
        f'color=c=0x0c0913:s=1080x1920:r=30:d={app_duration}[bg]',
        '[bg][app]overlay=x=210:y=270:shortest=1[phone]',
        '[story][phone]concat=n=2:v=1:a=0[edit]',
    ]
    labels = [
        "drawbox=x=0:y=0:w=1080:h=330:color=black@0.55:t=fill",
        label('pov','POV · ИГРОВОЙ МИР ТАРО',65,30,0,story_end,'0xe2c48c'),
        label('hook','ТЫ В МИРЕ ТАРО',150,64,0,meta[0]['end']),
        label('stakes1','ТРИ ДВЕРИ.',145,64,meta[1]['start'],meta[1]['end']),
        label('stakes2','ОДИН ВЫБОР ДО РАССВЕТА.',230,45,meta[1]['start'],meta[1]['end']),
        label('choice','СОЛНЦЕ · ЛУНА · ЗВЕЗДА',150,46,meta[2]['start'],story_end),
        label('question','КАКУЮ ВЫБЕРЕШЬ?',250,40,meta[2]['start']+1,story_end),
        label('app1','ТВОЙ РАСКЛАД',110,54,story_end,t),
        label('app2','В TELEGRAM',190,50,story_end,t,'0xe2c48c'),
        f"drawbox=x=115:y=1635:w=850:h=95:color=0xe2c48c:t=fill:enable='gte(t,{story_end})'",
        label('handle','@tarott_online_bot',1652,56,story_end,t,'0x150d21'),
        label('ai','AI-СЦЕНА · ДЕМОНСТРАЦИОННЫЙ СЮЖЕТ',1790,22,0,story_end,'0xdfd4dc',REGULAR),
        label('link','ОТКРОЙ БОТА · ЗАПУСТИ ПРИЛОЖЕНИЕ',1780,26,story_end,t,'0xdfd4dc',REGULAR),
    ]
    filters.append('[edit]'+','.join(labels)+'[video]')
    # Original synthesized atmosphere, kept below the narration; no licensed song.
    filters += [
        f"anoisesrc=color=pink:amplitude=0.025:duration={t},lowpass=f=850,afade=t=in:d=1,afade=t=out:st={t-1}:d=1[wind]",
        f"sine=frequency=110:duration={t},volume=0.02,afade=t=in:d=1,afade=t=out:st={t-1}:d=1[drone]",
        f'[2:a]aresample=44100,apad,atrim=duration={t}[voice]',
        '[voice][wind][drone]amix=inputs=3:normalize=0,alimiter=limit=0.89:level=0[audio]',
    ]
    (ROOT/'filter.txt').write_text(';\n'.join(filters))
    run(['ffmpeg','-hide_banner','-loglevel','error','-y','-i',str(ROOT/'doors-keyframe.png'),
         '-i',str(ROOT.parent/'real-app-source/app-real.webm'),'-i',str(ROOT/'narration.wav'),
         '-filter_complex_script',str(ROOT/'filter.txt'),'-map','[video]','-map','[audio]',
         '-t',str(round(t,3)),'-c:v','libx264','-preset','fast','-crf','20','-pix_fmt','yuv420p',
         '-c:a','aac','-b:a','160k','-movflags','+faststart',str(ROOT/'tarot-survival-voice.mp4')])
    print('Rendered:', ROOT/'tarot-survival-voice.mp4', 'seconds:', round(t,3))

if __name__ == '__main__':
    main()

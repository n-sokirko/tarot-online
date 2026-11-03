from pathlib import Path
import json,subprocess,textwrap
ROOT=Path(__file__).resolve().parent
WORK=ROOT/'work';WORK.mkdir(exist_ok=True)
FONT='/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf'
REG='/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf'
def run(cmd):subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y']+cmd,check=True)
meta=json.loads((ROOT/'script.json').read_text());cursor=0
for i,m in enumerate(meta):
 duration=m['duration']+[.5,.4,.7,.5,.6,.5,.6,.6,.8,1.5][i];m['start']=cursor;m['end']=cursor+duration;cursor+=duration
 image=ROOT/'exit.png' if m['shot'] in ['exit','lantern'] else ROOT.parent/'survival/doors-keyframe.png'
 title=WORK/f'title{i}.txt';title.write_text('\n'.join(textwrap.wrap(m['title'],width=29)))
 label=WORK/'label.txt';label.write_text('ИСТОРИЯ В МИРЕ ТАРО')
 caption=WORK/f'sub{i}.srt'
 def stamp(s):
  ms=round(s*1000);sec,ms=divmod(ms,1000);mi,se=divmod(sec,60);h,mi=divmod(mi,60);return f'{h:02}:{mi:02}:{se:02},{ms:03}'
 words=m['text'].split();chunks=[' '.join(words[n:n+7]) for n in range(0,len(words),7)]
 cap=[];ct=0
 for j,c in enumerate(chunks):
  end=ct+m['duration']*len(c.split())/len(words);cap.append(f'{j+1}\n{stamp(ct)} --> {stamp(end)}\n{c}');ct=end
 caption.write_text('\n\n'.join(cap))
 if m['shot']=='app':
  inp=['-stream_loop','-1','-i',str(ROOT.parent/'real-app-source/app-real.webm')]
  base='trim=start=20.5,setpts=PTS-STARTPTS,crop=390:780:0:0,scale=540:1080,pad=720:1280:90:100:color=0x0c0913,fps=30'
 else:
  z=1.05 if m['shot'] in ['doors','exit'] else 1.7 if m['shot'] in ['sun','moon'] else 2.1
  x='(iw-iw/zoom)/2' if m['shot'] not in ['sun','lantern'] else '(iw-iw/zoom)*0.05'
  y='(ih-ih/zoom)/2' if m['shot']!='lantern' else 'ih-ih/zoom'
  inp=['-loop','1','-i',str(image)]
  base=f"scale=1440:2560,zoompan=z='{z}+0.00015*on':x='{x}':y='{y}':d=1:s=720x1280:fps=30"
 vf=base+f",drawbox=x=0:y=0:w=720:h=190:color=black@0.55:t=fill,drawtext=fontfile={FONT}:textfile={title}:fontsize=30:fontcolor=0xffefdb:x=(w-tw)/2:y=76:line_spacing=9,drawtext=fontfile={REG}:textfile={label}:fontsize=17:fontcolor=0xe1c38f:x=(w-tw)/2:y=32,subtitles={caption}:force_style='FontName=Noto Sans,FontSize=16,PrimaryColour=&H00FFFFFF,OutlineColour=&H00201010,BorderStyle=1,Outline=2,Alignment=2,MarginV=86',fade=t=in:d=0.12,fade=t=out:st={duration-.12}:d=0.12"
 if m['shot']=='app':
  handle=WORK/'handle.txt';handle.write_text('@tarott_online_bot');vf+=f",drawbox=x=50:y=1150:w=620:h=70:color=0xe2c48c:t=fill,drawtext=fontfile={FONT}:textfile={handle}:fontsize=35:fontcolor=0x140d20:x=(w-tw)/2:y=1165"
 run(inp+['-i',str(ROOT/m['file']),'-vf',vf,'-af',f'highpass=f=70,apad,atrim=duration={duration}', '-t',str(duration),'-c:v','libx264','-preset','fast','-crf','21','-pix_fmt','yuv420p','-c:a','aac','-ar','48000','-b:a','160k',str(WORK/f'shot{i:02}.mp4')])
 print('Rendered shot',i,round(duration,1),flush=True)
(WORK/'concat.txt').write_text(''.join(f"file 'shot{i:02}.mp4'\n" for i in range(len(meta))))
run(['-f','concat','-safe','0','-i',str(WORK/'concat.txt'),'-filter_complex',f"[0:a]loudnorm=I=-16:TP=-1.5:LRA=9[voice];anoisesrc=color=pink:amplitude=0.008:duration={cursor},lowpass=f=500[air];[voice][air]amix=inputs=2:normalize=0,alimiter=limit=0.89:level=0[a]",'-map','0:v','-map','[a]','-c:v','copy','-c:a','aac','-ar','48000','-b:a','160k','-movflags','+faststart',str(ROOT/'tarot-story-v2.mp4')])
(ROOT/'timing.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2))
print('TOTAL',cursor)

from PIL import Image, ImageDraw, ImageFont
import math, random, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
W, H, FPS, SECONDS = 720, 1280, 24, 18
REG = '/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf'
BOLD = '/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf'
def font(size, bold=False):
    return ImageFont.truetype(BOLD if bold else REG, size)
random.seed(14)
stars = [(random.randrange(40,680),random.randrange(100,1140),random.choice([1,1,2]),random.random()*6) for _ in range(70)]
base = Image.new('RGB',(W,H))
pix = base.load()
for y in range(H):
    for x in range(W):
        glow = max(0, 1-math.hypot((x-360)/550,(y-640)/720))
        pix[x,y] = (int(12+17*glow),int(11+9*glow),int(24+26*glow))
GOLD=(225,193,135)
WHITE=(244,236,223)
MUTED=(180,169,190)
def center(d,text,y,size=36,color=WHITE,bold=False):
    f=font(size,bold)
    d.text((W/2,y),text,font=f,fill=color,anchor='mt')
def card(d,cx,cy,angle,phase,t):
    width,height=150,240
    x,y=int(cx-width/2),int(cy-height/2)
    d.rounded_rectangle((x,y,x+width,y+height),radius=14,fill=(31,24,48),outline=GOLD,width=2)
    d.rounded_rectangle((x+10,y+10,x+width-10,y+height-10),radius=8,outline=(105,82,112),width=1)
    center_x,center_y=x+width/2,y+height/2
    if phase==0:
        d.ellipse((center_x-35,center_y-35,center_x+35,center_y+35),outline=GOLD,width=2)
        for j in range(8):
            a=j*math.pi/4+t*.05
            d.line((center_x+45*math.cos(a),center_y+45*math.sin(a),center_x+53*math.cos(a),center_y+53*math.sin(a)),fill=GOLD,width=2)
    elif phase==1:
        d.ellipse((center_x-33,center_y-37,center_x+33,center_y+37),fill=GOLD)
        d.ellipse((center_x-12,center_y-46,center_x+43,center_y+25),fill=(31,24,48))
    else:
        pts=[(center_x+44*math.cos(j*math.pi*4/5-math.pi/2),center_y+44*math.sin(j*math.pi*4/5-math.pi/2)) for j in range(5)]
        d.line(pts+[pts[0]],fill=GOLD,width=2)
    d.text((center_x,y+height-39),['I','II','III'][phase],font=font(19),fill=GOLD,anchor='mt')

cmd=['ffmpeg','-hide_banner','-loglevel','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-an','-c:v','libx264','-preset','fast','-crf','20','-pix_fmt','yuv420p','-movflags','+faststart',str(ROOT/'tarot-tiktok-01.mp4')]
p=subprocess.Popen(cmd,stdin=subprocess.PIPE)
for i in range(FPS*SECONDS):
    t=i/FPS
    im=base.copy(); d=ImageDraw.Draw(im)
    for x,y,r,phase in stars:
        v=int(100+65*math.sin(t*.8+phase))
        d.ellipse((x-r,y-r,x+r,y+r),fill=(v,int(v*.85),int(v*.95)))
    center(d,'T A R O T   O N L I N E',160,23,GOLD)
    scene=0 if t<5 else 1 if t<11 else 2
    if scene==0:
        center(d,'Есть вопрос,',285,52,bold=True)
        center(d,'который не отпускает?',355,43,bold=True)
        center(d,'Посмотрите на него через образы',905,26,color=MUTED)
        center(d,'карт Таро',945,30,color=MUTED)
    elif scene==1:
        center(d,'Один вопрос.',285,50,bold=True)
        center(d,'Три карты.',355,50,bold=True)
        center(d,'«На что обратить внимание',905,28,color=MUTED)
        center(d,'в следующем шаге?»',949,28,color=MUTED)
    else:
        center(d,'Время для себя',285,50,bold=True)
        center(d,'и нового взгляда',355,43,bold=True)
        center(d,'Попробуйте расклад',875,34,bold=True)
        d.rounded_rectangle((130,945,590,1025),radius=24,fill=GOLD)
        center(d,'sokirdon.com',960,36,color=(24,17,34),bold=True)
        center(d,'Базовые описания — бесплатно',1055,23,color=MUTED)
        center(d,'AI-разбор — платная опция',1090,23,color=MUTED)
    for j,cx in enumerate([175,360,545]):
        entry=min(1,max(0,(t-j*.35)/1.0))
        entry=1-(1-entry)**3
        card(d,cx,650+(1-entry)*850+math.sin(t*1.1+j)*6,0,j,t)
    d.line((90,1165,630,1165),fill=(69,55,78),width=2)
    d.line((90,1165,90+int(540*(i+1)/(FPS*SECONDS)),1165),fill=GOLD,width=2)
    p.stdin.write(im.tobytes())
p.stdin.close()
if p.wait():
    raise SystemExit('ffmpeg failed')
print(ROOT/'tarot-tiktok-01.mp4')

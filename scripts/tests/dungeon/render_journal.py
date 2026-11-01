"""Render actual mocked Lua frame primitives for layout inspection, not a live WoW screenshot."""
from pathlib import Path
import math,re,sys
from PIL import Image,ImageDraw,ImageFont
from lupa.lua51 import LuaRuntime

HERE=Path(__file__).parent
addon=Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).resolve().parents[3]/'ElmoDungeonLoot'
out=Path(sys.argv[2]) if len(sys.argv)>2 else Path('/tmp/classicdungeon-journal-preview.png')
vm=LuaRuntime(unpack_returned_tuples=True)
for file in ['wow_mock.lua','journal_mock.lua']:vm.execute((HERE/file).read_text())
ns=vm.table();load=vm.eval('function(s,ns) assert(loadstring(s))("ElmoDungeonLoot",ns) end')
for file in (addon/'ElmoDungeonLoot.toc').read_text().splitlines():
    if file.endswith('.lua'):load((addon/file).read_text(),ns)
vm.globals().CD=ns
vm.execute('MOCK.level=20; MOCK.class="HUNTER"; CD.frame:GetScript("OnEvent")(CD.frame,"ADDON_LOADED","ElmoDungeonLoot"); CD.UI.Show()')
frames={f.mockID:f for f in vm.globals().MOCK.frames.values()}
root=ns.UI.frame
cache={}
factor={'TOPLEFT':(0,0),'TOP':(.5,0),'TOPRIGHT':(1,0),'LEFT':(0,.5),'CENTER':(.5,.5),
    'RIGHT':(1,.5),'BOTTOMLEFT':(0,1),'BOTTOM':(.5,1),'BOTTOMRIGHT':(1,1)}
def bbox(f):
    if f is None or f.mockID is None:return (0,0,1440,900)
    if f.mockID in cache:return cache[f.mockID]
    if f.mockID==root.mockID:return (0,0,1180,720)
    # Parent positions are resolved before dependants; cyclic anchors would be an error.
    parent=bbox(f.parent)
    if f.allPoints:return bbox(f.allPoints)
    width=f.width or (getfont(f).getlength(str(f.text or ''))+1 if f.kind=='FontString' else 0)
    h=f.height or ((f.fontSize or 12)*1.12 if f.kind=='FontString' else 0)
    anchors=list(f.anchors.values()) if f.anchors is not None else []
    points=[]
    for a in anchors:
        entries=list(a.values());which=entries[0]
        if len(entries)>=2 and hasattr(entries[1],'items'):
            relative=entries[1];rel=entries[2] if len(entries)>2 and isinstance(entries[2],str) else which
            dx=entries[3] if len(entries)>3 else 0;dy=entries[4] if len(entries)>4 else 0
        else:
            relative=f.parent;rel=which;dx=entries[1] if len(entries)>1 else 0;dy=entries[2] if len(entries)>2 else 0
        r=bbox(relative);fx,fy=factor[rel]
        points.append((which,r[0]+r[2]*fx+dx,r[1]+r[3]*fy-dy))
    if len(points)>=2:
        a,b=points[0],points[1];ax,ay=factor[a[0]];bx,by=factor[b[0]]
        if ax!=bx:width=(b[1]-a[1])/(bx-ax)
        if ay!=by:h=(b[2]-a[2])/(by-ay)
    x,y=parent[:2]
    if points:
        a=points[0];fx,fy=factor[a[0]];x,y=a[1]-width*fx,a[2]-h*fy
    if f.parent is not None and f.parent.kind=='ScrollFrame':y-=f.parent.scroll or 0
    result=(x,y,width,h);cache[f.mockID]=result;return result

def visible(f):
    p=f
    while p is not None and p.mockID is not None:
        if p.shown==False:return False
        p=p.parent
    return True

def clip(f):
    p=f.parent
    while p is not None and p.mockID is not None:
        if p.kind=='ScrollFrame':return bbox(p)
        p=p.parent
    return (0,0,1180,720)

image=Image.new('RGBA',(1180,720),(8,8,8,255))
fonts={}
def getfont(f):
    size=int(f.fontSize or 12)
    path=addon/'Fonts/Cinzel.ttf' if 'Cinzel' in (f.font or '') else Path('/System/Library/Fonts/Supplemental/Arial.ttf')
    key=str(path),size
    if key not in fonts:fonts[key]=ImageFont.truetype(str(path),size)
    return fonts[key]

for f in frames.values():
    if not visible(f) or f.layer=='HIGHLIGHT':continue
    x,y,w,h=bbox(f)
    if w<=0 or h<=0:continue
    layer=Image.new('RGBA',image.size)
    draw=ImageDraw.Draw(layer)
    if f.kind=='Texture':
        path=f.texture or ''
        if path.endswith('.png'):
            name=path.split('\\')[-1];source=addon/'Media/skin'/name
            if source.exists():
                tile=Image.open(source).convert('RGBA').resize((max(1,round(w)),max(1,round(h))))
                layer.alpha_composite(tile,(round(x),round(y)))
        elif f.vertexColor:
            values=list(f.vertexColor.values())
            rgb=tuple(round(v*255) for v in values[:3]);a=(f.alpha or (values[3] if len(values)>3 else 1))
            draw.rectangle((x,y,x+w,y+h),fill=rgb+(round(a*255),))
    elif f.kind=='FontString':
        font=getfont(f);s=re.sub(r'\|c[0-9a-fA-F]{8}|\|r','',str(f.text or ''))
        color=tuple(int(c*255) for c in (list(f.color.values()) if f.color else [1,1,1]))+(255,)
        yy=y
        for paragraph in s.split('\n'):
            lines=['']
            for word in paragraph.split(' '):
                candidate=(lines[-1]+' '+word).strip()
                if font.getlength(candidate)>w and lines[-1]:lines.append(word)
                else:lines[-1]=candidate
            for line in lines:
                draw.text((x,yy),line,font=font,fill=color,stroke_width=0)
                yy+=(f.fontSize or 12)*1.12
    elif f.backColor:
        def rgba(table):return tuple(round(v*255) for v in table.values())
        draw.rectangle((x,y,x+w,y+h),fill=rgba(f.backColor),outline=rgba(f.borderColor))
    cx,cy,cw,ch=clip(f)
    region=(max(0,round(cx)),max(0,round(cy)),min(1180,round(cx+cw)),min(720,round(cy+ch)))
    if region[2]>region[0] and region[3]>region[1]:image.alpha_composite(layer.crop(region),(region[0],region[1]))
image.convert('RGB').save(out)
print(out)

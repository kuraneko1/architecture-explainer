"""Measured text obstacles + orthogonal routing for architecture figures."""
import argparse
import heapq
import json
import math
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Circle
from matplotlib.colors import to_rgba
from PIL import Image

PALETTES = Path(__file__).resolve().parents[1] / 'assets/palettes.json'


def inflate(rect, pad=6):
    x, y, w, h = rect
    return (x-pad, y-pad, w+2*pad, h+2*pad)


def intersects(a, b, rect):
    """Axis-aligned segment against an open rectangle interior."""
    x,y,w,h=rect; eps=1e-5
    if abs(a[0]-b[0]) < eps:
        return x+eps<a[0]<x+w-eps and max(min(a[1],b[1]),y+eps)<min(max(a[1],b[1]),y+h-eps)
    if abs(a[1]-b[1]) < eps:
        return y+eps<a[1]<y+h-eps and max(min(a[0],b[0]),x+eps)<min(max(a[0],b[0]),x+w-eps)
    raise ValueError('Router requires orthogonal segments')


def clear(points, obstacles):
    return all(not intersects(a,b,r) for a,b in zip(points,points[1:]) for r in obstacles)


def subtract_rect(rect, cut):
    """Subtract shared terminal clearance from an edge's reserved rectangle."""
    x,y,w,h=rect;u,v,cw,ch=cut
    l,t,r,b=max(x,u),max(y,v),min(x+w,u+cw),min(y+h,v+ch)
    if l>=r or t>=b:return [rect]
    return [part for part in ((x,y,l-x,h),(r,y,x+w-r,h),(l,y,r-l,t-y),(l,b,r-l,y+h-b)) if part[2]>0 and part[3]>0]


def shared_zones(a,b):
    """Only common graph ports may have a short shared fan-out/fan-in stem."""
    points=[]
    for end in (0,-1):
        for other in (0,-1):
            key='from' if end==0 else 'to';other_key='from' if other==0 else 'to'
            if a.get(key) is not None and a.get(key)==b.get(other_key) and tuple(a['points'][end])==tuple(b['points'][other]):points.append(a['points'][end])
    points.extend(p for p in a.get('junctions',[]) if p in b.get('junctions',[]))
    return [(x-24,y-24,48,48) for x,y in points]


def wire_obstacles(prior,current,pad=7):
    reserved=[]
    for old in prior:
        zones=shared_zones(old,current)
        for a,b in zip(old['points'],old['points'][1:]):
            pieces=[(min(a[0],b[0])-pad,min(a[1],b[1])-pad,abs(a[0]-b[0])+2*pad,abs(a[1]-b[1])+2*pad)]
            for zone in zones:pieces=[piece for r in pieces for piece in subtract_rect(r,zone)]
            reserved.extend(pieces)
    return reserved


def wire_conflicts(routes):
    """Crossing, T-contact or overlap outside an intentional common-port stem."""
    pairs=[]
    for i,a in enumerate(routes):
        for j,b in enumerate(routes[:i]):
            # A tiny positive width detects endpoint contacts as well as crossings.
            if not clear(a['points'],wire_obstacles([b],a,pad=.05)):
                pairs.append((b['edge'],a['edge']))
    return pairs


def route_network(plans,canvas):
    """Route short wires first; reserve every accepted wire for subsequent ones.

    Retry with conflicting wires first to undo greedy traps. Never relax the
    node/text obstacles. A fallback route is reported, not silently certified.
    """
    priorities={};best=None;best_score=None
    for attempt in range(3):
        order=sorted(plans,key=lambda p:(-priorities.get(p['edge'],0),abs(p['p'][0]-p['q'][0])+abs(p['p'][1]-p['q'][1]),p['edge'] if attempt%2==0 else -p['edge']))
        result=[]
        for p in order:
            current={'edge':p['edge'],'from':p['from'],'to':p['to'],'points':[p['p'],p['q']],'junctions':p.get('junctions',[])}
            reservations=wire_obstacles(result,current)
            own={tuple(p['p']),tuple(p['q']),*(tuple(j) for j in p.get('junctions',[]))}
            # Don't paint an earlier wire across a later wire's fixed endpoint.
            for future in plans:
                if future['edge']==p['edge']:continue
                for terminal in (future['p'],future['q']):
                    if tuple(terminal) not in own:reservations.append((terminal[0]-6,terminal[1]-6,12,12))
            def middle_path(obstacles):
                anchors=[p['ps']]+p.get('anchors',[])+[p['qs']]
                pieces=[]
                for a,b in zip(anchors,anchors[1:]):
                    segment=route(a,b,obstacles,canvas,p.get('hint') if len(anchors)==2 else None)
                    pieces.extend(segment)
                return simplify(pieces)
            try:
                # Fixed port stubs also must clear previous wires.
                if not clear([p['p'],p['ps']],reservations) or not clear([p['qs'],p['q']],reservations):raise ValueError('port stub touches another wire')
                middle=middle_path(p['obstacles']+reservations)
            except ValueError:
                middle=middle_path(p['obstacles'])
            result.append({'edge':p['edge'],'from':p['from'],'to':p['to'],'junctions':p.get('junctions',[]),'points':simplify([p['p']]+middle+[p['q']])})
        conflicts=wire_conflicts(result)
        length=sum(abs(a[0]-b[0])+abs(a[1]-b[1]) for r in result for a,b in zip(r['points'],r['points'][1:]))
        score=(len(conflicts),length)
        if best_score is None or score<best_score:best=result;best_score=score
        if not conflicts:break
        priorities={}
        for a,b in conflicts:
            priorities[a]=priorities.get(a,0)+1;priorities[b]=priorities.get(b,0)+1
    return sorted(best,key=lambda r:r['edge']),wire_conflicts(best)


def simplify(points):
    result=[]
    for p in points:
        p=tuple(p)
        if result and p==result[-1]: continue
        if len(result)>1 and ((result[-2][0]==result[-1][0]==p[0]) or (result[-2][1]==result[-1][1]==p[1])):
            result[-1]=p
        else: result.append(p)
    return result


def route(start, end, obstacles, canvas, hint=None):
    """Find an orthogonal route; fail rather than draw through labels."""
    start,end=tuple(start),tuple(end)
    def good(p):
        return all(0<=x<=canvas[0] and 0<=y<=canvas[1] for x,y in p) and clear(p,obstacles)
    if hint:
        candidate=[start]+[tuple(p) for p in hint]+[end]
        if all(a[0]==b[0] or a[1]==b[1] for a,b in zip(candidate,candidate[1:])) and good(candidate):return simplify(candidate)
    candidates=[]
    for p in ([start,(end[0],start[1]),end],[start,(start[0],end[1]),end]):
        if good(p):candidates.append(simplify(p))
    xs={start[0],end[0],(start[0]+end[0])/2,12,canvas[0]-12}
    ys={start[1],end[1],(start[1]+end[1])/2,12,canvas[1]-12}
    for x,y,w,h in obstacles:
        xs.update([x-2,x+w+2]);ys.update([y-2,y+h+2])
    xs=sorted(x for x in xs if 0<=x<=canvas[0]);ys=sorted(y for y in ys if 0<=y<=canvas[1])
    for x in xs:
        p=[start,(x,start[1]),(x,end[1]),end]
        if good(p): candidates.append(simplify(p))
    for y in ys:
        p=[start,(start[0],y),(end[0],y),end]
        if good(p): candidates.append(simplify(p))
    if candidates:
        return min(candidates,key=lambda p:sum(abs(a[0]-b[0])+abs(a[1]-b[1]) for a,b in zip(p,p[1:]))+24*len(p))
    # Sparse visibility grid: connect adjacent unobstructed x/y coordinates.
    ix,iy=xs.index(start[0]),ys.index(start[1]);goal=(xs.index(end[0]),ys.index(end[1]))
    queue=[(0,0,ix,iy,-1)];best={(ix,iy,-1):0};parents={};seen_clear={}
    while queue:
        _,cost,i,j,d=heapq.heappop(queue);state=(i,j,d)
        if cost>best.get(state,math.inf):continue
        if (i,j)==goal:
            path=[]
            while state in parents:
                path.append((xs[state[0]],ys[state[1]]));state=parents[state]
            return simplify([start]+list(reversed(path)))
        for ni,nj,nd in ((i-1,j,0),(i+1,j,0),(i,j-1,1),(i,j+1,1)):
            if not(0<=ni<len(xs) and 0<=nj<len(ys)):continue
            a,b=(xs[i],ys[j]),(xs[ni],ys[nj]);key=tuple(sorted((a,b)))
            if key not in seen_clear:seen_clear[key]=clear([a,b],obstacles)
            if not seen_clear[key]:continue
            newcost=cost+abs(a[0]-b[0])+abs(a[1]-b[1])+(24 if d not in (-1,nd) else 0)
            nxt=(ni,nj,nd)
            if newcost<best.get(nxt,math.inf):
                best[nxt]=newcost;parents[nxt]=state
                heuristic=abs(b[0]-end[0])+abs(b[1]-end[1])
                heapq.heappush(queue,(newcost+heuristic,newcost,ni,nj,nd))
    raise ValueError(f'No collision-free route: {start} -> {end}; spread the connected nodes')


def port(node, side, fraction=.5, stub=14):
    x,y,w,h=node['box']
    p={'top':(x+w*fraction,y),'bottom':(x+w*fraction,y+h),'left':(x,y+h*fraction),'right':(x+w,y+h*fraction)}[side]
    dx,dy={'top':(0,-stub),'bottom':(0,stub),'left':(-stub,0),'right':(stub,0)}[side]
    return p,(p[0]+dx,p[1]+dy)


def measured_rect(text,renderer,ax):
    b=text.get_window_extent(renderer)
    a,c=ax.transData.inverted().transform([[b.x0,b.y0],[b.x1,b.y1]])
    return [min(a[0],c[0]),min(a[1],c[1]),abs(c[0]-a[0]),abs(c[1]-a[1])]


def palette(name):
    c=json.loads(PALETTES.read_text())[name].copy()
    c.update(memory=c['fourth'],modulation=c['third'])
    for role in ('local','global','third','fourth','memory','modulation'):
        rgb=tuple(int(c[role][i:i+2],16) for i in (1,3,5))
        c[role+'_soft']='#'+''.join(f'{round(v*.08+255*.92):02x}' for v in rgb)
    c.update(neutral=c['line'],neutral_soft=c['base'])
    return c


def render(scene, out, palette_name='jade-violet'):
    c=palette(palette_name);out=Path(out);out.parent.mkdir(parents=True,exist_ok=True)
    w,h=scene['canvas'];fig=plt.figure(figsize=(w/100,h/100),dpi=100,facecolor=c['canvas'])
    ax=fig.add_axes([0,0,1,1]);ax.set_xlim(0,w);ax.set_ylim(h,0);ax.axis('off')
    texts=[];nodes={n['id']:n for n in scene['nodes']}
    def text(x,y,s,size=22,color='text',ha='center',bold=False,owner=None):
        t=ax.text(x,y,s,fontsize=size*.72,fontfamily='Noto Sans CJK JP',color=c.get(color,color),ha=ha,va='center',fontweight='bold' if bold else 'normal',linespacing=1.35,zorder=5)
        texts.append((t,owner))
    for f in scene.get('frames',[]):
        x,y,bw,bh=f['box'];col=c[f.get('role','frame')]
        fill=to_rgba(c[f['fill']],f.get('fill_alpha',1)) if f.get('fill') else col if f.get('filled') else 'none'
        ax.add_patch(FancyBboxPatch((x,y),bw,bh,boxstyle=f"round,pad=0,rounding_size={f.get('radius',10)}",facecolor=fill,edgecolor=col,lw=1,zorder=0))
    for item in scene.get('lines',[]):
        ax.plot(*zip(*item['points']),color=c[item.get('role','frame')],lw=item.get('width',1),linestyle=(0,(4,4)) if item.get('dashed') else '-',zorder=0)
    for n in nodes.values():
        x,y,nw,nh=n['box'];role=n.get('role','neutral');size=n.get('fontsize',22)
        fill=c[role] if n.get('emphasis') else c[role+'_soft']
        if n.get('shape')=='circle':
            ax.add_patch(Circle((x+nw/2,y+nh/2),nw/2,facecolor=fill,edgecolor=c[role],lw=1.1,zorder=2))
        else:
            ax.add_patch(FancyBboxPatch((x,y),nw,nh,boxstyle='round,pad=0,rounding_size=7',facecolor=fill,edgecolor=c[role],lw=1.1,zorder=2,linestyle=(0,(4,3)) if palette_name=='monochrome' and role=='global' else '-'))
        text(x+nw/2,y+nh/2-(13 if n.get('sublabel') else 0),n['label'],size,'#ffffff' if n.get('emphasis') else role if role!='neutral' else 'text',bold=n.get('bold',False),owner=n['id'])
        if n.get('sublabel'):text(x+nw/2,y+nh/2+18,n['sublabel'],n.get('subsize',17),'#ffffff' if n.get('emphasis') else 'muted',owner=n['id'])
    for t in scene.get('captions',[]):text(t['x'],t['y'],t['text'],t.get('size',22),t.get('color','text'),t.get('ha','center'),t.get('bold',False))
    fig.canvas.draw();renderer=fig.canvas.get_renderer()
    labels=[{'text':t.get_text(),'owner':owner,'box':measured_rect(t,renderer,ax)} for t,owner in texts]
    problems=[]
    for l in labels:
        x,y,lw,lh=l['box']
        if x<0 or y<0 or x+lw>w or y+lh>h:problems.append('page overflow: '+l['text'])
        if l['owner']:
            nx,ny,nw,nh=nodes[l['owner']]['box']
            if x<nx+3 or x+lw>nx+nw-3 or y<ny+2 or y+lh>ny+nh-2:problems.append('node label overflow: '+l['text'])
    for i,a in enumerate(labels):
        for b in labels[i+1:]:
            x,y,bw,bh=a['box'];u,v,cw,ch=b['box']
            if min(x+bw,u+cw)-max(x,u)>1 and min(y+bh,v+ch)-max(y,v)>1:problems.append('text overlap: '+a['text']+' / '+b['text'])
    if problems:raise ValueError('\n'.join(problems))
    text_obstacles=[inflate(l['box'],7) for l in labels]
    node_obstacles=[inflate(n['box'],7) for n in nodes.values()]
    plans=[]
    for i,e in enumerate(scene['edges']):
        a,b=nodes[e['from']],nodes[e['to']]
        ac=(a['box'][0]+a['box'][2]/2,a['box'][1]+a['box'][3]/2);bc=(b['box'][0]+b['box'][2]/2,b['box'][1]+b['box'][3]/2)
        if abs(bc[1]-ac[1])>=abs(bc[0]-ac[0]):default=('bottom','top') if bc[1]>ac[1] else ('top','bottom')
        else:default=('right','left') if bc[0]>ac[0] else ('left','right')
        p,ps=port(a,e.get('from_side',default[0]),e.get('from_fraction',.5));q,qs=port(b,e.get('to_side',default[1]),e.get('to_fraction',.5))
        plans.append({'edge':i,'from':a['id'],'to':b['id'],'p':p,'ps':ps,'q':q,'qs':qs,'obstacles':text_obstacles+node_obstacles,'hint':e.get('waypoints')})
    routes,conflicts=route_network(plans,scene['canvas'])
    if conflicts:
        Path(str(out)+'.routing-failure.json').write_text(json.dumps({'unresolved_wire_pairs':conflicts,'routes':routes},indent=2)+'\n')
        raise ValueError(f'{len(conflicts)} unresolved wire crossings/overlaps; see {out}.routing-failure.json; spread connected nodes or adjust ports')
    for r in routes:
        i=r['edge'];e=scene['edges'][i];a,b=nodes[e['from']],nodes[e['to']];points=r['points']
        if not clear(points,text_obstacles):raise ValueError(f'Edge {i} overlaps text at its port; adjust port fraction')
        other=[inflate(n['box'],4) for n in nodes.values() if n['id'] not in (a['id'],b['id'])]
        if not clear(points,other):raise ValueError(f'Edge {i} crosses another node')
        col=c[e.get('role','muted')];dash=e.get('dashed',False) or (palette_name=='monochrome' and e.get('role')=='global')
        weight=e.get('width',1.2)
        ax.plot(*zip(*points),color=col,lw=weight,linestyle=(0,(4,4)) if dash else '-',zorder=1)
        ax.add_patch(FancyArrowPatch(points[-2],points[-1],arrowstyle='-|>',mutation_scale=11,color=col,lw=weight,zorder=3,shrinkA=0,shrinkB=0))
    with plt.rc_context({'svg.fonttype':'none'}):
        for ext in ('png','svg'):
            fig.savefig(str(out)+'.'+ext,dpi=160,metadata={'Date':None} if ext=='svg' else None)
    with plt.rc_context({'svg.fonttype':'path'}):fig.savefig(str(out)+'-outlined.svg',metadata={'Date':None})
    plt.close(fig)
    with Image.open(str(out)+'.png') as im:
        im.thumbnail((1500,1500));im.save(str(out)+'-preview.png')
    Path(str(out)+'.geometry.json').write_text(json.dumps({'labels':labels,'routes':routes},ensure_ascii=False,indent=2)+'\n')
    report={'palette':palette_name,'nodes':len(nodes),'edges':len(routes),'arrow_text_collisions':0,'arrow_node_collisions':0,'text_overlaps':0,'wire_crossings_or_overlaps':len(conflicts),'status':'pass'}
    Path(str(out)+'.validation.json').write_text(json.dumps(report,indent=2)+'\n')
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('scene');parser.add_argument('--out',required=True);parser.add_argument('--palette',default='jade-violet')
    args=parser.parse_args();print(json.dumps(render(json.loads(Path(args.scene).read_text()),args.out,args.palette)))

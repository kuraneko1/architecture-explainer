"""Exercise visible routing failure modes, not just JSON shape."""
import json
import tempfile
from pathlib import Path
from diagram import render, route, clear, route_network, wire_conflicts

with tempfile.TemporaryDirectory(prefix='architecture-routing-') as folder:
    stem=Path(folder)/'obstacle'
    scene={'canvas':[800,360], 'nodes':[
        {'id':'a','box':[40,140,160,70],'label':'Input','role':'memory'},
        {'id':'b','box':[600,140,160,70],'label':'Output','role':'global','emphasis':True}],
        'captions':[{'x':400,'y':175,'text':'文字の障害物 / label','size':24}],
        'edges':[{'from':'a','to':'b','from_side':'right','to_side':'left','role':'modulation','width':1.7}]}
    reports=[]
    for name in ('jade-violet','ocean','amber-indigo','accessible','monochrome'):
        out=Path(str(stem)+'-'+name);reports.append(render(scene,out,name))
        geometry=json.loads(Path(str(out)+'.geometry.json').read_text())
        if name=='jade-violet':reference=geometry
        else:assert geometry==reference,'Palette change moved labels or routes'
    points=reference['routes'][0]['points']
    assert points[0]==[200,175] and points[-1]==[600,175],'Ports changed'
    assert any(y!=175 for x,y in points),'Arrow did not detour around measured text'
    try:route((20,100),(180,100),[(80,0,40,200)],[200,200])
    except ValueError:pass
    else:raise AssertionError('Unroutable path did not fail')
    bad=json.loads(json.dumps(scene));bad['nodes'][0]['label']='too wide '*25
    try:render(bad,Path(folder)/'overflow')
    except ValueError:pass
    else:raise AssertionError('Label overflow was not rejected')
    def plan(index,a,b):return {'edge':index,'from':str(a),'to':str(b),'p':a,'ps':a,'q':b,'qs':b,'obstacles':[]}
    crossed=[plan(0,(50,180),(550,180)),plan(1,(300,40),(300,340))]
    overlap=[plan(0,(50,120),(450,120)),plan(1,(250,120),(650,120))]
    fanout=[plan(0,(80,80),(500,80)),plan(1,(80,80),(500,270))]
    for name,plans in [('crossing',crossed),('collinear overlap',overlap),('shared source',fanout)]:
        routes,conflicts=route_network(plans,[720,400])
        assert not conflicts,(name,conflicts)
        for r in routes:
            assert tuple(r['points'][0])==plans[r['edge']]['p'] and tuple(r['points'][-1])==plans[r['edge']]['q'],name
    # Endpoint-on-segment contact must be detected even when perpendicular
    # intersections would miss it; distant shared-source crossings stay errors.
    bad=[{'edge':0,'points':[(50,100),(500,100)]},{'edge':1,'points':[(250,100),(250,300)]}]
    assert wire_conflicts(bad),'T-contact was not detected'
    far=[{'edge':0,'from':'shared','to':'a','points':[(80,80),(500,80),(500,300)]},
         {'edge':1,'from':'shared','to':'b','points':[(80,80),(80,300),(600,300)]}]
    assert wire_conflicts(far),'Sharing a source incorrectly exempted a distant crossing'
    print(json.dumps({'measured_label_detour':'pass','fixed_ports':'pass','five_palette_geometry_invariance':'pass','unroutable_fails':'pass','overflow_fails':'pass','wire_crossing_detour':'pass','wire_overlap_detour':'pass','shared_source':'pass','T_contact_detection':'pass'}))

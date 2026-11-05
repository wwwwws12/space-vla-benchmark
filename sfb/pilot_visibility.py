"""Conservative DEM silhouette checks for development layout, never pixel truth."""
import math
import numpy as np


def top_clearance(g, xy, height, angle, distance, width=3.0, samples=5):
    """Maximum terrain obstruction on each ray to a grid on the target roof.

    Positive means a DEM sample rises above the ray. Covers bounding roof,
    including cylinder/sphere empty corners, to favor conservative hiding.
    No inference, distance-based Yes answers, or target/camera scale changes.
    """
    a=math.radians(angle);x,y=xy
    cx,cy=x-distance*math.cos(a),y-distance*math.sin(a);cz=g.z(cx,cy)+4
    u=np.linspace(-width/2,width/2,samples);xx,yy=np.meshgrid(u,u)
    tx=x+xx.ravel();ty=y+yy.ravel();tz=g.z(x,y)+height
    t=np.linspace(0,1,max(3,math.ceil(distance/.5)+1))[1:-1]
    xs=cx+(tx[:,None]-cx)*t;ys=cy+(ty[:,None]-cy)*t
    ray=cz+(tz-cz)*t
    return np.max(g.z(xs,ys)-ray,axis=1)


def screen_candidates(g):
    """Single bounded search over this tile: 8m grid and 30-degree headings."""
    coords=np.arange(-216,217,8);xx,yy=np.meshgrid(coords,coords)
    x,y=xx.ravel(),yy.ravel();z=g.z(x,y);t=np.linspace(0,1,121)[1:-1]
    coarse=[]
    for angle in range(0,360,30):
        a=math.radians(angle);cx=x-60*math.cos(a);cy=y-60*math.sin(a)
        cz=g.z(cx,cy)+4
        obstruction=np.max(g.z(cx[:,None]+(x-cx)[:,None]*t,cy[:,None]+(y-cy)[:,None]*t)-(cz[:,None]+(z+2.8-cz)[:,None]*t),axis=1)
        for i in np.flatnonzero(obstruction>=.8):
            coarse.append((float(obstruction[i]),[float(x[i]),float(y[i])],angle))
    # Strong ridge margin first; all ranking is terrain geometry, before RGB.
    coarse.sort(key=lambda v:(-v[0],v[1],v[2]))
    accepted=[]
    for strength,xy,angle in coarse:
        if any(math.dist(xy,v['xy'])<12 and angle==v['angle_deg'] for v in accepted):continue
        margins=[];good=True
        for distance in (60,75,90,110,130,145):
            c=top_clearance(g,xy,2.8,angle,distance,width=3,samples=5)
            margins.append(float(c.min()))
            if c.min()<.25:good=False;break
        if not good:continue
        # Target center should naturally become exposed before the success region.
        near=top_clearance(g,xy,1.4,angle,35,width=1,samples=3)
        if near.max()>=0:continue
        accepted.append(dict(xy=xy,angle_deg=angle,minimum_far_roof_obstruction_m=min(margins),
            far_distances_m=[60,75,90,110,130,145],near_center_max_obstruction_m=float(near.max()),
            roof_size_m=[3,3,2.8],source='bounded DEM only; no model or Oracle-score selection'))
    return dict(grid_step_m=8,grid_bounds_m=[-216,216],headings=list(range(0,360,30)),
        coarse_candidates=len(coarse),candidates=accepted)

"""v3 terrain free space and target distances, independent of Isaac."""
import math
from sfb.scene import terrain_height_m


def segment_free(scene,x0,y0,x1,y1):
    terrain=scene.config["terrain"]
    limit_x,limit_y=terrain["width_m"]/2-6,terrain["depth_m"]/2-6
    if any(abs(x)>limit_x or abs(y)>limit_y for x,y in ((x0,y0),(x1,y1))):
        return False
    dx,dy=x1-x0,y1-y0
    length2=dx*dx+dy*dy
    for target in scene.targets:
        if target.get("height",0)<=3: continue
        cx,cy=target["xy"]
        fraction=max(0,min(1,((cx-x0)*dx+(cy-y0)*dy)/length2)) if length2 else 0
        if math.hypot(x0+fraction*dx-cx,y0+fraction*dy-cy)<=target["radius"]+1:
            return False
    return True


def target_pose(scene,target):
    x,y=target["xy"]
    return [x,y,terrain_height_m(scene,x,y)+scene.config["flight_height_m"]]


def target_distance(scene,pose,target):
    point=target_pose(scene,target)
    return math.sqrt(sum((a-b)**2 for a,b in zip((pose.x,pose.y,pose.z),point)))

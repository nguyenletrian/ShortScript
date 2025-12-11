import maya.cmds as cmds
import maya.api.OpenMaya as om
from functools import partial

#Boolean
def get_mesh_fn(mesh):
    sel = om.MSelectionList()
    sel.add(mesh)
    dag = sel.getDagPath(0)
    return om.MFnMesh(dag)

def get_face_centroids(mesh):
    fn = get_mesh_fn(mesh)
    centroids = {}
    for i in range(fn.numPolygons):
        points = fn.getPolygonVertices(i)
        verts = [om.MVector(fn.getPoint(v, om.MSpace.kWorld)) for v in points]
        c = sum(verts, om.MVector()) / len(verts)
        centroids[i] = c
    return centroids

def FindMatchingFaces(source,target, tolerance=0.001):
    centA = get_face_centroids(source)
    centB = get_face_centroids(target)
    matches = []
    for fA, cA in centA.items():
        for fB, cB in centB.items():
            if (cA - cB).length() < tolerance:
                matches.append(fB)
    return matches

def DeleteBoolean(source,target):
    sourceDup = cmds.duplicate(source, name=source + "_dup")[0]
    targetDup = cmds.duplicate(target, name=target + "_dup")[0]
    newMesh = cmds.polyBoolOp(sourceDup,targetDup, op=3)[0]
    cmds.delete(newMesh, ch=True)
    faceIDs = FindMatchingFaces(newMesh,target)
    cmds.delete([f"{target}.f[%a]" % a for a in faceIDs],newMesh)
    
def DeleteBooleanRun(*arr):
    objs = cmds.ls(selection=True)
    if len(objs)>=2:
        source = objs[0]
        targets = objs[1:]
        for target in targets:
            DeleteBoolean(source,target)   

#Skrink wrap
def GetPolygonData(obj):
    data = {
        "vtxs":{},
        "faces":{}
    }
    
    vtxs = cmds.ls(obj+'.vtx[*]',flatten=True)
    for vtx in vtxs:
        data["vtxs"][vtx] = cmds.xform(vtx, q=True, ws=True, t=True)
    faces = cmds.ls(obj+'.f[*]',flatten=True)
    for face in faces:
        data["faces"][face] = cmds.polyInfo(face, faceNormals=True)
    return(data)
    
def CreateDeformer(source,target,reverse):
    sw = cmds.deformer(target, type='shrinkWrap')[0]
    sourceShape = cmds.listRelatives(source, shapes=True, noIntermediate=True)[0]
    cmds.connectAttr(sourceShape + '.worldMesh[0]', sw + '.targetGeom', force=True)
    return(sw)

def GetNewVertexPos(target,source):
    pass

def DeleteIntersectFaces(source,target,reverse):
    orgData = GetPolygonData(target)
    deform = CreateDeformer(source,target,reverse)
    if reverse:
        cmds.setAttr(deform+".reverse",1)
    newData = GetPolygonData(target)
    cmds.setAttr(deform+".envelope",0)
    deleteFaces = []
    for face in newData["faces"]:
        vtxs = cmds.ls(cmds.polyListComponentConversion(face, tv=True),flatten=True)
        delState = True
        for vtx in vtxs:
            vtxNewPos = newData["vtxs"][vtx]
            vtxOldPos = orgData["vtxs"][vtx]
            if vtxNewPos == vtxOldPos:
                delState = False
                break
        if delState == True:
            deleteFaces.append(face)
    cmds.delete(deleteFaces)
    cmds.delete(deform)

def DeleteIntersect(reverse,*arr):
    objs = cmds.ls(selection=True)
    if len(objs)>=2:
        source = objs[0]
        targets = objs[1:]
        for target in targets:
            DeleteIntersectFaces(source,target,reverse)
            
#UI
if cmds.window("DeleteIntersect", exists=True):
    cmds.deleteUI("DeleteIntersect")
window = cmds.window("DeleteIntersect", title="Delete Intersect Faces")
cmds.columnLayout(adjustableColumn=True)
cmds.rowColumnLayout(nc=1, width=200,height=150)
cmds.button(label="Delete Normal", command=partial(DeleteIntersect,False),width=198,height=50)
cmds.button(label="Delete Inverse", command=partial(DeleteIntersect,True),height=50)
cmds.button(label="Delete Boolean", command=DeleteBooleanRun,height=50)
cmds.setParent("..")
cmds.showWindow(window)

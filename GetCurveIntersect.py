import maya.cmds as cmds
import maya.api.OpenMaya as om

def filterValence2Vertices(mesh, vertices):
    sel = om.MSelectionList()
    sel.add(mesh)
    dag = sel.getDagPath(0)

    vtxIter = om.MItMeshVertex(dag)

    # Chuyển sang set index cho nhanh
    targetIndices = {
        int(v.split("[")[-1].split("]")[0]) for v in vertices
    }

    removeVerts = []

    while not vtxIter.isDone():
        idx = vtxIter.index()

        if idx in targetIndices:
            edges = vtxIter.getConnectedEdges()
            if len(edges) == 2:
                removeVerts.append(f"{mesh}.vtx[{idx}]")

        vtxIter.next()

    return removeVerts


def getVertexPositions(mesh, tol=0.01):#1e-6
    sel = om.MSelectionList()
    sel.add(mesh)
    dag = sel.getDagPath(0)
    fn = om.MFnMesh(dag)
    positions = set()
    for p in fn.getPoints(om.MSpace.kWorld):

        positions.add((
            round(p.x / tol) * tol,
            round(p.y / tol) * tol,
            round(p.z / tol) * tol
        ))
    return positions


def getNewVertices(mesh, oldPositions, tol=0.01):
    sel = om.MSelectionList()
    sel.add(mesh)
    dag = sel.getDagPath(0)
    fn = om.MFnMesh(dag)
    newVerts = []
    for i, p in enumerate(fn.getPoints(om.MSpace.kWorld)):
        pos = (
            round(p.x / tol) * tol,
            round(p.y / tol) * tol,
            round(p.z / tol) * tol
        )
        if pos not in oldPositions:
            newVerts.append(f"{mesh}.vtx[{i}]")
    return newVerts

def booleanSplitEdges_removeNewVertices():
    objs = cmds.ls(selection=True)
    meshA = objs[0]
    meshBs =  objs[1:]
    for meshB in meshBs:
        # 1️⃣ Lưu vertex cũ
        oldPositions = getVertexPositions(meshA)
    
        # 2️⃣ Boolean Split Edges
        result = cmds.polyCBoolOp(
            meshA,
            meshB,
            op=8,
            ch=True
        )[0]
        allVertex =  cmds.ls(result+".vtx[*]",flatten=True)
        newVerts = getNewVertices(result, oldPositions)
        removeVerts = filterValence2Vertices(result, newVerts)
        noDelete = list(set(newVerts) - set(removeVerts))
        deleteVertex = list(set(allVertex) - set(noDelete))   
        cmds.delete(removeVerts)
        cmds.delete(result, constructionHistory=True)
booleanSplitEdges_removeNewVertices()
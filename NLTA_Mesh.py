import maya.cmds as cmds
import importlib
import pymel.core as pm
import math
import maya.api.OpenMaya as om
import maya.api.OpenMayaAnim as oma

import NLTA_General, NLTA_OpenMaya
for module in [NLTA_General, NLTA_OpenMaya]:
    try:
        importlib.reload(module)
    except:
        reload(module)

cmds.selectPref(trackSelectionOrder=True)

import maya.api.OpenMaya as om

def ShowQuardraw(*arr):
    pm.mel.eval('lockNode -l off  -lockUnpublished off initialShadingGroup;')

def GetVertexsSelected(*arr):
    sel = cmds.ls(sl=True)    
    if not sel:
        return []    
    verts = cmds.polyListComponentConversion(sel, toVertex=True)
    verts = cmds.ls(verts, fl=True)    
    return verts

def GetMesh(*arr):
    selection = cmds.ls(sl=True, fl=True)
    return(list(set([s.split(".")[0] for s in selection])))

def EdgeDirection(mesh, edgeIndex):
    mesh_path = NLTA_OpenMaya.GetDagPath(mesh)
    edge_it = om.MItMeshEdge(mesh_path)
    edge_it.setIndex(edgeIndex)
    p1 = edge_it.point(0, om.MSpace.kWorld)
    p2 = edge_it.point(1, om.MSpace.kWorld)
    v = om.MVector(p2 - p1)
    return v.normal()

def CheckEdgeBorder(mesh, edgeId):
    dag = NLTA_OpenMaya.GetDagPath(mesh)
    it = om.MItMeshEdge(dag)
    it.setIndex(edgeId)
    return(it.onBoundary())

def JointPos(j):
    return om.MVector(cmds.xform(j, q=True, ws=True, t=True))

def GetID(component):
    if isinstance(component, (int, float)):
        return(component)
    else:
        return(
            int(component.split("[")[-1].replace("]", ""))
        )

def GetJointAxis(joint):
    m = cmds.xform(joint, q=True, ws=True, m=True)
    axis = om.MVector(m[0], m[1], m[2])
    return axis.normal()

def GetClosestVertex(mesh, joint):
    mesh_path = NLTA_OpenMaya.GetDagPath(mesh)
    mesh_fn = om.MFnMesh(mesh_path)
    JointPos = cmds.xform(joint, q=True, ws=True, t=True)
    point = om.MPoint(JointPos)
    closest_point, face_id = mesh_fn.getClosestPoint(point, om.MSpace.kWorld)
    vertices = mesh_fn.getPoints(om.MSpace.kWorld)
    min_dist = float("inf")
    closest_index = -1
    for i, v in enumerate(vertices):
        dist = (v - closest_point).length()
        if dist < min_dist:
            min_dist = dist
            closest_index = i
    return closest_index

"""
def GetEdgeLoop(mesh, start_edge):
    returnData = []
    edges = cmds.polySelect(mesh, edgeLoop=GetID(start_edge), noSelection=True)
    for edge in edges:
        returnData.append(
            "{}.e[{}]".format(mesh, edge)
        )
    return(returnData)
"""
def GetEdgeLoop(startEdge,*arr):
    mesh = startEdge.split(".")[0]
    edgeId = GetID(startEdge) if isinstance(startEdge, str) else startEdge
    sel = om.MSelectionList()
    sel.add(mesh)
    dag = sel.getDagPath(0)
    edgeIt = om.MItMeshEdge(dag)
    vertIt = om.MItMeshVertex(dag)
    visited = set()
    def Walk(edgeId, fromVertex):
        result = []
        while True:
            if edgeId in visited:
                break
            visited.add(edgeId)
            result.append(edgeId)
            edgeIt.setIndex(edgeId)
            if edgeIt.vertexId(0) == fromVertex:
                v = edgeIt.vertexId(1)
            else:
                v = edgeIt.vertexId(0)
            vertIt.setIndex(v)
            connectedEdges = vertIt.getConnectedEdges()
            if vertIt.onBoundary():
                candidates = []
                for e in connectedEdges:
                    if e == edgeId:
                        continue
                    edgeIt.setIndex(e)
                    if edgeIt.onBoundary():
                        candidates.append(e)
                if len(candidates) != 1:
                    break
                nextEdge = candidates[0]
            else:
                if len(connectedEdges) != 4:
                    break
                nextEdge = None
                for e in connectedEdges:
                    if e == edgeId:
                        continue
                    edgeIt.setIndex(e)
                    if edgeIt.onBoundary():
                        continue
                    common = set(edgeIt.getConnectedFaces())
                    edgeIt.setIndex(edgeId)
                    if len(common & set(edgeIt.getConnectedFaces())) == 0:
                        nextEdge = e
                        break
                if nextEdge is None:
                    break
            edgeIt.setIndex(nextEdge)
            if edgeIt.vertexId(0) == v:
                fromVertex = v
            else:
                fromVertex = v
            edgeId = nextEdge
        return result
    edgeIt.setIndex(edgeId)
    v0 = edgeIt.vertexId(0)
    v1 = edgeIt.vertexId(1)
    loop = []
    loop.extend(reversed(Walk(edgeId, v0)))
    visited.discard(edgeId)
    loop.extend(Walk(edgeId, v1))
    final = []
    seen = set()
    for e in loop:
        if e not in seen:
            seen.add(e)
            final.append("{}.e[{}]".format(mesh, e))
    return final

def GetEdgeRing(mesh, start_edge):
    returnData = []
    edges = cmds.polySelect(mesh, edgeRing=GetID(start_edge), noSelection=True)
    for edge in edges:
        returnData.append("{}.e[{}]".format(mesh, edge))
    return(returnData)

def VertexFromEdges(mesh, edges):
    dag = NLTA_OpenMaya.GetDagPath(mesh)
    it = om.MItMeshEdge(dag)
    verts = set()
    for edge in edges:
        eid = GetID(edge)
        it.setIndex(eid)

        v1 = it.vertexId(0)
        v2 = it.vertexId(1)

        verts.add(v1)
        verts.add(v2)
    return ["{}.vtx[{}]".format(mesh, v) for v in verts]

def GetConnectedEdges(mesh,vertex_index):
    mesh_path = NLTA_OpenMaya.GetDagPath(mesh)
    vert_it = om.MItMeshVertex(mesh_path)
    vert_it.setIndex(vertex_index)
    return vert_it.getConnectedEdges()

def GetJointEdge(mesh, joint, vertex_index):
    joint_axis = GetJointAxis(joint)
    edges = GetConnectedEdges(mesh, vertex_index)
    best_edge = None
    best_dot = -1
    for e in edges:
        dir_vec = EdgeDirection(mesh, e)
        dot = abs(dir_vec * joint_axis)
        if dot > best_dot:
            best_dot = dot
            best_edge = e
    return best_edge

def GetJointEdgeLoop(mesh, joint,vtxIndex):
    best_edge = GetJointEdge(mesh, joint, vtxIndex)
    if best_edge is None:
        cmds.warning("No edge found")
        return
    return(GetEdgeLoop(mesh+".e[{}]".format(best_edge)))

def GetPerpendicularEdge(mesh, joint, vertex_index):
    joint_axis = GetJointAxis(joint)
    edges = GetConnectedEdges(mesh, vertex_index)
    best_edge = None
    best_dot = 999
    for e in edges:
        dir_vec = EdgeDirection(mesh, e)
        dot = abs(dir_vec * joint_axis)
        if dot < best_dot:
            best_dot = dot
            best_edge = e
    return best_edge

def GetPerpendicularEdgeLoop(mesh, joint,vtxIndex):
    best_edge = GetPerpendicularEdge(mesh, joint, vtxIndex)
    if best_edge is None:
        cmds.warning("No edge found")
        return
    return(GetEdgeLoop(mesh+".e[{}]".format(best_edge)))

def GetTwoClosestJoints(targetJoint, joints):
    distances = []
    for j in joints:
        if j == targetJoint:
            continue
        dist = NLTA_General.GetDistance(targetJoint,j)
        distances.append((j, dist))
    distances.sort(key=lambda x: x[1])
    return distances[:2]

def GetClosestJoint(targetJoint, joints):
    distances = []
    for j in joints:
        if j == targetJoint:
            continue
        dist = NLTA_General.GetDistance(targetJoint,j)
        distances.append((j, dist))
    distances.sort(key=lambda x: x[1])
    return distances[:1]

def SelectVerticesWithinRadius(mesh,joint,verts,radius):
    p0 = JointPos(joint)
    result = []
    for v in verts:
        pos = om.MVector(cmds.pointPosition(v, w=True))
        d = (pos - p0).length()
        if d <= radius:
            result.append(v)
    return(result)
    
def SelectLoopRegion(mesh, joint,joints,verts):
    closest = GetTwoClosestJoints(joint, joints)
    d1 = closest[0][1]
    d2 = closest[1][1]
    radius = min(d1, d2) * 0.7
    verts = SelectVerticesWithinRadius(mesh, joint,verts,radius)
    return(verts)

def EdgesBetween(mesh, edgeSource, edgeTarget):
    id1 = GetID(edgeSource)
    id2 = GetID(edgeTarget)
    edges = cmds.polySelect(
        mesh,
        edgeRingPath=(id1, id2),
        noSelection=True
    )
    if edges is None:
        edges = cmds.polySelect(
            mesh,
            edgeLoopPath=(id1, id2),
            noSelection=True
        )
    if edges is None:
        return []
    if isinstance(edges, int):
        edges = [edges]
    result = ["{}.e[{}]".format(mesh, i) for i in edges]
    return result

def CheckEdgesBetween(mesh, edgeSource, edges):
    id1 = GetID(edgeSource)
    for edge in edges:        
        id2 = GetID(edge)
        edges = cmds.polySelect(mesh, edgeRingPath=(id1, id2),noSelection=True)
        if edges:
            return(edge)
    return []

def EdgeCenter(mesh, edgeId):
    edgeId = GetID(edgeId)
    dag = NLTA_OpenMaya.GetDagPath(mesh)
    it = om.MItMeshEdge(dag)
    it.setIndex(edgeId)
    p1 = om.MVector(it.point(0, om.MSpace.kWorld))
    p2 = om.MVector(it.point(1, om.MSpace.kWorld))
    return (p1 + p2) * 0.5

def EdgeRatioBetweenJoints(mesh, edgeId, jointA, jointB):
    pA = JointPos(jointA)
    pB = JointPos(jointB)
    edgeC = EdgeCenter(mesh, edgeId)
    boneVec = pB - pA
    edgeVec = edgeC - pA
    t = (edgeVec * boneVec) / boneVec.length()**2
    return max(0, min(1, t))

def EdgeRatioBetweenEdges(mesh, edgeMid, edgeA, edgeB):
    pA = EdgeCenter(mesh, edgeA)
    pB = EdgeCenter(mesh, edgeB)
    pC = EdgeCenter(mesh, edgeMid)
    vecAB = pB - pA
    vecAC = pC - pA
    t = (vecAC * vecAB) / vecAB.length()**2
    return max(0, min(1, t))

def GetFarthestEdge(mesh, baseEdge, edges):
    baseId = GetID(baseEdge)
    baseCenter = EdgeCenter(mesh, baseId)
    maxDist = -1
    farEdge = None
    for edge in edges:
        eid = GetID(edge)
        center = EdgeCenter(mesh, eid)
        dist = (center - baseCenter).length()
        if dist > maxDist:
            maxDist = dist
            farEdge = edge
    return farEdge
    
def GetClosestEdge(mesh, edges, joint):
    jointPos = om.MVector(cmds.xform(joint, q=True, ws=True, t=True))
    minDist = 1e10
    closestEdge = None
    for edge in edges:
        edgeId = GetID(edge)
        center = EdgeCenter(mesh, edgeId)
        dist = (center - jointPos).length()
        if dist < minDist:
            minDist = dist
            closestEdge = edge
    return closestEdge

def GetFarthestVertex(mesh, verts, joint):
    jointPos = om.MVector(cmds.xform(joint, q=True, ws=True, t=True))
    maxDist = -1.0
    farthestVert = None
    for vert in verts:
        vertId = GetID(vert)
        pos = om.MVector(cmds.pointPosition(vert, w=True))
        dist = (pos - jointPos).length()
        if dist > maxDist:
            maxDist = dist
            farthestVert = vert
    return farthestVert

def CheckEdgeLoopClosed(mesh, edges):
    edgeIDs = [GetID(e) if isinstance(e, str) else e for e in edges]
    sel = om.MSelectionList()
    sel.add(mesh)
    dag = sel.getDagPath(0)
    if dag.apiType() != om.MFn.kMesh:
        dag.extendToShape()
    edgeIt = om.MItMeshEdge(dag)
    vertexCount = {}
    for edgeID in edgeIDs:
        edgeIt.setIndex(edgeID)
        v0 = edgeIt.vertexId(0)
        v1 = edgeIt.vertexId(1)
        vertexCount[v0] = vertexCount.get(v0, 0) + 1
        vertexCount[v1] = vertexCount.get(v1, 0) + 1
    return all(count == 2 for count in vertexCount.values())

def SortCircularJoints(joints, clockwise=False):
    if len(joints) < 3:
        return joints[:]
    positions = {}
    center = om.MVector()
    for j in joints:
        p = om.MVector(cmds.xform(j, q=True, ws=True, t=True))
        positions[j] = p
        center += p
    center /= len(joints)
    maxDist = -1
    xAxis = None
    for i in range(len(joints)):
        for k in range(i + 1, len(joints)):
            d = positions[joints[i]] - positions[joints[k]]
            l = d.length()
            if l > maxDist:
                maxDist = l
                xAxis = d.normal()

    normal = om.MVector()
    vecs = [positions[j] - center for j in joints]
    for i in range(len(vecs)):
        for k in range(i + 1, len(vecs)):
            normal += vecs[i] ^ vecs[k]
    if normal.length() < 1e-6:
        cmds.warning("Cannot compute normal.")
        return joints[:]

    normal.normalize()
    yAxis = normal ^ xAxis
    yAxis.normalize()
    result = []
    for j in joints:
        v = positions[j] - center
        x = v * xAxis
        y = v * yAxis
        angle = math.atan2(y, x)
        result.append((angle, j))
    result.sort(key=lambda x: x[0], reverse=clockwise)
    return [j for _, j in result]


#########################

def Normalize(v):
    l = math.sqrt(sum(x*x for x in v))
    return v if l == 0 else [x/l for x in v]

def Dot(a, b):
    return sum(a[i]*b[i] for i in range(3))

def GetPos(v):
    return cmds.xform(v, q=True, ws=True, t=True)



def GetPerpEdge(v1, v2, threshold=0.25):
    p1 = GetPos(v1)
    p2 = GetPos(v2)
    dir_vec = Normalize([p2[i] - p1[i] for i in range(3)])
    edges = cmds.polyListComponentConversion(v1, te=True)
    edges = cmds.ls(edges, fl=True)
    best = None
    best_score = 999
    for e in edges:
        vs = cmds.polyListComponentConversion(e, tv=True)
        vs = cmds.ls(vs, fl=True)
        other = [x for x in vs if x != v1]
        if not other:
            continue
        other = other[0]
        if other == v2:
            continue
        vec = Normalize([GetPos(other)[i] - p1[i] for i in range(3)])
        d = abs(Dot(dir_vec, vec))
        if d < best_score:
            best_score = d
            best = e
    if best_score > threshold:
        return None
    return best

def EdgeLoopToVerts(edge):
    mesh = edge.split(".e[")[0]
    edgeId = GetID(edge)
    edgeIds = cmds.polySelect(mesh,edgeLoop=edgeId,noSelection=True)
    if not edgeIds:
        return []
    loopEdges = ["{}.e[{}]".format(mesh, i) for i in edgeIds]
    verts = cmds.polyListComponentConversion(loopEdges,fromEdge=True,toVertex=True)
    verts = cmds.ls(verts, fl=True)
    return list(dict.fromkeys(verts))

def EdgesToVerts(edges):
    return(cmds.polyListComponentConversion(edges,toVertex=True))

def GetConnectVerts(v, vertSet):
    vertSet = set(vertSet)
    result = []
    for edge in cmds.ls(cmds.polyListComponentConversion(v, te=True), fl=True):
        verts = cmds.ls(cmds.polyListComponentConversion(edge, tv=True), fl=True)
        other = next((x for x in verts if x != v), None)
        if other and other in vertSet:
            result.append((v, other, edge))
    return result


def ListToPerVerts(verts, threshold=9999):
    returnData = {}
    for v in verts:
        connections = GetConnectVerts(v,verts)
        for (a, b, _) in connections:
            edge = GetPerpEdge(a, b, threshold)
            edgeLoopVerts = EdgesToVerts(GetEdgeLoop(edge))
            returnData[v] = edgeLoopVerts        
    return(returnData)


def GetIntersectVerts(meshA, meshB, threshold,*arr):
    close_curve=True
    cpm = cmds.createNode("closestPointOnMesh")
    shapeB = cmds.listRelatives(meshB, shapes=True, fullPath=True)[0]
    cmds.connectAttr(
        "{}.worldMesh[0]".format(shapeB),
        "{}.inMesh".format(cpm),
        force=True
    )

    cmds.connectAttr(
        "{}.worldMatrix[0]".format(meshB),
        "{}.inputMatrix".format(cpm),
        force=True
    )

    verts = cmds.ls(
        "{}.vtx[*]".format(meshA),
        fl=True
    )
    close_verts = []
    for v in verts:
        pos = cmds.pointPosition(v, world=True)
        cmds.setAttr(
            "{}.inPosition".format(cpm),
            *pos,
            type="double3"
        )
        closest = cmds.getAttr(
            "{}.position".format(cpm)
        )[0]
        dist = math.sqrt(sum((pos[i] - closest[i]) ** 2 for i in range(3)))
        if dist <= threshold:
            close_verts.append(v)
    cmds.delete(cpm)
    return(close_verts)

def GetVertexBetweenParentChild(data,*arr):
    mesh =  data["mesh"]
    source = data["source"]
    des = data["destination"]
    closetVert =  GetClosestVertex(mesh,source)
    edgeLoop = GetJointEdgeLoop(mesh,source,closetVert)
    sourceClosestEgde = GetClosestEdge(mesh,edgeLoop,source)
    desClosestEdge = GetClosestEdge(mesh,edgeLoop,des)
    edgeBetween = EdgesBetween(mesh,sourceClosestEgde,desClosestEdge)
    cmds.select(edgeBetween)
    """
    edgeLoop =  GetJointEdge({
        "mesh":mesh,
        "joint":source

    })
    """


def GetVertRatioBetweenJoints(data, *arr):
    vert = data["vert"]
    joints = data["joints"]
    if len(joints) != 2:
        cmds.error("Need exactly 2 joints")
    joint1, joint2 = joints
    dist1 = NLTA_General.GetDistance(vert, joint1)
    dist2 = NLTA_General.GetDistance(vert, joint2)
    total = dist1 + dist2
    if total == 0:
        ratio1 = 0.5
        ratio2 = 0.5
    else:
        ratio1 = 1.0 - (dist1 / total)
        ratio2 = 1.0 - (dist2 / total)

    return {
        "vert": vert,
        "joints": [joint1, joint2],
        "ratios": [ratio1, ratio2]
    }





def GetMirrorVertexByUv(vtx, axis="U", tol=0.01):
    mesh = vtx.split(".")[0]
    uvs = cmds.polyListComponentConversion(vtx, tuv=True)
    uvs = cmds.ls(uvs, fl=True)
    if not uvs:
        return None
    uv = uvs[0]
    u, v = cmds.polyEditUV(uv, q=True)
    if axis.upper() == "U":
        target_uv = (1.0 - u, v)
    else:
        target_uv = (u, 1.0 - v)
    vtx_count = cmds.polyEvaluate(mesh, v=True)
    best = None
    best_dist = 999999
    for i in range(vtx_count):
        other = "{}.vtx[{}]".format(mesh,i)
        other_uvs = cmds.polyListComponentConversion(
            other,
            tuv=True
        )
        other_uvs = cmds.ls(other_uvs, fl=True)
        if not other_uvs:
            continue
        ou, ov = cmds.polyEditUV(
            other_uvs[0],
            q=True
        )
        dist = (
            abs(ou - target_uv[0]) +
            abs(ov - target_uv[1])
        )
        if dist < best_dist:
            best_dist = dist
            best = other
    if best_dist <= tol:
        return best
    return None


def MirrorVertexByUvSingle(vtx, axis="X"):
    mirror_vtx = GetMirrorVertexByUv(vtx)
    if not mirror_vtx:
        cmds.warning("Mirror vertex not found")
        return
    pos = cmds.pointPosition(vtx, w=True)
    x, y, z = pos
    axis = axis.upper()
    if axis == "X":
        mirrored_pos = (-x, y, z)
    elif axis == "Y":
        mirrored_pos = (x, -y, z)
    elif axis == "Z":
        mirrored_pos = (x, y, -z)
    else:
        cmds.warning("Invalid axis")
        return
    cmds.xform(
        mirror_vtx,
        ws=True,
        t=mirrored_pos
    )

def MirrorVertexByUv(*arr):
    verts = cmds.ls(selection=True,flatten=True)
    for vert in verts:
        MirrorVertexByUvSingle(vert)


def MirrorVertPos(*arr):
    sel = cmds.ls(orderedSelection=True)
    if len(sel) != 2:
        cmds.warning("Select source vertex then target vertex")
        return
    src = sel[0]
    dst = sel[1]
    x, y, z = cmds.pointPosition(src, w=True)
    mirrored_pos = (-x, y, z)
    cmds.xform(
        dst,
        ws=True,
        t=mirrored_pos
    )

"""
def GetDistanceVertex(data,*arr):
    def getDag(node):
        sel = om.MSelectionList()
        sel.add(node)
        return sel.getDagPath(0)
    sourceMesh = data["source"]
    targetMesh = data["target"]
    maxDistance = data["distance"]
    sourceDag = getDag(sourceMesh)
    targetDag = getDag(targetMesh)
    sourceFn = om.MFnMesh(sourceDag)
    targetFn = om.MFnMesh(targetDag)
    result = []
    points = sourceFn.getPoints(om.MSpace.kWorld)
    for i, p in enumerate(points):
        closestPoint, normal, faceId = \
            targetFn.getClosestPointAndNormal(
                om.MPoint(p),
                om.MSpace.kWorld
            )
        vec = om.MVector(p - closestPoint)
        dot = vec * normal
        dist = vec.length()
        if dot > 0 and dist <= maxDistance:
            ratio = dist / maxDistance
            result.append({
                "vertex":
                    "%s.vtx[%s]" % (
                        sourceMesh,
                        i
                    ),
                "distance":
                    dist,
                "ratio":
                    ratio
            })
    verts = [item["vertex"] for item in result]
    cmds.select(verts, r=True)
    return result
"""


def ColorVertices(vertices, color=(1, 0, 0, 1)):
    def getDag(node):
        sel = om.MSelectionList()
        sel.add(node)
        return sel.getDagPath(0)
    meshMap = {}
    for vtx in vertices:
        mesh = vtx.split(".")[0]
        idx = int(vtx.split("[")[-1][:-1])
        if mesh not in meshMap:
            meshMap[mesh] = []
        meshMap[mesh].append(idx)
    for mesh, ids in meshMap.items():
        dag = getDag(mesh)
        meshFn = om.MFnMesh(dag)
        colors = [om.MColor(color)for _ in ids]
        meshFn.setVertexColors(colors,ids)
        shape = cmds.listRelatives(mesh,s=True,ni=True)[0]
        cmds.setAttr(shape + ".displayColors",1)

def GetMeshComponents(mesh):
    sel = om.MSelectionList()
    sel.add(mesh)
    dagPath = sel.getDagPath(0)
    meshFn = om.MFnMesh(dagPath)
    vertexCount = meshFn.numVertices
    adjacency = [[] for _ in range(vertexCount)]
    for edgeId in range(meshFn.numEdges):
        v1, v2 = meshFn.getEdgeVertices(edgeId)
        adjacency[v1].append(v2)
        adjacency[v2].append(v1)
    visited = set()
    components = []
    for startVertex in range(vertexCount):
        if startVertex in visited:
            continue
        component = []
        stack = [startVertex]
        visited.add(startVertex)
        while stack:
            vertex = stack.pop()
            component.append(vertex)
            for neighbor in adjacency[vertex]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    stack.append(neighbor)
        components.append(component)
    return components


def MatchVertexPairs(meshA, meshB, vertsA, vertsB):
    def GetMesh(mesh):
        sel = om.MSelectionList()
        sel.add(mesh)
        path = sel.getDagPath(0)
        fn = om.MFnMesh(path)
        return path, fn
    pathA, fnA = GetMesh(meshA)
    pathB, fnB = GetMesh(meshB)

    if len(vertsA) != 3 or len(vertsB) != 3:
        raise ValueError("Exactly 3 vertices are required for each mesh.")

    if fnA.numVertices != fnB.numVertices:
        raise ValueError("Meshes have different vertex counts.")

    def BuildVertexFaces(path, vertexCount):
        result = {}
        it = om.MItMeshVertex(path)
        for vertexID in range(vertexCount):
            it.setIndex(vertexID)
            result[vertexID] = set(it.getConnectedFaces())
        return result

    vertexFacesA = BuildVertexFaces(pathA,fnA.numVertices)
    vertexFacesB = BuildVertexFaces(pathB,fnB.numVertices)

    def FindSeedFace(fn, vertexFaces, vertices):
        commonFaces = (vertexFaces[vertices[0]] & vertexFaces[vertices[1]] & vertexFaces[vertices[2]] )
        for faceID in commonFaces:
            faceVertices = list(fn.getPolygonVertices(faceID))
            if not all(vertex in faceVertices for vertex in vertices):
                continue
            count = len(faceVertices)
            for center in vertices:
                index = faceVertices.index(center)
                prevVertex = faceVertices[(index - 1) % count]
                nextVertex = faceVertices[(index + 1) % count]
                others = [vertex for vertex in vertices if vertex != center ]
                if (others[0] in (prevVertex, nextVertex) and others[1] in (prevVertex, nextVertex)):
                    return faceID
        raise ValueError(
            "The 3 vertices must lie on the same face "
            "and form 2 connected edges."
        )
    seedFaceA = FindSeedFace(fnA,vertexFacesA,vertsA)
    seedFaceB = FindSeedFace(fnB,vertexFacesB,vertsB)

    def FindCenterVertex(fn, faceID, vertices):
        faceVertices = list(fn.getPolygonVertices(faceID))
        count = len(faceVertices)
        for center in vertices:
            index = faceVertices.index(center)
            prevVertex = faceVertices[ (index - 1) % count ]
            nextVertex = faceVertices[ (index + 1) % count ]
            others = [ vertex for vertex in vertices if vertex != center ]
            if ( others[0] in (prevVertex, nextVertex) and others[1] in (prevVertex, nextVertex) ):
                return center
        raise ValueError( "Could not determine center vertex." )
    centerA = FindCenterVertex(fnA,seedFaceA,vertsA)
    centerB = FindCenterVertex(fnB,seedFaceB,vertsB)

    outerA = [ vertex for vertex in vertsA if vertex != centerA ]
    outerB = [ vertex for vertex in vertsB if vertex != centerB ]

    mapping = { centerA: centerB }
    reverseMapping = { centerB: centerA }
    mapping[outerA[0]] = outerB[0]
    mapping[outerA[1]] = outerB[1]
    reverseMapping[outerB[0]] = outerA[0]
    reverseMapping[outerB[1]] = outerA[1]

    def GetComponent(path, startVertex):
        component = set()
        it = om.MItMeshVertex(path)
        stack = [startVertex]
        while stack:
            vertexID = stack.pop()
            if vertexID in component:
                continue
            component.add(vertexID)
            it.setIndex(vertexID)
            neighbors = it.getConnectedVertices()
            for neighbor in neighbors:
                if neighbor not in component:
                    stack.append(neighbor)
        return component

    componentA = GetComponent(pathA,centerA)
    componentB = GetComponent(pathB,centerB)
    if len(componentA) != len(componentB):
        raise ValueError(
            "Selected components have different vertex counts."
        )

    faceMapping = {seedFaceA: seedFaceB}
    reverseFaceMapping = {seedFaceB: seedFaceA}

    def FindMatchingFace(faceA):
        verticesA = list(fnA.getPolygonVertices(faceA))
        mappedVertices = []
        for vertexA in verticesA:
            if vertexA in mapping:
                mappedVertices.append(mapping[vertexA])
        if len(mappedVertices) < 2:
            return None
        candidateFaces = None
        for vertexB in mappedVertices:
            faces = vertexFacesB[vertexB]
            if candidateFaces is None:
                candidateFaces = set(faces)
            else:
                candidateFaces &= faces

        if not candidateFaces:
            return None

        for faceB in candidateFaces:
            if faceB in reverseFaceMapping:
                continue

            verticesB = set(fnB.getPolygonVertices(faceB))
            if all( vertex in verticesB for vertex in mappedVertices ):
                return faceB
        return None

    def MapFace(faceA, faceB):
        verticesA = list(fnA.getPolygonVertices(faceA))
        verticesB = list(fnB.getPolygonVertices(faceB))
        if len(verticesA) != len(verticesB):
            raise ValueError(
                "Topology mismatch: face vertex count differs."
            )
        count = len(verticesA)
        candidates = []

        for reverse in (False, True):
            orderA = (list(reversed(verticesA)) if reverse else verticesA )
            for offset in range(count):
                valid = True
                candidate = []
                for i in range(count):
                    vertexA = orderA[i]
                    vertexB = verticesB[ (i + offset) % count ]
                    if vertexA in mapping:
                        if mapping[vertexA] != vertexB:
                            valid = False
                            break
                    if vertexB in reverseMapping:
                        if reverseMapping[vertexB] != vertexA:
                            valid = False
                            break
                    candidate.append( (vertexA, vertexB) )
                if valid:
                    candidates.append(candidate)
        if not candidates:
            raise RuntimeError( "Cannot determine mapping for face {} -> {}.".format( faceA, faceB ) )

        if len(candidates) > 1:
            raise RuntimeError( "Ambiguous topology at face {} -> {}. " "More seed vertices are required.".format( faceA, faceB ) )
        for vertexA, vertexB in candidates[0]:
            if vertexA not in mapping:
                mapping[vertexA] = vertexB
                reverseMapping[vertexB] = vertexA
    processedFaces = set()
    changed = True
    while changed:
        changed = False
        for faceA in list(faceMapping.keys()):
            if faceA in processedFaces:
                continue
            faceB = faceMapping[faceA]
            MapFace( faceA, faceB )
            processedFaces.add(faceA)
            changed = True
            verticesA = fnA.getPolygonVertices(faceA)
            for vertexA in verticesA:
                if vertexA not in mapping:
                    continue
                vertexB = mapping[vertexA]
                for nextFaceA in vertexFacesA[vertexA]:
                    if nextFaceA in faceMapping:
                        continue
                    nextFaceB = FindMatchingFace(nextFaceA)
                    if nextFaceB is None:
                        continue
                    faceMapping[nextFaceA] = nextFaceB
                    reverseFaceMapping[nextFaceB] = nextFaceA

    missing = [ vertex for vertex in componentA if vertex not in mapping ]
    if missing:
        raise RuntimeError(
            "Failed to match entire component. "
            "{} vertices remain.".format(
                len(missing)
            )
        )

    return [
        (vertexA, mapping[vertexA])
        for vertexA in sorted(componentA)
    ]
"""
pairs = MatchVertexPairs(
    "sleeves_GEO",
    "sleeves_GEO1",
    [935,936,976],
    [444,445,485]
)
for pair in pairs:
    print('cmds.select("sleeves_GEO.vtx[{}]","sleeves_GEO1.vtx[{}]")'.format(pair[0],pair[1]))
"""


def FindSymmetricVertexPairs(mesh, vertsA, vertsB):
    if len(vertsA) != 3 or len(vertsB) != 3:
        raise ValueError("Exactly 3 vertices are required on each component.")
    if set(vertsA) & set(vertsB):
        raise ValueError("vertsA and vertsB must belong to different components.")

    # ---------------------------------------------------------
    # Get mesh
    # ---------------------------------------------------------

    sel = om.MSelectionList()
    sel.add(mesh)
    path = sel.getDagPath(0)
    fn = om.MFnMesh(path)

    # ---------------------------------------------------------
    # Build vertex -> faces
    # ---------------------------------------------------------

    vertexFaces = {}
    it = om.MItMeshVertex(path)
    for vertexID in range(fn.numVertices):
        it.setIndex(vertexID)
        vertexFaces[vertexID] = set(it.getConnectedFaces())

    # ---------------------------------------------------------
    # Find common face
    # ---------------------------------------------------------

    def FindCommonFace(vertices):
        common = set(vertexFaces[vertices[0]])
        for vertex in vertices[1:]:
            common &= vertexFaces[vertex]
        if not common:
            return None
        return next(iter(common))
    faceA = FindCommonFace(vertsA)
    faceB = FindCommonFace(vertsB)

    if faceA is None:
        raise ValueError("vertsA are not on the same face.")

    if faceB is None:
        raise ValueError("vertsB are not on the same face.")

    # ---------------------------------------------------------
    # Find center vertex
    #
    # The 3 selected vertices must form 2 connected edges.
    # ---------------------------------------------------------
    def FindCenterVertex(faceID, vertices):
        faceVertices = list(fn.getPolygonVertices(faceID))
        count = len(faceVertices)
        for vertex in vertices:
            index = faceVertices.index(vertex)
            prevVertex = faceVertices[(index - 1) % count]
            nextVertex = faceVertices[(index + 1) % count]
            others = [v for v in vertices if v != vertex]
            if (others[0] in (prevVertex, nextVertex) and others[1] in (prevVertex, nextVertex)):
                return vertex
        return None

    centerA = FindCenterVertex(faceA, vertsA)
    centerB = FindCenterVertex(faceB, vertsB)
    if centerA is None or centerB is None:
        raise ValueError(
            "Each group of 3 vertices must form "
            "2 connected edges on the same face."
        )

    # ---------------------------------------------------------
    # Get connected component
    # ---------------------------------------------------------

    def GetComponent(startVertex):
        component = set()
        stack = [startVertex]
        it = om.MItMeshVertex(path)
        while stack:
            vertex = stack.pop()
            if vertex in component:
                continue
            component.add(vertex)
            it.setIndex(vertex)
            for neighbor in it.getConnectedVertices():
                if neighbor not in component:
                    stack.append(neighbor)
        return component
    componentA = GetComponent(centerA)
    componentB = GetComponent(centerB)

    # Verify seeds
    if not all(vertex in componentA for vertex in vertsA):
        raise ValueError("vertsA are not in the same component.")

    if not all( vertex in componentB for vertex in vertsB):
        raise ValueError("vertsB are not in the same component.")

    if len(componentA) != len(componentB):
        raise ValueError(
            "The two components have different vertex counts: "
            "{} vs {}".format(
                len(componentA),
                len(componentB)
            )
        )

    # ---------------------------------------------------------
    # Build face -> vertices
    # ---------------------------------------------------------

    faceVertices = {}
    componentFacesA = set()
    componentFacesB = set()

    for vertex in componentA:
        componentFacesA.update(vertexFaces[vertex])

    for vertex in componentB:
        componentFacesB.update(vertexFaces[vertex])

    for faceID in componentFacesA | componentFacesB:
        faceVertices[faceID] = list(fn.getPolygonVertices(faceID))

    # ---------------------------------------------------------
    # Initial vertex mapping
    # ---------------------------------------------------------

    mapping = {}
    reverseMapping = {}
    for a, b in zip(vertsA, vertsB):

        if a in mapping and mapping[a] != b:
            raise ValueError("Conflicting mapping on component A.")

        if b in reverseMapping and reverseMapping[b] != a:
            raise ValueError("Conflicting mapping on component B.")
        mapping[a] = b
        reverseMapping[b] = a

    # ---------------------------------------------------------
    # Initial face mapping
    # ---------------------------------------------------------

    faceMapping = {faceA: faceB}
    reverseFaceMapping = {faceB: faceA}

    # ---------------------------------------------------------
    # Map a face using cyclic topology
    # ---------------------------------------------------------

    def MapFace(sourceFace, targetFace):
        source = faceVertices[sourceFace]
        target = faceVertices[targetFace]
        if len(source) != len(target):
            raise RuntimeError("Face topology mismatch: {} -> {}".format(sourceFace,targetFace))
        count = len(source)
        candidates = []
        # -----------------------------------------------------
        # Try both winding directions and all cyclic offsets.
        # -----------------------------------------------------
        for reverse in (False, True):
            sourceOrder = (list(reversed(source)) if reverse else source)
            for offset in range(count):
                candidate = []
                valid = True
                for i in range(count):
                    vertexA = sourceOrder[i]
                    vertexB = target[ (i + offset) % count ]
                    if vertexA in mapping:
                        if mapping[vertexA] != vertexB:
                            valid = False
                            break
                    if vertexB in reverseMapping:
                        if reverseMapping[vertexB] != vertexA:
                            valid = False
                            break
                    candidate.append((vertexA, vertexB))
                if valid:
                    candidates.append(candidate)

        if not candidates:
            raise RuntimeError("Cannot map face {} -> {}.".format(sourceFace,targetFace))

        # -----------------------------------------------------
        # If there is more than one valid solution, topology
        # alone cannot distinguish them.
        # -----------------------------------------------------
        if len(candidates) > 1:
            raise RuntimeError(
                "Ambiguous topology between face {} and {}. "
                "The selected 3 vertices are not enough "
                "to uniquely determine the symmetry.".format(
                    sourceFace,
                    targetFace
                )
            )

        candidate = candidates[0]
        for vertexA, vertexB in candidate:
            if vertexA not in mapping:
                mapping[vertexA] = vertexB
                reverseMapping[vertexB] = vertexA

    # ---------------------------------------------------------
    # Find target face from mapped vertices
    # ---------------------------------------------------------

    def FindMatchingFace(sourceFace):
        sourceVertices = faceVertices[sourceFace]
        mappedVertices = []
        for vertexA in sourceVertices:
            if vertexA in mapping:
                mappedVertices.append(mapping[vertexA])

        if len(mappedVertices) < 2:
            return None
        candidates = None
        for vertexB in mappedVertices:
            faces = ( vertexFaces[vertexB] & componentFacesB)
            if candidates is None:
                candidates = set(faces)
            else:
                candidates &= faces

        if not candidates:
            return None

        for targetFace in candidates:
            if targetFace in reverseFaceMapping:
                continue
            targetVertices = set(faceVertices[targetFace])
            if all(vertexB in targetVertices for vertexB in mappedVertices):
                return targetFace
        return None

    # ---------------------------------------------------------
    # Traverse from component A to component B
    # ---------------------------------------------------------

    processedFaces = set()
    while True:
        progress = False
        for sourceFace in list(faceMapping.keys()):
            if sourceFace in processedFaces:
                continue
            targetFace = faceMapping[sourceFace]
            # Map vertices of this face
            MapFace(sourceFace,targetFace)
            processedFaces.add(sourceFace)
            progress = True
            # Find neighboring faces
            sourceVertices = faceVertices[sourceFace]
            for vertexA in sourceVertices:
                if vertexA not in mapping:
                    continue
                for nextFaceA in vertexFaces[vertexA]:
                    if nextFaceA not in componentFacesA:
                        continue
                    if nextFaceA in faceMapping:
                        continue
                    nextFaceB = FindMatchingFace(nextFaceA)
                    if nextFaceB is None:
                        continue
                    if nextFaceB in reverseFaceMapping:
                        continue
                    faceMapping[nextFaceA] = nextFaceB
                    reverseFaceMapping[nextFaceB] = nextFaceA
                    progress = True
        if not progress:
            break

    # ---------------------------------------------------------
    # Validate
    # ---------------------------------------------------------

    missingA = [vertex for vertex in componentA if vertex not in mapping ]
    if missingA:
        raise RuntimeError(
            "Could not match entire component. "
            "{} vertices remain.".format(
                len(missingA)
            )
        )
    # Make sure every target vertex was mapped
    if len(mapping) != len(componentA):
        raise RuntimeError("Mapping count mismatch.")

    return [
        (vertexA, mapping[vertexA])
        for vertexA in sorted(componentA)
    ]
"""    
pairs = FindSymmetricVertexPairs(
    "sleeves_GEO1",
    [977, 935, 934],
    [486, 444, 443]
)

for pair in pairs:
    print('cmds.select("sleeves_GEO1.vtx[{}]","sleeves_GEO1.vtx[{}]")'.format(pair[0],pair[1]))
"""

"""
def GetMirrorPairsSameComponent(mesh, vertsA, vertsB):
    print(mesh)
    print(vertsA)
    print(vertsB)
    if len(vertsA) != 3 or len(vertsB) != 3:
        raise ValueError(
            "Exactly 3 vertices are required on each side."
        )

    if set(vertsA) & set(vertsB):
        raise ValueError(
            "vertsA and vertsB must be different vertices."
        )
    sel = om.MSelectionList()
    sel.add(mesh)
    path = sel.getDagPath(0)
    fn = om.MFnMesh(path)
    vertexFaces = {}
    it = om.MItMeshVertex(path)
    for vertexID in range(fn.numVertices):
        it.setIndex(vertexID)
        vertexFaces[vertexID] = set(it.getConnectedFaces())

    def GetComponent(startVertex):
        component = set()
        stack = [startVertex]
        it = om.MItMeshVertex(path)
        while stack:
            vertex = stack.pop()
            if vertex in component:
                continue
            component.add(vertex)
            it.setIndex(vertex)
            for neighbor in it.getConnectedVertices():
                if neighbor not in component:
                    stack.append(neighbor)
        return component
    componentA = GetComponent(vertsA[0])
    componentB = GetComponent(vertsB[0])
    if componentA != componentB:
        raise ValueError(
            "vertsA and vertsB must belong to the same "
            "connected component."
        )
    component = componentA
    if not all(v in component for v in vertsA):
        raise ValueError(
            "vertsA are not in the same component."
        )

    if not all(v in component for v in vertsB):
        raise ValueError(
            "vertsB are not in the same component."
        )

    # ---------------------------------------------------------
    # Find seed face
    # ---------------------------------------------------------

    def FindCommonFace(vertices):

        common = set(vertexFaces[vertices[0]])

        for vertex in vertices[1:]:
            common &= vertexFaces[vertex]

        if not common:
            return None

        return next(iter(common))

    faceA = FindCommonFace(vertsA)
    faceB = FindCommonFace(vertsB)

    if faceA is None:
        raise ValueError(
            "vertsA are not on the same face."
        )

    if faceB is None:
        raise ValueError(
            "vertsB are not on the same face."
        )

    # ---------------------------------------------------------
    # Find center vertex
    # ---------------------------------------------------------

    def FindCenterVertex(faceID, vertices):

        faceVertices = list(
            fn.getPolygonVertices(faceID)
        )

        count = len(faceVertices)

        for vertex in vertices:

            index = faceVertices.index(vertex)

            prevVertex = faceVertices[
                (index - 1) % count
            ]

            nextVertex = faceVertices[
                (index + 1) % count
            ]

            others = [
                v for v in vertices
                if v != vertex
            ]

            if (
                others[0] in (prevVertex, nextVertex)
                and
                others[1] in (prevVertex, nextVertex)
            ):
                return vertex

        return None

    centerA = FindCenterVertex(faceA, vertsA)
    centerB = FindCenterVertex(faceB, vertsB)

    if centerA is None or centerB is None:

        raise ValueError(
            "Each group of 3 vertices must form "
            "2 connected edges on the same face."
        )

    # ---------------------------------------------------------
    # Initial mapping
    # ---------------------------------------------------------

    mapping = {}
    reverseMapping = {}

    for a, b in zip(vertsA, vertsB):

        if a in mapping and mapping[a] != b:
            raise ValueError(
                "Conflicting vertex mapping."
            )

        if b in reverseMapping and reverseMapping[b] != a:
            raise ValueError(
                "Conflicting vertex mapping."
            )

        mapping[a] = b
        reverseMapping[b] = a

    # ---------------------------------------------------------
    # Component faces
    # ---------------------------------------------------------

    componentFaces = set()

    for vertex in component:
        componentFaces.update(
            vertexFaces[vertex]
        )

    faceVertices = {}

    for faceID in componentFaces:

        faceVertices[faceID] = list(
            fn.getPolygonVertices(faceID)
        )

    # ---------------------------------------------------------
    # Find corresponding face
    # ---------------------------------------------------------

    def FindMatchingFace(sourceFace):

        sourceVertices = faceVertices[sourceFace]

        mappedVertices = [
            mapping[v]
            for v in sourceVertices
            if v in mapping
        ]

        if len(mappedVertices) < 2:
            return None

        candidateFaces = None

        for vertex in mappedVertices:

            faces = (
                vertexFaces[vertex]
                & componentFaces
            )

            if candidateFaces is None:
                candidateFaces = set(faces)
            else:
                candidateFaces &= faces

        if not candidateFaces:
            return None

        for targetFace in candidateFaces:

            targetVertices = set(
                faceVertices[targetFace]
            )

            if all(
                v in targetVertices
                for v in mappedVertices
            ):
                return targetFace

        return None

    # ---------------------------------------------------------
    # Map face
    # ---------------------------------------------------------

    def MapFace(sourceFace, targetFace):

        source = faceVertices[sourceFace]
        target = faceVertices[targetFace]

        if len(source) != len(target):
            raise RuntimeError(
                "Face topology mismatch."
            )

        count = len(source)
        candidates = []

        for reverse in (False, True):

            sourceOrder = (
                list(reversed(source))
                if reverse
                else source
            )

            for offset in range(count):

                candidate = []
                valid = True

                for i in range(count):

                    a = sourceOrder[i]

                    b = target[
                        (i + offset) % count
                    ]

                    if a in mapping:

                        if mapping[a] != b:
                            valid = False
                            break

                    if b in reverseMapping:

                        if reverseMapping[b] != a:
                            valid = False
                            break

                    candidate.append(
                        (a, b)
                    )

                if valid:
                    candidates.append(candidate)

        if not candidates:

            raise RuntimeError(
                "Cannot map face {} -> {}.".format(
                    sourceFace,
                    targetFace
                )
            )

        if len(candidates) > 1:

            raise RuntimeError(
                "Ambiguous topology at face {} -> {}. "
                "More seed vertices are required.".format(
                    sourceFace,
                    targetFace
                )
            )

        for a, b in candidates[0]:

            if a not in mapping:

                mapping[a] = b
                reverseMapping[b] = a

    # ---------------------------------------------------------
    # Traverse
    # ---------------------------------------------------------

    faceMapping = {
        faceA: faceB
    }

    reverseFaceMapping = {
        faceB: faceA
    }

    processed = set()

    while True:

        progress = False

        for sourceFace in list(faceMapping):

            if sourceFace in processed:
                continue

            targetFace = faceMapping[sourceFace]

            MapFace(
                sourceFace,
                targetFace
            )

            processed.add(sourceFace)
            progress = True

            # -------------------------------------------------
            # Find neighboring faces
            # -------------------------------------------------

            for vertexA in faceVertices[sourceFace]:

                if vertexA not in mapping:
                    continue

                for nextFace in vertexFaces[vertexA]:

                    if nextFace not in componentFaces:
                        continue

                    if nextFace in faceMapping:
                        continue

                    targetFace = FindMatchingFace(
                        nextFace
                    )

                    if targetFace is None:
                        continue

                    if targetFace in reverseFaceMapping:
                        continue

                    faceMapping[nextFace] = targetFace
                    reverseFaceMapping[targetFace] = nextFace

                    progress = True

        if not progress:
            break

    # ---------------------------------------------------------
    # Validate
    # ---------------------------------------------------------

    missing = [
        vertex
        for vertex in component
        if vertex not in mapping
    ]

    if missing:

        raise RuntimeError(
            "Could not resolve all vertices. "
            "{} vertices remain.".format(
                len(missing)
            )
        )

    return [
        (a, mapping[a])
        for a in sorted(component)
    ]

pairs = FindSymmetricVertexPairs(
    "sleeves_GEO2",
    [913, 928, 907],
    [423, 438,417]
)


for pair in pairs:
    print('cmds.select("sleeves_GEO2.vtx[{}]","sleeves_GEO2.vtx[{}]")'.format(pair[0],pair[1]))
"""



def CopySkinByVertexPairs(meshA, meshB, pairs):
    """
    Copy skin weights from meshA -> meshB using vertex pairs.

    pairs:
        [
            (vertexA, vertexB),
            ...
        ]

    Requirements:
        - meshA and meshB already have skinClusters.
        - Both skinClusters use the same influences by name.
        - Vertex pairs describe the correspondence.
    """

    # ---------------------------------------------------------
    # Get dag path
    # ---------------------------------------------------------

    def GetDagPath(mesh):
        sel = om.MSelectionList()
        sel.add(mesh)
        return sel.getDagPath(0)
    dagA = GetDagPath(meshA)
    dagB = GetDagPath(meshB)

    def GetSkinCluster(dagPath):
        history = om.MItDependencyGraph(
            dagPath.node(),
            om.MFn.kSkinClusterFilter,
            om.MItDependencyGraph.kUpstream,
            om.MItDependencyGraph.kDepthFirst,
            om.MItDependencyGraph.kPlugLevel
        )
        if history.isDone():
            return None
        obj = history.currentItem()
        return oma.MFnSkinCluster(obj)
    skinA = GetSkinCluster(dagA)
    skinB = GetSkinCluster(dagB)
    if skinA is None:
        raise RuntimeError("No skinCluster found on {}".format(meshA))

    if skinB is None:
        raise RuntimeError("No skinCluster found on {}".format(meshB))

    influencesA = skinA.influenceObjects()
    influencesB = skinB.influenceObjects()

    influenceNamesA = [om.MFnDagNode(obj).fullPathName() for obj in influencesA]
    influenceNamesB = [om.MFnDagNode(obj).fullPathName() for obj in influencesB]

    # ---------------------------------------------------------
    # Build influence mapping
    #
    # Source influence index -> target influence index
    # ---------------------------------------------------------

    influenceMap = {}
    for indexA, nameA in enumerate(influenceNamesA):
        if nameA not in influenceNamesB:
            raise RuntimeError(
                "Influence '{}' from {} "
                "does not exist on {}.".format(
                    nameA,
                    meshA,
                    meshB
                )
            )
        influenceMap[indexA] = (influenceNamesB.index(nameA))

    # ---------------------------------------------------------
    # Get all source weights
    # ---------------------------------------------------------

    sourceComponents = om.MFnSingleIndexedComponent().create(om.MFn.kMeshVertComponent)
    sourceComponentFn = om.MFnSingleIndexedComponent(sourceComponents)
    sourceVertexIDs = [vertexA for vertexA, vertexB in pairs]
    sourceComponentFn.addElements(sourceVertexIDs)
    weightsA, influenceCountA = skinA.getWeights(dagA,sourceComponents)

    # ---------------------------------------------------------
    # Get target component
    # ---------------------------------------------------------

    targetComponents = om.MFnSingleIndexedComponent().create(om.MFn.kMeshVertComponent)
    targetComponentFn = om.MFnSingleIndexedComponent(targetComponents)
    targetVertexIDs = [vertexB for vertexA, vertexB in pairs]
    targetComponentFn.addElements(targetVertexIDs)

    # ---------------------------------------------------------
    # Build target weights
    #
    # MFnSkinCluster.setWeights expects:
    #
    # vertex0:
    #   influence0, influence1, ...
    #
    # vertex1:
    #   influence0, influence1, ...
    #
    # ---------------------------------------------------------

    influenceCountB = len(influencesB)
    targetWeights = [ 0.0] * (len(pairs) * influenceCountB)
    for vertexIndex in range(len(pairs)):
        sourceOffset = (vertexIndex *influenceCountA)
        targetOffset = (vertexIndex *influenceCountB)

        for sourceInfluenceIndex in range(influenceCountA):
            weight = weightsA[sourceOffset + sourceInfluenceIndex]
            if weight == 0.0:
                continue
            targetInfluenceIndex = influenceMap[sourceInfluenceIndex]
            targetWeights[targetOffset + targetInfluenceIndex] = weight

    # ---------------------------------------------------------
    # Set weights
    # ---------------------------------------------------------

    influenceIndicesB = om.MIntArray(range(influenceCountB))
    targetWeights = om.MDoubleArray(targetWeights)
    skinB.setWeights(dagB,targetComponents,influenceIndicesB,targetWeights,False)
    print("Copied skin weights: {} vertices".format(len(pairs)))

"""
pairs = FindSymmetricVertexPairsSameComponent(
    "sleeves_GEO1",
    [977, 935, 934],
    [486, 444, 443]
)

CopySkinByVertexPairs(
    "sleeves_GEO1",
    "body_GEO",
    pairs
)
"""

def FindMirrorJointPairs(joints,axis=0,tolerance=0.001):
    jointData = {}
    for joint in joints:
        sel = om.MSelectionList()
        sel.add(joint)
        dagPath = sel.getDagPath(0)
        matrix = dagPath.inclusiveMatrix()
        position = om.MTransformationMatrix(matrix).translation(om.MSpace.kWorld)
        jointData[joint] = (position.x,position.y,position.z)

    def MirrorPosition(position):
        result = list(position)
        result[axis] *= -1.0
        return tuple(result)

    def DistanceSquared(a, b):
        return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2)

    toleranceSquared = tolerance ** 2
    pairs = []
    used = set()

    for jointA, positionA in jointData.items():
        if jointA in used:
            continue
        mirroredPosition = MirrorPosition(positionA)
        axisDistance = abs(positionA[axis])
        if axisDistance <= tolerance:
            pairs.append((jointA, jointA))
            used.add(jointA)
            continue
        bestJoint = None
        bestDistance = None
        for jointB, positionB in jointData.items():
            if jointB == jointA:
                continue
            if jointB in used:
                continue
            distance = DistanceSquared(mirroredPosition,positionB)
            if distance > toleranceSquared:
                continue

            if (bestDistance is None or distance < bestDistance):
                bestJoint = jointB
                bestDistance = distance

        if bestJoint is None:
            continue

        pairs.append((jointA, bestJoint))
        used.add(jointA)
        used.add(bestJoint)
    return pairs

def MirrorSkinByPairs(mesh,vertexPairs,jointPairs):
    """
    Mirror skin weights using:

        vertexPairs:
            [(vertexA, vertexB), ...]

        jointPairs:
            [(jointA, jointB), ...]

    Weight:
        vertexA / jointA
            ↓
        vertexB / jointB
    """

    if not vertexPairs:
        return

    sel = om.MSelectionList()
    sel.add(mesh)
    dagPath = sel.getDagPath(0)
    dgIter = om.MItDependencyGraph(
        dagPath.node(),
        om.MFn.kSkinClusterFilter,
        om.MItDependencyGraph.kUpstream,
        om.MItDependencyGraph.kDepthFirst,
        om.MItDependencyGraph.kPlugLevel
    )
    if dgIter.isDone():
        raise RuntimeError("No skinCluster found on {}".format(mesh))
    skinObj = dgIter.currentItem()
    skinFn = oma.MFnSkinCluster(skinObj)
    influences = skinFn.influenceObjects()
    influenceNames = {}
    for index, influence in enumerate(influences):
        influenceNames[om.MFnDagNode(influence).fullPathName()] = index

    jointMap = {}
    for jointA, jointB in jointPairs:
        if jointA not in influenceNames:
            raise RuntimeError("{} is not an influence of {}".format(jointA,mesh))
        if jointB not in influenceNames:
            raise RuntimeError("{} is not an influence of {}".format(jointB,mesh))
        indexA = influenceNames[jointA]
        indexB = influenceNames[jointB]
        jointMap[indexA] = indexB

    sourceIDs = [vertexA for vertexA, vertexB in vertexPairs]
    sourceComponent = (om.MFnSingleIndexedComponent().create(om.MFn.kMeshVertComponent))
    sourceComponentFn = om.MFnSingleIndexedComponent(sourceComponent)
    sourceComponentFn.addElements(sourceIDs)
    sourceWeights, influenceCount = (skinFn.getWeights(dagPath,sourceComponent))
    targetIDs = [vertexB for vertexA, vertexB in vertexPairs]
    targetComponent = (om.MFnSingleIndexedComponent().create(om.MFn.kMeshVertComponent))
    targetComponentFn = om.MFnSingleIndexedComponent(targetComponent)
    targetComponentFn.addElements(targetIDs)
    targetWeights = om.MDoubleArray(len(vertexPairs) * influenceCount,0.0)
    for vertexIndex in range(len(vertexPairs)):
        sourceOffset = (vertexIndex *influenceCount)
        targetOffset = (vertexIndex *influenceCount)
        for influenceA in range(influenceCount):
            weight = sourceWeights[sourceOffset + influenceA]
            if weight == 0.0:
                continue
            influenceB = jointMap.get(influenceA)
            if influenceB is None:
                continue
            targetWeights[targetOffset + influenceB] = weight
    influenceIndices = om.MIntArray(range(influenceCount))
    skinFn.setWeights(dagPath,targetComponent,influenceIndices,targetWeights,False)
    print("Mirrored skin: {} vertices".format(len(vertexPairs)))


def GetSymmetryPlaneFromPairs(mesh, pairs):
    if len(pairs) != 3:
        raise ValueError("Exactly 3 vertex pairs are required.")
    sel = om.MSelectionList()
    sel.add(mesh)
    dagPath = sel.getDagPath(0)
    fnMesh = om.MFnMesh(dagPath)
    midpoints = []
    for vertexA, vertexB in pairs:
        pointA = fnMesh.getPoint(vertexA,om.MSpace.kWorld)
        pointB = fnMesh.getPoint(vertexB,om.MSpace.kWorld)
        midpoint = om.MPoint((pointA.x + pointB.x) * 0.5,(pointA.y + pointB.y) * 0.5,(pointA.z + pointB.z) * 0.5)
        midpoints.append(midpoint)
    p0 = midpoints[0]
    p1 = midpoints[1]
    p2 = midpoints[2]
    v1 = p1 - p0
    v2 = p2 - p0
    normal = v1 ^ v2
    if normal.length() < 1e-8:
        raise ValueError(
            "The 3 midpoint positions are collinear. "
            "Cannot determine symmetry plane."
        )
    normal.normalize()
    return p0, normal

def MirrorPointByPlane(point, planePoint, planeNormal):
    vector = point - planePoint
    distance = vector * planeNormal
    return point - (planeNormal * (2.0 * distance))

def MirrorVertexPositionsByPairs(mesh,pairs):
    if not pairs:
        return
    planePoint, planeNormal = (GetSymmetryPlaneFromPairs(mesh,pairs[:3]))
    sel = om.MSelectionList()
    sel.add(mesh)
    dagPath = sel.getDagPath(0)
    fnMesh = om.MFnMesh(dagPath)
    for vertexA, vertexB in pairs:
        pointA = fnMesh.getPoint(vertexA,om.MSpace.kWorld)
        pointB = MirrorPointByPlane(pointA,planePoint,planeNormal)
        fnMesh.setPoint(vertexB,pointB,om.MSpace.kWorld)
    fnMesh.updateSurface()
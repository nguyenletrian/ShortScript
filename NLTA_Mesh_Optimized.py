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


def ShowQuardraw(*arr):
    cmds.lockNode("initialShadingGroup", lock=False, lockUnpublished=False)

def GetVertexsSelected(*arr):
    sel = cmds.ls(sl=True)
    if not sel:
        return []
    verts = cmds.polyListComponentConversion(sel, toVertex=True)
    return cmds.ls(verts, fl=True)

def GetMesh(*arr):
    selection = cmds.ls(sl=True, fl=True)
    return list(dict.fromkeys(s.split(".")[0] for s in selection))


def JointPos(j):
    return om.MVector(cmds.xform(j, q=True, ws=True, t=True))

def GetID(component):
    if isinstance(component, (int, float)):
        return(component)
    else:
        return(
            int(component.split("[")[-1].replace("]", ""))
        )


def GetMeshData(mesh):
    dag = NLTA_OpenMaya.GetDagPath(mesh)
    return dag, om.MFnMesh(dag)

def GetMeshFn(mesh):
    dagPath = NLTA_OpenMaya.GetDagPath(mesh)
    return om.MFnMesh(dagPath)


def GetVertexIterator(mesh):
    dagPath = NLTA_OpenMaya.GetDagPath(mesh)
    return om.MItMeshVertex(dagPath)


def GetEdgeIterator(mesh):
    dagPath = NLTA_OpenMaya.GetDagPath(mesh)
    return om.MItMeshEdge(dagPath)


def EdgeDirection(mesh, edgeIndex):
    edgeIt = GetEdgeIterator(mesh)
    edgeIt.setIndex(GetID(edgeIndex))
    p1 = edgeIt.point(0, om.MSpace.kWorld)
    p2 = edgeIt.point(1, om.MSpace.kWorld)
    return om.MVector(p2 - p1).normal()


def CheckEdgeBorder(mesh, edgeId):
    edgeIt = GetEdgeIterator(mesh)
    edgeIt.setIndex(GetID(edgeId))
    return edgeIt.onBoundary()


def VertexFromEdges(mesh, edges):
    dag = GetMeshData(mesh)["dag"]
    edge_it = om.MItMeshEdge(dag)
    vertex_ids = set()

    for edge in edges:
        edge_it.setIndex(GetID(edge))
        vertex_ids.add(edge_it.vertexId(0))
        vertex_ids.add(edge_it.vertexId(1))

    return ["{}.vtx[{}]".format(mesh, vertex_id) for vertex_id in vertex_ids]


def GetConnectedEdges(mesh, vertex_index):
    dag = GetMeshData(mesh)["dag"]
    vertex_it = om.MItMeshVertex(dag)
    vertex_it.setIndex(vertex_index)
    return vertex_it.getConnectedEdges()


def EdgeCenter(mesh, edgeId):
    edgeIt = GetEdgeIterator(mesh)
    edgeIt.setIndex(GetID(edgeId))
    p1 = om.MVector(edgeIt.point(0, om.MSpace.kWorld))
    p2 = om.MVector(edgeIt.point(1, om.MSpace.kWorld))
    return (p1 + p2) * 0.5


def GetEdgeRing(mesh, start_edge):
    edge_ids = cmds.polySelect(
        mesh,
        edgeRing=GetID(start_edge),
        noSelection=True
    )

    if not edge_ids:
        return []

    return ["{}.e[{}]".format(mesh, edge_id) for edge_id in edge_ids]


def VertexFromEdges(mesh, edges):
    dag = GetMeshData(mesh)["dag"]
    edge_it = om.MItMeshEdge(dag)
    vertex_ids = set()

    for edge in edges:
        edge_it.setIndex(GetID(edge))
        vertex_ids.add(edge_it.vertexId(0))
        vertex_ids.add(edge_it.vertexId(1))

    return ["{}.vtx[{}]".format(mesh, vertex_id) for vertex_id in vertex_ids]


def GetConnectedEdges(mesh, vertex_index):
    dag = GetMeshData(mesh)["dag"]
    vertex_it = om.MItMeshVertex(dag)
    vertex_it.setIndex(vertex_index)
    return vertex_it.getConnectedEdges()





def GetFarthestEdge(mesh, baseEdge, edges):
    baseId = GetID(baseEdge)
    edgeIt = GetEdgeIterator(mesh)

    edgeIt.setIndex(baseId)
    p1 = om.MVector(edgeIt.point(0, om.MSpace.kWorld))
    p2 = om.MVector(edgeIt.point(1, om.MSpace.kWorld))
    baseCenter = (p1 + p2) * 0.5

    maxDistance = -1.0
    farEdge = None

    for edge in edges:
        edgeId = GetID(edge)
        edgeIt.setIndex(edgeId)

        p1 = om.MVector(edgeIt.point(0, om.MSpace.kWorld))
        p2 = om.MVector(edgeIt.point(1, om.MSpace.kWorld))
        center = (p1 + p2) * 0.5

        distance = (center - baseCenter).lengthSquared()

        if distance > maxDistance:
            maxDistance = distance
            farEdge = edge

    return farEdge


def GetClosestEdge(mesh, edges, joint):
    jointPos = JointPos(joint)
    edgeIt = GetEdgeIterator(mesh)

    minDistance = float("inf")
    closestEdge = None

    for edge in edges:
        edgeId = GetID(edge)
        edgeIt.setIndex(edgeId)

        p1 = om.MVector(edgeIt.point(0, om.MSpace.kWorld))
        p2 = om.MVector(edgeIt.point(1, om.MSpace.kWorld))
        center = (p1 + p2) * 0.5

        distance = (center - jointPos).lengthSquared()

        if distance < minDistance:
            minDistance = distance
            closestEdge = edge

    return closestEdge

def GetFarthestVertex(mesh, verts, joint):
    jointPos = JointPos(joint)
    points = GetMeshFn(mesh).getPoints(om.MSpace.kWorld)
    maxDistance = -1.0
    farthestVert = None
    for vert in verts:
        vertexId = GetID(vert)
        distance = (points[vertexId] - jointPos).lengthSquared()
        if distance > maxDistance:
            maxDistance = distance
            farthestVert = vert

    return farthestVert


def CheckEdgeLoopClosed(mesh, edges):
    edgeIds = [GetID(edge) for edge in edges]
    meshFn = GetMeshFn(mesh)
    vertexCount = {}

    for edgeId in edgeIds:
        v0, v1 = meshFn.getEdgeVertices(edgeId)
        vertexCount[v0] = vertexCount.get(v0, 0) + 1
        vertexCount[v1] = vertexCount.get(v1, 0) + 1

    return all(count == 2 for count in vertexCount.values())


def GetPerpEdge(v1, v2, threshold=0.25):
    mesh = v1.split(".")[0]
    vertexId = GetID(v1)
    targetId = GetID(v2)

    meshFn = GetMeshFn(mesh)
    points = meshFn.getPoints(om.MSpace.kWorld)

    p1 = om.MVector(points[vertexId])
    p2 = om.MVector(points[targetId])

    direction = p2 - p1

    if direction.lengthSquared() == 0:
        return None

    direction.normalize()

    vertIt = GetVertexIterator(mesh)
    vertIt.setIndex(vertexId)

    bestEdge = None
    bestScore = float("inf")

    for edgeId in vertIt.getConnectedEdges():
        vA, vB = meshFn.getEdgeVertices(edgeId)
        otherId = vB if vA == vertexId else vA

        if otherId == targetId:
            continue

        vector = om.MVector(points[otherId]) - p1

        if vector.lengthSquared() == 0:
            continue

        vector.normalize()

        score = abs(direction * vector)

        if score < bestScore:
            bestScore = score
            bestEdge = edgeId

    if bestScore > threshold:
        return None

    return "{}.e[{}]".format(mesh, bestEdge)

def EdgeLoopToVerts(edge):
    mesh = edge.split(".e[")[0]
    edgeId = GetID(edge)
    edgeIds = cmds.polySelect(
        mesh,
        edgeLoop=edgeId,
        noSelection=True
    )

    if not edgeIds:
        return []

    meshFn = GetMeshFn(mesh)
    vertices = set()

    for edgeId in edgeIds:
        v0, v1 = meshFn.getEdgeVertices(edgeId)
        vertices.add(v0)
        vertices.add(v1)

    return [
        "{}.vtx[{}]".format(mesh, vertexId)
        for vertexId in sorted(vertices)
    ]


def EdgesToVerts(edges):
    if not edges:
        return []

    if isinstance(edges, str):
        edges = [edges]

    mesh = edges[0].split(".")[0]
    meshFn = GetMeshFn(mesh)
    vertices = set()

    for edge in edges:
        edgeId = GetID(edge)
        v0, v1 = meshFn.getEdgeVertices(edgeId)
        vertices.add(v0)
        vertices.add(v1)

    return [
        "{}.vtx[{}]".format(mesh, vertexId)
        for vertexId in sorted(vertices)
    ]


def GetConnectVerts(v, vertSet):
    mesh = v.split(".")[0]
    vertexId = GetID(v)
    vertSetIds = {GetID(vertex) for vertex in vertSet}

    meshFn = GetMeshFn(mesh)
    vertIt = GetVertexIterator(mesh)
    vertIt.setIndex(vertexId)

    result = []

    for edgeId in vertIt.getConnectedEdges():
        v0, v1 = meshFn.getEdgeVertices(edgeId)
        otherId = v1 if v0 == vertexId else v0

        if otherId in vertSetIds:
            result.append((
                v,
                "{}.vtx[{}]".format(mesh, otherId),
                "{}.e[{}]".format(mesh, edgeId)
            ))

    return result


def GetJointAxis(joint):
    matrix = cmds.xform(joint, q=True, ws=True, m=True)
    return om.MVector(matrix[0], matrix[1], matrix[2]).normal()


def GetJointEdge(mesh, joint, vertex_index):
    return GetBestEdgeByAxis(
        mesh,
        joint,
        vertex_index,
        perpendicular=False
    )


def GetJointEdgeLoop(mesh, joint, vtxIndex):
    edge_id = GetJointEdge(mesh, joint, vtxIndex)

    if edge_id is None:
        cmds.warning("No edge found")
        return []

    return GetEdgeLoop("{}.e[{}]".format(mesh, edge_id))


def GetClosestJoints(targetJoint, joints, count=1):
    result = []

    for joint in joints:
        if joint == targetJoint:
            continue

        distance = NLTA_General.GetDistance(targetJoint, joint)
        result.append((joint, distance))

    result.sort(key=lambda item: item[1])
    return result[:count]
    

def GetPerpendicularEdge(mesh, joint, vertex_index):
    return GetBestEdgeByAxis(
        mesh,
        joint,
        vertex_index,
        perpendicular=True
    )

def GetPerpendicularEdgeLoop(mesh, joint, vtxIndex):
    edge_id = GetPerpendicularEdge(mesh, joint, vtxIndex)

    if edge_id is None:
        cmds.warning("No edge found")
        return []

    return GetEdgeLoop("{}.e[{}]".format(mesh, edge_id))


def GetTwoClosestJoints(targetJoint, joints):
    return GetClosestJoints(targetJoint, joints, 2)


def GetClosestJoint(targetJoint, joints):
    return GetClosestJoints(targetJoint, joints, 1)


def GetBestEdgeByAxis(mesh, joint, vertex_index, perpendicular=False):
    dag = GetMeshData(mesh)["dag"]
    joint_axis = GetJointAxis(joint)
    edge_it = om.MItMeshEdge(dag)
    edges = GetConnectedEdges(mesh, vertex_index)

    best_edge = None
    best_value = float("inf") if perpendicular else -1.0

    for edge_id in edges:
        edge_it.setIndex(edge_id)

        p1 = om.MVector(edge_it.point(0, om.MSpace.kWorld))
        p2 = om.MVector(edge_it.point(1, om.MSpace.kWorld))
        direction = (p2 - p1).normal()
        dot = abs(direction * joint_axis)

        if perpendicular:
            if dot < best_value:
                best_value = dot
                best_edge = edge_id
        elif dot > best_value:
            best_value = dot
            best_edge = edge_id

    return best_edge


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

    return ["{}.e[{}]".format(mesh, edgeId) for edgeId in edges]


def CheckEdgesBetween(mesh, edgeSource, edges):
    sourceId = GetID(edgeSource)

    for edge in edges:
        targetId = GetID(edge)
        result = cmds.polySelect(
            mesh,
            edgeRingPath=(sourceId, targetId),
            noSelection=True
        )

        if result:
            return edge

    return []


def EdgeRatioBetweenJoints(mesh, edgeId, jointA, jointB):
    pA = JointPos(jointA)
    pB = JointPos(jointB)
    edgeCenter = EdgeCenter(mesh, edgeId)

    boneVector = pB - pA
    edgeVector = edgeCenter - pA
    lengthSquared = boneVector.lengthSquared()

    if lengthSquared == 0:
        return 0.0

    ratio = (edgeVector * boneVector) / lengthSquared
    return max(0.0, min(1.0, ratio))


def EdgeRatioBetweenEdges(mesh, edgeMid, edgeA, edgeB):
    pA = EdgeCenter(mesh, edgeA)
    pB = EdgeCenter(mesh, edgeB)
    pC = EdgeCenter(mesh, edgeMid)

    vectorAB = pB - pA
    vectorAC = pC - pA
    lengthSquared = vectorAB.lengthSquared()

    if lengthSquared == 0:
        return 0.0

    ratio = (vectorAC * vectorAB) / lengthSquared
    return max(0.0, min(1.0, ratio))


def GetMeshComponents(mesh):
    data = GetMeshData(mesh)
    meshFn = om.MFnMesh(data["dag"])

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
                if neighbor in visited:
                    continue

                visited.add(neighbor)
                stack.append(neighbor)

        components.append(component)

    return components

def SelectVerticesWithinRadius(mesh, joint, verts, radius):
    jointPos = JointPos(joint)
    meshFn = GetMeshFn(mesh)
    points = meshFn.getPoints(om.MSpace.kWorld)
    radiusSquared = radius * radius
    result = []

    for vert in verts:
        vertexId = GetID(vert)
        delta = points[vertexId] - jointPos

        if delta.lengthSquared() <= radiusSquared:
            result.append(vert)

    return result


def SelectLoopRegion(mesh, joint, joints, verts):
    closest = GetClosestJoints(joint, joints, 2)

    if len(closest) < 2:
        cmds.warning("Need at least 2 other joints")
        return []

    radius = min(closest[0][1], closest[1][1]) * 0.7
    return SelectVerticesWithinRadius(mesh, joint, verts, radius)


def GetIntersectVerts(meshA, meshB, threshold, *arr):
    cpm = cmds.createNode("closestPointOnMesh")

    try:
        shapeB = cmds.listRelatives(
            meshB,
            shapes=True,
            fullPath=True
        )[0]

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

        thresholdSquared = threshold * threshold
        result = []

        for vert in verts:
            position = cmds.pointPosition(
                vert,
                world=True
            )

            cmds.setAttr(
                "{}.inPosition".format(cpm),
                *position,
                type="double3"
            )

            closest = cmds.getAttr(
                "{}.position".format(cpm)
            )[0]

            distanceSquared = sum(
                (position[i] - closest[i]) ** 2
                for i in range(3)
            )

            if distanceSquared <= thresholdSquared:
                result.append(vert)

        return result

    finally:
        if cmds.objExists(cpm):
            cmds.delete(cpm)


def GetVertexBetweenParentChild(data, *arr):
    mesh = data["mesh"]
    source = data["source"]
    destination = data["destination"]

    closestVertex = GetClosestVertex(
        mesh,
        source
    )

    edgeLoop = GetJointEdgeLoop(
        mesh,
        source,
        closestVertex
    )

    sourceEdge = GetClosestEdge(
        mesh,
        edgeLoop,
        source
    )

    destinationEdge = GetClosestEdge(
        mesh,
        edgeLoop,
        destination
    )

    edgeBetween = EdgesBetween(
        mesh,
        sourceEdge,
        destinationEdge
    )

    cmds.select(edgeBetween)


def GetVertRatioBetweenJoints(data, *arr):
    vert = data["vert"]
    joints = data["joints"]

    if len(joints) != 2:
        cmds.error("Need exactly 2 joints")

    joint1, joint2 = joints

    dist1 = NLTA_General.GetDistance(
        vert,
        joint1
    )

    dist2 = NLTA_General.GetDistance(
        vert,
        joint2
    )

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



def GetClosestJoints(targetJoint, joints, count=1):
    distances = []

    for joint in joints:
        if joint == targetJoint:
            continue

        distance = NLTA_General.GetDistance(targetJoint, joint)
        distances.append((joint, distance))

    distances.sort(key=lambda item: item[1])
    return distances[:count]




def GetClosestVertex(mesh, joint):
    _, mesh_fn = GetMeshData(mesh)
    joint_pos = om.MPoint(cmds.xform(joint, q=True, ws=True, t=True))
    closest_point, _ = mesh_fn.getClosestPoint(joint_pos, om.MSpace.kWorld)
    vertices = mesh_fn.getPoints(om.MSpace.kWorld)

    closest_index = -1
    min_dist = float("inf")

    for i, vertex in enumerate(vertices):
        dist = (vertex - closest_point) * (vertex - closest_point)
        if dist < min_dist:
            min_dist = dist
            closest_index = i

    return closest_index





def GetEdgeLoop(startEdge, *arr):
    mesh = startEdge.split(".")[0] if isinstance(startEdge, str) else None
    edgeId = GetID(startEdge)

    if mesh is None:
        cmds.error("startEdge must be a mesh edge component.")

    data = GetMeshData(mesh)
    edgeIt = om.MItMeshEdge(data["dag"])
    vertIt = om.MItMeshVertex(data["dag"])

    visited = set()

    def Walk(edgeId, fromVertex):
        result = []

        while True:
            if edgeId in visited:
                break

            visited.add(edgeId)
            result.append(edgeId)

            edgeIt.setIndex(edgeId)

            v0 = edgeIt.vertexId(0)
            v1 = edgeIt.vertexId(1)
            nextVertex = v1 if v0 == fromVertex else v0

            vertIt.setIndex(nextVertex)
            connectedEdges = vertIt.getConnectedEdges()

            if vertIt.onBoundary():
                candidates = []

                for edge in connectedEdges:
                    if edge == edgeId:
                        continue

                    edgeIt.setIndex(edge)

                    if edgeIt.onBoundary():
                        candidates.append(edge)

                if len(candidates) != 1:
                    break

                nextEdge = candidates[0]

            else:
                if len(connectedEdges) != 4:
                    break

                nextEdge = None
                currentFaces = set(edgeIt.getConnectedFaces())

                for edge in connectedEdges:
                    if edge == edgeId:
                        continue

                    edgeIt.setIndex(edge)

                    if edgeIt.onBoundary():
                        continue

                    commonFaces = currentFaces & set(
                        edgeIt.getConnectedFaces()
                    )

                    if not commonFaces:
                        nextEdge = edge
                        break

                if nextEdge is None:
                    break

            edgeId = nextEdge
            fromVertex = nextVertex

        return result

    edgeIt.setIndex(edgeId)

    v0 = edgeIt.vertexId(0)
    v1 = edgeIt.vertexId(1)

    loop = []

    loop.extend(reversed(Walk(edgeId, v0)))

    visited.discard(edgeId)

    loop.extend(Walk(edgeId, v1))

    result = []
    seen = set()

    for edge in loop:
        if edge in seen:
            continue

        seen.add(edge)
        result.append("{}.e[{}]".format(mesh, edge))

    return result





def SortCircularJoints(joints, clockwise=False):
    if len(joints) < 3:
        return joints[:]

    positions = {
        joint: om.MVector(cmds.xform(joint, q=True, ws=True, t=True))
        for joint in joints
    }

    center = sum(positions.values(), om.MVector())
    center /= len(joints)

    maxDistance = -1.0
    xAxis = None

    for i, jointA in enumerate(joints):
        for jointB in joints[i + 1:]:
            vector = positions[jointA] - positions[jointB]
            distance = vector.lengthSquared()

            if distance > maxDistance:
                maxDistance = distance
                xAxis = vector.normal()

    normal = om.MVector()
    vectors = [positions[joint] - center for joint in joints]

    for i, vectorA in enumerate(vectors):
        for vectorB in vectors[i + 1:]:
            normal += vectorA ^ vectorB

    if normal.length() < 1e-6:
        cmds.warning("Cannot compute normal.")
        return joints[:]

    normal.normalize()

    yAxis = normal ^ xAxis
    yAxis.normalize()

    result = []

    for joint in joints:
        vector = positions[joint] - center
        x = vector * xAxis
        y = vector * yAxis
        angle = math.atan2(y, x)
        result.append((angle, joint))

    result.sort(key=lambda item: item[0], reverse=clockwise)

    return [joint for _, joint in result]


#########################

def Normalize(vector):
    length = math.sqrt(sum(value * value for value in vector))
    return vector if length == 0 else [value / length for value in vector]

def Dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]

def GetPos(vertex):
    return cmds.xform(vertex, q=True, ws=True, t=True)






def ListToPerVerts(verts, threshold=9999):
    returnData = {}

    for vertex in verts:
        connections = GetConnectVerts(vertex, verts)

        for source, target, _ in connections:
            edge = GetPerpEdge(source, target, threshold)

            if edge is None:
                continue

            edgeLoopVerts = EdgeLoopToVerts(edge)
            returnData[vertex] = edgeLoopVerts

    return returnData







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

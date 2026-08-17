"""Optimized companion for NLTA_Mesh.py.

Keeps the original NLTA_Mesh.py untouched and overrides the hottest mesh/skin
helpers with Maya API based implementations. Public function names and the
existing argument/return conventions are kept where practical.

Usage in Maya:
    import NLTA_Mesh_Optimized as NLTA_Mesh

This module imports the original helpers first, so functions that are not
optimized here remain available exactly as before.
"""

import math
import maya.cmds as cmds
import maya.api.OpenMaya as om
import maya.api.OpenMayaAnim as oma

from NLTA_Mesh import *


def _GetDagPath(mesh):
    sel = om.MSelectionList()
    sel.add(mesh)
    dag = sel.getDagPath(0)
    if dag.apiType() != om.MFn.kMesh:
        dag.extendToShape()
    return dag


def _GetMeshFn(mesh):
    return om.MFnMesh(_GetDagPath(mesh))


def _GetSkinFn(mesh):
    dag = _GetDagPath(mesh)
    it = om.MItDependencyGraph(dag.node(), om.MFn.kSkinClusterFilter,
                               om.MItDependencyGraph.kUpstream,
                               om.MItDependencyGraph.kDepthFirst,
                               om.MItDependencyGraph.kPlugLevel)
    if it.isDone():
        raise RuntimeError("No skinCluster found on {}".format(mesh))
    return dag, oma.MFnSkinCluster(it.currentItem())


def GetClosestVertex(mesh, joint):
    """Return the vertex nearest to the closest point on the mesh to joint."""
    fn = _GetMeshFn(mesh)
    point = om.MPoint(cmds.xform(joint, q=True, ws=True, t=True))
    closest, _ = fn.getClosestPoint(point, om.MSpace.kWorld)
    points = fn.getPoints(om.MSpace.kWorld)
    best_id = -1
    best_dist = float("inf")
    for i, p in enumerate(points):
        d = (p - closest).lengthSquared()
        if d < best_dist:
            best_dist = d
            best_id = i
    return best_id


def SelectVerticesWithinRadius(mesh, joint, verts, radius):
    """Avoid one cmds.pointPosition call per vertex."""
    center = om.MVector(cmds.xform(joint, q=True, ws=True, t=True))
    radius_sq = radius * radius
    fn = _GetMeshFn(mesh)
    points = fn.getPoints(om.MSpace.kWorld)
    result = []
    for vert in verts:
        index = GetID(vert)
        if index < 0 or index >= len(points):
            continue
        if (om.MVector(points[index]) - center).lengthSquared() <= radius_sq:
            result.append(vert)
    return result


def GetClosestEdge(mesh, edges, joint):
    center = om.MVector(cmds.xform(joint, q=True, ws=True, t=True))
    fn = _GetMeshFn(mesh)
    points = fn.getPoints(om.MSpace.kWorld)
    best = None
    best_dist = float("inf")
    for edge in edges:
        eid = GetID(edge)
        v0, v1 = fn.getEdgeVertices(eid)
        edge_center = (om.MVector(points[v0]) + om.MVector(points[v1])) * 0.5
        dist = (edge_center - center).lengthSquared()
        if dist < best_dist:
            best_dist = dist
            best = edge
    return best


def GetFarthestEdge(mesh, baseEdge, edges):
    fn = _GetMeshFn(mesh)
    points = fn.getPoints(om.MSpace.kWorld)
    base_id = GetID(baseEdge)
    v0, v1 = fn.getEdgeVertices(base_id)
    base_center = (om.MVector(points[v0]) + om.MVector(points[v1])) * 0.5
    best = None
    best_dist = -1.0
    for edge in edges:
        eid = GetID(edge)
        a, b = fn.getEdgeVertices(eid)
        center = (om.MVector(points[a]) + om.MVector(points[b])) * 0.5
        dist = (center - base_center).lengthSquared()
        if dist > best_dist:
            best_dist = dist
            best = edge
    return best


def GetFarthestVertex(mesh, verts, joint):
    center = om.MVector(cmds.xform(joint, q=True, ws=True, t=True))
    points = _GetMeshFn(mesh).getPoints(om.MSpace.kWorld)
    best = None
    best_dist = -1.0
    for vert in verts:
        index = GetID(vert)
        if index < 0 or index >= len(points):
            continue
        dist = (om.MVector(points[index]) - center).lengthSquared()
        if dist > best_dist:
            best_dist = dist
            best = vert
    return best


def GetIntersectVerts(meshA, meshB, threshold, *arr):
    """API-only replacement for the per-vertex closestPointOnMesh node loop."""
    fn_a = _GetMeshFn(meshA)
    fn_b = _GetMeshFn(meshB)
    threshold_sq = threshold * threshold
    points_a = fn_a.getPoints(om.MSpace.kWorld)
    result = []
    for index, point in enumerate(points_a):
        closest, _ = fn_b.getClosestPoint(point, om.MSpace.kWorld)
        if (point - closest).lengthSquared() <= threshold_sq:
            result.append("{}.vtx[{}]".format(meshA, index))
    return result


def GetMirrorVertexByUv(vtx, axis="U", tol=0.01):
    """Find a mirrored vertex using one cached UV pass instead of per-vertex cmds calls."""
    mesh = vtx.split(".")[0]
    source_id = GetID(vtx)
    fn = _GetMeshFn(mesh)
    try:
        uv_counts, uv_ids = fn.getAssignedUVs()
        u_values, v_values = fn.getUVs()
    except Exception:
        return None

    vertex_uv = {}
    offset = 0
    for face_id in range(fn.numPolygons):
        face_vertices = fn.getPolygonVertices(face_id)
        count = uv_counts[face_id]
        if not count:
            continue
        for local_index, vertex_id in enumerate(face_vertices):
            if local_index >= count:
                continue
            uv_id = uv_ids[offset + local_index]
            if vertex_id not in vertex_uv:
                vertex_uv[vertex_id] = (u_values[uv_id], v_values[uv_id])
        offset += count

    if source_id not in vertex_uv:
        return None
    u, v = vertex_uv[source_id]
    if axis.upper() == "U":
        target = (1.0 - u, v)
    else:
        target = (u, 1.0 - v)

    best = None
    best_dist = float("inf")
    for vertex_id, uv in vertex_uv.items():
        if vertex_id == source_id:
            continue
        dist = abs(uv[0] - target[0]) + abs(uv[1] - target[1])
        if dist < best_dist:
            best_dist = dist
            best = vertex_id
    if best is None or best_dist > tol:
        return None
    return "{}.vtx[{}]".format(mesh, best)


def CopySkinByVertexPairs(meshA, meshB, pairs):
    """Copy skin weights using dictionary based influence matching."""
    if not pairs:
        return
    dag_a, skin_a = _GetSkinFn(meshA)
    dag_b, skin_b = _GetSkinFn(meshB)
    influences_a = skin_a.influenceObjects()
    influences_b = skin_b.influenceObjects()
    names_b = {om.MFnDagNode(obj).fullPathName(): i for i, obj in enumerate(influences_b)}
    influence_map = {}
    for i, obj in enumerate(influences_a):
        name = om.MFnDagNode(obj).fullPathName()
        if name not in names_b:
            raise RuntimeError("Influence '{}' from {} does not exist on {}.".format(name, meshA, meshB))
        influence_map[i] = names_b[name]

    source_ids = [a for a, _ in pairs]
    target_ids = [b for _, b in pairs]
    source_comp = om.MFnSingleIndexedComponent().create(om.MFn.kMeshVertComponent)
    om.MFnSingleIndexedComponent(source_comp).addElements(source_ids)
    target_comp = om.MFnSingleIndexedComponent().create(om.MFn.kMeshVertComponent)
    om.MFnSingleIndexedComponent(target_comp).addElements(target_ids)
    weights_a, influence_count_a = skin_a.getWeights(dag_a, source_comp)
    influence_count_b = len(influences_b)
    weights_b = [0.0] * (len(pairs) * influence_count_b)

    for row in range(len(pairs)):
        source_offset = row * influence_count_a
        target_offset = row * influence_count_b
        for source_index in range(influence_count_a):
            weight = weights_a[source_offset + source_index]
            if weight:
                weights_b[target_offset + influence_map[source_index]] = weight

    skin_b.setWeights(dag_b, target_comp, om.MIntArray(range(influence_count_b)), om.MDoubleArray(weights_b), False)
    print("Copied skin weights: {} vertices".format(len(pairs)))


def FindMirrorJointPairs(joints, axis=0, tolerance=0.001):
    """Match mirrored joints using a spatial hash instead of an O(n^2) scan."""
    if not joints:
        return []
    cell = max(float(tolerance), 1e-8)
    positions = {}
    for joint in joints:
        dag = om.MSelectionList().add(joint).getDagPath(0)
        p = om.MTransformationMatrix(dag.inclusiveMatrix()).translation(om.MSpace.kWorld)
        positions[joint] = (p.x, p.y, p.z)

    def key(pos):
        return tuple(int(math.floor(v / cell)) for v in pos)

    buckets = {}
    for joint, pos in positions.items():
        buckets.setdefault(key(pos), []).append(joint)

    tolerance_sq = tolerance * tolerance
    used = set()
    result = []
    for joint_a, pos_a in positions.items():
        if joint_a in used:
            continue
        if abs(pos_a[axis]) <= tolerance:
            result.append((joint_a, joint_a))
            used.add(joint_a)
            continue
        mirrored = list(pos_a)
        mirrored[axis] *= -1.0
        base = key(mirrored)
        best = None
        best_dist = float("inf")
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    for joint_b in buckets.get((base[0] + dx, base[1] + dy, base[2] + dz), ()): 
                        if joint_b == joint_a or joint_b in used:
                            continue
                        pos_b = positions[joint_b]
                        d = sum((mirrored[i] - pos_b[i]) ** 2 for i in range(3))
                        if d <= tolerance_sq and d < best_dist:
                            best = joint_b
                            best_dist = d
        if best is not None:
            result.append((joint_a, best))
            used.add(joint_a)
            used.add(best)
    return result


def MirrorVertexPositionsByPairs(mesh, pairs):
    if not pairs:
        return
    plane_point, plane_normal = GetSymmetryPlaneFromPairs(mesh, pairs[:3])
    fn = _GetMeshFn(mesh)
    points = fn.getPoints(om.MSpace.kWorld)
    changed = False
    for vertex_a, vertex_b in pairs:
        point = points[vertex_a]
        vector = point - plane_point
        distance = vector * plane_normal
        points[vertex_b] = point - plane_normal * (2.0 * distance)
        changed = True
    if changed:
        fn.setPoints(points, om.MSpace.kWorld)
        fn.updateSurface()

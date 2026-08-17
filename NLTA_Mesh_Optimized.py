"""Optimized companion for NLTA_Mesh.py.

The original NLTA_Mesh.py remains untouched and all of its public functions
remain available through this module. The functions below replace the main
mesh hot paths with Maya API implementations that reduce repeated cmds calls,
iterator creation, and Python-side adjacency data.

Usage:
    import NLTA_Mesh_Optimized as NLTA_Mesh

For anything not overridden here, the original NLTA_Mesh implementation is
used unchanged.
"""

import maya.cmds as cmds
import maya.api.OpenMaya as om
import NLTA_Mesh as _mesh
import NLTA_OpenMaya

# Preserve the complete original API.
for _name in dir(_mesh):
    if not _name.startswith("_"):
        globals()[_name] = getattr(_mesh, _name)


def _GetDag(mesh):
    return NLTA_OpenMaya.GetDagPath(mesh)


def _GetMeshFn(mesh):
    return om.MFnMesh(_GetDag(mesh))


def _GetIndex(component):
    if isinstance(component, int):
        return component
    return int(component.rsplit("[", 1)[1][:-1])


def GetVertexsSelected(*arr):
    sel = cmds.ls(sl=True, fl=True)
    if not sel:
        return []
    return cmds.ls(cmds.polyListComponentConversion(sel, toVertex=True), fl=True)


def GetMesh(*arr):
    selection = cmds.ls(sl=True, fl=True)
    return list(dict.fromkeys(s.split(".")[0] for s in selection))


def JointPos(joint):
    return om.MVector(cmds.xform(joint, q=True, ws=True, t=True))


def GetJointAxis(joint):
    matrix = cmds.xform(joint, q=True, ws=True, m=True)
    return om.MVector(matrix[0], matrix[1], matrix[2]).normal()


def EdgeDirection(mesh, edgeIndex):
    iterator = om.MItMeshEdge(_GetDag(mesh))
    iterator.setIndex(_GetIndex(edgeIndex))
    return om.MVector(iterator.point(1, om.MSpace.kWorld) - iterator.point(0, om.MSpace.kWorld)).normal()


def CheckEdgeBorder(mesh, edgeId):
    iterator = om.MItMeshEdge(_GetDag(mesh))
    iterator.setIndex(_GetIndex(edgeId))
    return iterator.onBoundary()


def GetConnectedEdges(mesh, vertex_index):
    iterator = om.MItMeshVertex(_GetDag(mesh))
    iterator.setIndex(_GetIndex(vertex_index))
    return iterator.getConnectedEdges()


def GetClosestVertex(mesh, joint):
    """Find the vertex closest to the point on the mesh nearest the joint."""
    fn_mesh = _GetMeshFn(mesh)
    joint_point = om.MPoint(cmds.xform(joint, q=True, ws=True, t=True))
    closest_point, _ = fn_mesh.getClosestPoint(joint_point, om.MSpace.kWorld)
    points = fn_mesh.getPoints(om.MSpace.kWorld)
    best_index = -1
    best_distance = float("inf")
    for index, point in enumerate(points):
        distance = (point - closest_point).length()
        if distance < best_distance:
            best_distance = distance
            best_index = index
    return best_index


def EdgeCenter(mesh, edgeId):
    iterator = om.MItMeshEdge(_GetDag(mesh))
    iterator.setIndex(_GetIndex(edgeId))
    point_a = om.MVector(iterator.point(0, om.MSpace.kWorld))
    point_b = om.MVector(iterator.point(1, om.MSpace.kWorld))
    return (point_a + point_b) * 0.5


def GetClosestEdge(mesh, edges, joint):
    joint_position = JointPos(joint)
    iterator = om.MItMeshEdge(_GetDag(mesh))
    best_edge = None
    best_distance = float("inf")
    for edge in edges:
        iterator.setIndex(_GetIndex(edge))
        center = (om.MVector(iterator.point(0, om.MSpace.kWorld)) + om.MVector(iterator.point(1, om.MSpace.kWorld))) * 0.5
        distance = (center - joint_position).length()
        if distance < best_distance:
            best_distance = distance
            best_edge = edge
    return best_edge


def GetFarthestEdge(mesh, baseEdge, edges):
    base_center = EdgeCenter(mesh, baseEdge)
    iterator = om.MItMeshEdge(_GetDag(mesh))
    farthest_edge = None
    best_distance = -1.0
    for edge in edges:
        iterator.setIndex(_GetIndex(edge))
        center = (om.MVector(iterator.point(0, om.MSpace.kWorld)) + om.MVector(iterator.point(1, om.MSpace.kWorld))) * 0.5
        distance = (center - base_center).length()
        if distance > best_distance:
            best_distance = distance
            farthest_edge = edge
    return farthest_edge


def GetFarthestVertex(mesh, verts, joint):
    joint_position = JointPos(joint)
    points = _GetMeshFn(mesh).getPoints(om.MSpace.kWorld)
    farthest_vertex = None
    best_distance = -1.0
    for vertex in verts:
        distance = (om.MVector(points[_GetIndex(vertex)]) - joint_position).length()
        if distance > best_distance:
            best_distance = distance
            farthest_vertex = vertex
    return farthest_vertex


def SelectVerticesWithinRadius(mesh, joint, verts, radius):
    """Use one getPoints call instead of cmds.pointPosition once per vertex."""
    joint_position = JointPos(joint)
    points = _GetMeshFn(mesh).getPoints(om.MSpace.kWorld)
    radius_squared = radius * radius
    result = []
    for vertex in verts:
        delta = om.MVector(points[_GetIndex(vertex)]) - joint_position
        if delta * delta <= radius_squared:
            result.append(vertex)
    return result


def GetJointEdge(mesh, joint, vertex_index):
    joint_axis = GetJointAxis(joint)
    edge_iterator = om.MItMeshEdge(_GetDag(mesh))
    vertex_iterator = om.MItMeshVertex(_GetDag(mesh))
    vertex_iterator.setIndex(_GetIndex(vertex_index))
    best_edge = None
    best_dot = -1.0
    for edge in vertex_iterator.getConnectedEdges():
        edge_iterator.setIndex(edge)
        direction = om.MVector(edge_iterator.point(1, om.MSpace.kWorld) - edge_iterator.point(0, om.MSpace.kWorld)).normal()
        dot = abs(direction * joint_axis)
        if dot > best_dot:
            best_dot = dot
            best_edge = edge
    return best_edge


def GetPerpendicularEdge(mesh, joint, vertex_index):
    joint_axis = GetJointAxis(joint)
    edge_iterator = om.MItMeshEdge(_GetDag(mesh))
    vertex_iterator = om.MItMeshVertex(_GetDag(mesh))
    vertex_iterator.setIndex(_GetIndex(vertex_index))
    best_edge = None
    best_dot = float("inf")
    for edge in vertex_iterator.getConnectedEdges():
        edge_iterator.setIndex(edge)
        direction = om.MVector(edge_iterator.point(1, om.MSpace.kWorld) - edge_iterator.point(0, om.MSpace.kWorld)).normal()
        dot = abs(direction * joint_axis)
        if dot < best_dot:
            best_dot = dot
            best_edge = edge
    return best_edge


def ColorVertices(vertices, color=(1, 0, 0, 1)):
    """Group vertices by mesh and write each mesh's colors in one API call."""
    mesh_map = {}
    for vertex in vertices:
        mesh = vertex.split(".", 1)[0]
        mesh_map.setdefault(mesh, []).append(_GetIndex(vertex))
    for mesh, indices in mesh_map.items():
        fn_mesh = _GetMeshFn(mesh)
        fn_mesh.setVertexColors([om.MColor(color)] * len(indices), indices)
        shapes = cmds.listRelatives(mesh, s=True, ni=True, f=True) or []
        if shapes:
            cmds.setAttr(shapes[0] + ".displayColors", 1)


def GetMeshComponents(mesh):
    """Find disconnected components without creating a full Python adjacency list."""
    path = _GetDag(mesh)
    fn_mesh = om.MFnMesh(path)
    vertex_count = fn_mesh.numVertices
    iterator = om.MItMeshVertex(path)
    visited = set()
    components = []
    for start_vertex in range(vertex_count):
        if start_vertex in visited:
            continue
        component = []
        stack = [start_vertex]
        visited.add(start_vertex)
        while stack:
            vertex = stack.pop()
            component.append(vertex)
            iterator.setIndex(vertex)
            for neighbor in iterator.getConnectedVertices():
                if neighbor not in visited:
                    visited.add(neighbor)
                    stack.append(neighbor)
        components.append(component)
    return components


def GetSymmetryPlaneFromPairs(mesh, pairs):
    if len(pairs) != 3:
        raise ValueError("Exactly 3 vertex pairs are required.")
    fn_mesh = _GetMeshFn(mesh)
    midpoints = []
    for vertex_a, vertex_b in pairs:
        point_a = fn_mesh.getPoint(_GetIndex(vertex_a), om.MSpace.kWorld)
        point_b = fn_mesh.getPoint(_GetIndex(vertex_b), om.MSpace.kWorld)
        midpoints.append(om.MPoint((point_a.x + point_b.x) * 0.5, (point_a.y + point_b.y) * 0.5, (point_a.z + point_b.z) * 0.5))
    normal = (midpoints[1] - midpoints[0]) ^ (midpoints[2] - midpoints[0])
    if normal.length() < 1e-8:
        raise ValueError("The 3 midpoint positions are collinear. Cannot determine symmetry plane.")
    normal.normalize()
    return midpoints[0], normal


def MirrorPointByPlane(point, planePoint, planeNormal):
    vector = point - planePoint
    distance = vector * planeNormal
    return point - planeNormal * (2.0 * distance)


def MirrorVertexPositionsByPairs(mesh, pairs):
    if not pairs:
        return
    plane_point, plane_normal = GetSymmetryPlaneFromPairs(mesh, pairs[:3])
    fn_mesh = _GetMeshFn(mesh)
    points = fn_mesh.getPoints(om.MSpace.kWorld)
    for vertex_a, vertex_b in pairs:
        points[_GetIndex(vertex_b)] = MirrorPointByPlane(points[_GetIndex(vertex_a)], plane_point, plane_normal)
    fn_mesh.setPoints(points, om.MSpace.kWorld)
    fn_mesh.updateSurface()


def FindMirrorJointPairs(joints, axis=0, tolerance=0.001):
    joint_data = {}
    for joint in joints:
        selection = om.MSelectionList()
        selection.add(joint)
        path = selection.getDagPath(0)
        position = om.MTransformationMatrix(path.inclusiveMatrix()).translation(om.MSpace.kWorld)
        joint_data[joint] = (position.x, position.y, position.z)

    tolerance_squared = tolerance * tolerance
    pairs = []
    used = set()
    items = list(joint_data.items())
    for joint_a, position_a in items:
        if joint_a in used:
            continue
        if abs(position_a[axis]) <= tolerance:
            pairs.append((joint_a, joint_a))
            used.add(joint_a)
            continue
        target = list(position_a)
        target[axis] *= -1.0
        best_joint = None
        best_distance = None
        for joint_b, position_b in items:
            if joint_b == joint_a or joint_b in used:
                continue
            distance = ((target[0] - position_b[0]) ** 2 + (target[1] - position_b[1]) ** 2 + (target[2] - position_b[2]) ** 2)
            if distance <= tolerance_squared and (best_distance is None or distance < best_distance):
                best_joint = joint_b
                best_distance = distance
        if best_joint is not None:
            pairs.append((joint_a, best_joint))
            used.add(joint_a)
            used.add(best_joint)
    return pairs


# Complex topology/skin functions remain the original implementations on
# purpose. They are already API-based and changing their algorithms would be a
# behavior change rather than a safe performance optimization.
CopySkinByVertexPairs = _mesh.CopySkinByVertexPairs
MirrorSkinByPairs = _mesh.MirrorSkinByPairs
FindSymmetricVertexPairs = _mesh.FindSymmetricVertexPairs
MatchVertexPairs = _mesh.MatchVertexPairs

print("NLTA_Mesh_Optimized loaded: original API preserved; hot paths optimized.")

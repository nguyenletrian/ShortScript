import maya.cmds as cmds

def ExtrudeWireRun(valence_limit, offset_val, thickness_val):
    objs = cmds.ls(sl=True)
    if not objs:
        cmds.error("Hãy chọn 1 mesh trước.")
    
    for obj in objs:
        mesh = obj
        verts = cmds.ls(mesh + ".vtx[*]", fl=True)

        target_faces = set()

        # --- Tìm các mặt dựa trên vertex có valence >= valence_limit ---
        for v in verts:
            connected_edges = cmds.polyListComponentConversion(v, toEdge=True)
            connected_edges = cmds.filterExpand(connected_edges, sm=32)
            
            if not connected_edges:
                continue
            
            valence = len(connected_edges)

            if valence >= valence_limit:
                faces = cmds.polyListComponentConversion(v, toFace=True)
                faces = cmds.filterExpand(faces, sm=34)
                
                if faces:
                    for f in faces:
                        target_faces.add(f)

        # --- Chọn mặt ---
        target_faces = list(target_faces)
        if not target_faces:
            cmds.warning("Không có mặt nào có vertex đủ số cạnh yêu cầu.")
            return

        cmds.select(target_faces)

        # --- Extrude 1: Offset ---
        cmds.polyExtrudeFacet(target_faces, offset=offset_val)

        # --- Extrude 2: Thickness ---
        cmds.polyExtrudeFacet(target_faces, thickness=thickness_val)

        print("Extrude hoàn tất.")

def ExtrudeWireUI():
    if cmds.window("ExtrudeWireTool", exists=True):
        cmds.deleteUI("ExtrudeWireTool")
    
    win = cmds.window("ExtrudeWireTool", title="Extrude Wire Tool", widthHeight=(300, 150))
    cmds.columnLayout(adjustableColumn=True, rowSpacing=8)

    cmds.text(label="Số cạnh tối thiểu (valence):")
    valence_txt = cmds.textField(text="5")

    cmds.text(label="Extrude Offset:")
    offset_f = cmds.floatField(value=0.1)

    cmds.text(label="Extrude Thickness:")
    thickness_f = cmds.floatField(value=-0.1)

    # NÚT RUN
    def runTool(*args):
        try:
            valence = int(cmds.textField(valence_txt, q=True, text=True))
            offset = cmds.floatField(offset_f, q=True, value=True)
            thickness = cmds.floatField(thickness_f, q=True, value=True)
            ExtrudeWireRun(valence, offset, thickness)
        except:
            cmds.warning("Giá trị nhập không hợp lệ.")
    cmds.button(label="RUN", height=40, command=runTool)
    cmds.showWindow(win)

ExtrudeWireUI()
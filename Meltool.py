import maya.cmds as cmds
import maya.mel as mel
import json
import os

# JSON PATH
jsonPath = os.path.join(cmds.internalVar(userAppDir=True), "mel_script_buttons.json")
width = 300
print(jsonPath)

if not os.path.exists(jsonPath):
    with open(jsonPath, "w") as f:
        json.dump({}, f, indent=4)

def DeleteButton(name):
    with open(jsonPath, "r") as f:
        data = json.load(f)

    if name in data:
        data.pop(name)

    with open(jsonPath, "w") as f:
        json.dump(data, f, indent=4)

    cmds.inViewMessage(
        amg=f"<span style='color:#f88;'>Deleted: {name}</span>",
        pos='topCenter',
        fade=True
    )
    LoadButtons()

def SaveScript(*args):
    name = cmds.textField("tool_name_field", q=True, text=True)
    script = cmds.scrollField("tool_script_field", q=True, text=True)

    if not name:
        cmds.warning("Vui lòng nhập tên.")
        return
    if not script.strip():
        cmds.warning("Script rỗng.")
        return

    with open(jsonPath, "r") as f:
        data = json.load(f)

    data[name] = script

    with open(jsonPath, "w") as f:
        json.dump(data, f, indent=4)

    cmds.inViewMessage(
        amg=f"<span style='color:#8f8;'>Saved: {name}</span>",
        pos='topCenter',
        fade=True
    )
    LoadButtons()

def LoadButtons(*args):
    children = cmds.rowColumnLayout("buttonList", q=True, ca=True)
    if children:
        for c in children:
            cmds.deleteUI(c)
    with open(jsonPath, "r") as f:
        data = json.load(f)
    for name, script in data.items():
        btn = cmds.button(
            label=name,
            parent="buttonList",
            width=(width - 16) / 2,
            command=lambda x, s=script: mel.eval(s)
        )
        pm = cmds.popupMenu(parent=btn, button=3)
        cmds.menuItem(
            label="Delete",
            parent=pm,
            c=lambda x, n=name: DeleteButton(n)
        )

def melToolUi():
    if cmds.window("melToolWin", exists=True):
        cmds.deleteUI("melToolWin")

    win = cmds.window("melToolWin", title="Mel Script Tool", width=width)
    winContent = cmds.columnLayout()
    
    cmds.rowColumnLayout(nc=2, parent=winContent, rs=[3, 3], width=width)
    cmds.text(label=" Name: ", width=50)
    cmds.textField("tool_name_field", width=(width - 50))
    cmds.text(label=" Script: ")
    cmds.scrollField("tool_script_field", height=120, wordWrap=True)
    cmds.setParent("..")

    cmds.columnLayout()
    cmds.button(
        label="Save",
        h=30,
        width=width,
        bgc=[0.3, 0.5, 0.3],
        command=SaveScript
    )
    cmds.setParent("..")
    
    cmds.rowColumnLayout(width=width)
    cmds.separator(h=10)
    cmds.scrollLayout(h=200, width=width)
    cmds.rowColumnLayout("buttonList", adj=True, nc=2, width=(width - 16))
    cmds.setParent("..")

    cmds.setParent("..")
    cmds.showWindow(win)
    LoadButtons()
    
melToolUi()

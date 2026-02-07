# -*- coding: utf-8 -*-
import maya.cmds as cmds
import os
import sys
import subprocess
import zipfile
import traceback

# ================= CONFIG =================
ROOT_DIR = os.path.join(cmds.internalVar(userAppDir=True), "mel_tools")
SYSTEM_LIB = "SystemLibrary"

WIN_NAME = "MelToolManagerWin"
ADD_WIN = "AddToolWin"

WIDTH = 500
BTN_H = 28

# ================= CORE =================
def ensureRoot():
    if not os.path.exists(ROOT_DIR):
        os.makedirs(ROOT_DIR)

def ensureSystemLibrary():
    path = os.path.join(ROOT_DIR, SYSTEM_LIB)
    if not os.path.exists(path):
        os.makedirs(path)

def addSysPaths():
    ensureRoot()
    ensureSystemLibrary()
    for root, _, _ in os.walk(ROOT_DIR):
        if root not in sys.path:
            sys.path.append(root)

# ================= SCRIPT RUNNER =================
def runPyFile(path):
    if not os.path.exists(path):
        cmds.warning("File not found")
        return
    try:
        namespace = {"__name__": "__main__"}
        with open(path, "r", encoding="utf-8") as f:
            exec(f.read(), namespace)
    except Exception:
        cmds.warning(traceback.format_exc())

# ================= FILE / FOLDER =================
def getToolFolders():
    ensureSystemLibrary()
    return sorted([
        f for f in os.listdir(ROOT_DIR)
        if os.path.isdir(os.path.join(ROOT_DIR, f))
        and f != SYSTEM_LIB
    ])

def openRootFolder(*_):
    ensureRoot()
    if sys.platform.startswith("win"):
        os.startfile(ROOT_DIR)
    elif sys.platform == "darwin":
        subprocess.call(["open", ROOT_DIR])
    else:
        subprocess.call(["xdg-open", ROOT_DIR])

# ================= ZIP =================
def exportAllTools(*_):
    path = cmds.fileDialog2(fm=0, cap="Export All Tools", ff="Zip (*.zip)")
    if not path:
        return
    zipPath = path[0]
    with zipfile.ZipFile(zipPath, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(ROOT_DIR):
            for f in files:
                full = os.path.join(root, f)
                arc = os.path.relpath(full, ROOT_DIR)
                zipf.write(full, arc)
    cmds.inViewMessage(amg="<hl>Exported All Tools</hl>", pos="topCenter", fade=True)

def importAllTools(*_):
    path = cmds.fileDialog2(fm=1, cap="Import Tools Zip", ff="Zip (*.zip)")
    if not path:
        return
    with zipfile.ZipFile(path[0], "r") as zipf:
        zipf.extractall(ROOT_DIR)
    reloadUI()

# ================= ADD / EDIT TOOL UI =================
def openAddToolUI(editPath=None):
    if cmds.window(ADD_WIN, exists=True):
        cmds.deleteUI(ADD_WIN)

    editMode = editPath is not None
    folder = fileName = content = ""

    if editMode:
        folder = os.path.basename(os.path.dirname(editPath))
        fileName = os.path.basename(editPath)
        with open(editPath, "r", encoding="utf-8") as f:
            content = f.read()

    win = cmds.window(ADD_WIN, title="Edit Tool" if editMode else "Add Tool", width=440)
    cmds.columnLayout(adj=True, rs=3)
    
    cmds.rowColumnLayout(nc=2)
    cmds.text("Folder",al="left",width=70)
    menu = cmds.optionMenu()
    for f in getToolFolders():
        cmds.menuItem(label=f)
    if editMode:
        cmds.optionMenu(menu, e=True, v=folder)
    cmds.setParent("..")
    
    cmds.rowColumnLayout(nc=2)
    cmds.text("File Name",al="left",width=70)
    nameField = cmds.textField(text=fileName)
    cmds.setParent("..")
    
    cmds.text("Script Content:",al="left")
    contentField = cmds.scrollField(h=200, wordWrap=True, text=content)

    def save(*_):
        fName = cmds.textField(nameField, q=True, text=True).strip()
        if not fName.endswith(".py"):
            fName += ".py"
        targetFolder = cmds.optionMenu(menu, q=True, v=True)
        newPath = os.path.join(ROOT_DIR, targetFolder, fName)

        with open(newPath, "w", encoding="utf-8") as f:
            f.write(cmds.scrollField(contentField, q=True, text=True))

        if editMode and newPath != editPath and os.path.exists(editPath):
            os.remove(editPath)

        cmds.deleteUI(ADD_WIN)
        reloadUI()

    cmds.button("Save", h=34, bgc=[0.3, 0.7, 0.3], c=save)
    cmds.showWindow(win)

# ================= UI BUILD =================
def deleteTool(path):
    if cmds.confirmDialog(
        t="Delete Tool",
        m="Delete this tool?",
        b=["Yes", "No"],
        db="No"
    ) == "Yes":
        os.remove(path)
        reloadUI()

def buildButtons(parent):
    for folder in getToolFolders():
        frame = cmds.frameLayout(label=folder, collapsable=True, collapse=False, parent=parent)
        col = cmds.rowColumnLayout(nc=5, adj=True,width=(WIDTH - 10))
        for f in sorted(os.listdir(os.path.join(ROOT_DIR, folder))):
            if not f.endswith(".py"):
                continue
            full = os.path.join(ROOT_DIR, folder, f)
            btnLabel =  os.path.splitext(f)[0]
            btnLabel = btnLabel.split(".")[-1]
            btn = cmds.button(
                label=btnLabel,
                h=BTN_H,
                c=lambda _, p=full: runPyFile(p)
            )
            pm = cmds.popupMenu(parent=btn)
            cmds.menuItem(label="Edit", c=lambda _, p=full: openAddToolUI(p))
            cmds.menuItem(divider=True)
            cmds.menuItem(label="Delete", c=lambda _, p=full: deleteTool(p))
        cmds.setParent("..")

# ================= MAIN UI =================
def reloadUI():
    if cmds.window(WIN_NAME, exists=True):
        cmds.deleteUI(WIN_NAME)
    show()

def show():
    addSysPaths()
    
    if cmds.window(WIN_NAME, exists=True):
        cmds.deleteUI(WIN_NAME)
    
    if cmds.window(ADD_WIN, exists=True):
        cmds.deleteUI(ADD_WIN)

    win = cmds.window(WIN_NAME, title="Script Folder Tool", width=WIDTH)
    cmds.columnLayout(adj=True,width=WIDTH)

    cmds.menuBarLayout()
    cmds.menu(label="Tools")
    cmds.menuItem(label="Add New Tool", c=lambda *_: openAddToolUI())
    cmds.menuItem(label="Open Tool Folder", c=openRootFolder)
    cmds.menuItem(divider=True)
    cmds.menuItem(label="Export All", c=exportAllTools)
    cmds.menuItem(label="Import All", c=importAllTools)
    cmds.menuItem(divider=True)
    cmds.menuItem(label="Reload UI", c=lambda *_: reloadUI())
    cmds.setParent("..")

    cmds.scrollLayout(h=460)
    main = cmds.columnLayout(adj=True)
    buildButtons(main)

    cmds.showWindow(win)

# ================= AUTO SHOW =================
show()

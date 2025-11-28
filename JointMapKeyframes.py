import maya.cmds as cmds
import maya.mel as mel
import json
import os
from functools import partial

window = "BoneControlUI"
session = {
    "pairUI":{},
    "ignoreNamespace":False,
    "sourceLSidefix":"",
    "sourceRSidefix":"",
    "targetLSidefix":"",
    "targetRSidefix":"",
    "rootOrigin":"",
}

def HierarchyToJoints(root,namespace="BakeAnimationJoints"):
    if not cmds.namespace(exists=namespace):
        cmds.namespace(add=namespace)
    rootName = root.split(":")[-1]
    objs = cmds.listRelatives(root, ad=True, fullPath=True)[::-1]
    objs.insert(0, root)

    for obj in objs:
        objParent = cmds.listRelatives(obj, parent=True, fullPath=True)
        objName = obj.split(":")[-1]
        jointName = f"{namespace}:{objName}"
        cmds.select(clear=True)
        jointNew = cmds.joint(name=jointName)
        constraint = cmds.parentConstraint(obj, jointNew, maintainOffset=False)[0]
        cmds.delete(constraint)
        cmds.makeIdentity(jointNew, apply=True, t=1, r=1, s=1, n=0, pn=1)
        if objParent:
            objParentName = objParent[0].split(":")[-1]
            parentName = f"{namespace}:{objParentName}"
            if cmds.objExists(parentName):
                cmds.parent(jointNew, parentName)
    return(f"{namespace}:{rootName}")
    
def AddItem(list,data,*arr):
    global session    
    def GetTarget(inputUI,*arr):
        sl = cmds.ls(selection=True)
        if sl:
            obj = sl[0]
            if session['ignoreNamespace']:
                obj = obj.split(":")[-1]
            cmds.textField(inputUI,edit=True,text=obj)
        
    def GetSources(inputUI,*arr):
        sl = cmds.ls(selection=True)
        if sl:
            if session['ignoreNamespace']:
                slTemp = []
                for obj in sl:
                    slTemp.append(obj.split(":")[-1])
                sl = slTemp                    
            cmds.scrollField(inputUI,edit=True,text=("\n").join(sl))
        else:
            cmds.scrollField(inputUI,edit=True,text="")
            
    def AddSource(parentUI,sourcesUI,sourceName,*arr):
        def RemoveSouceItem(parentUI,sourcesUI,sourceItemUI,sourceItemUIParent,*arr):
            session["pairUI"][parentUI]["sources"].remove(sourceItemUI)
            cmds.deleteUI(sourceItemUIParent)
        
            
        def AddSourceItem(parentUI,sourcesUI,sourceName,*arrr):
            sourceItemUIParent = cmds.rowColumnLayout(nc=2,parent=sourcesUI)
            sourceItemUI = cmds.textField(placeholderText="Bone Name",width=240,height=30,editable=False,text=sourceName)            
            session["pairUI"][parentUI]["sources"].append(sourceItemUI)
            cmds.button(label="X",width=30,c=partial(RemoveSouceItem,parentUI,sourcesUI,sourceItemUI,sourceItemUIParent))
            cmds.setParent("..")
            
        if sourceName != "":
            AddSourceItem(parentUI,sourcesUI,sourceName)            
        else: 
            sl = cmds.ls(selection=True)
            if sl:
                for obj in sl:
                    if session['ignoreNamespace']:
                        obj = obj.split(":")[-1]
                    AddSourceItem(parentUI,sourcesUI,obj)
                

    
    def CreateMirror(listUI,parentUI,*arr):
        targetUI = session["pairUI"][parentUI][0]
        sourceUI = session["pairUI"][parentUI][1]
        targetValue = cmds.textField(targetUI,query=True,text=True)
        sourceValue = cmds.scrollField(sourceUI,query=True,text=True)
        if session["targetLSidefix"] in targetValue:
            targetSidefix = session["targetLSidefix"]
            targetMirrorSidefix = session["targetRSidefix"]
            sourceSidefix = session["sourceLSidefix"]
            sourceMirrorSidefix = session["sourceRSidefix"]            
        elif session["targetRSidefix"] in targetValue:
            targetSidefix = session["targetRSidefix"]
            targetMirrorSidefix = session["targetLSidefix"]
            sourceSidefix = session["sourceRSidefix"]
            sourceMirrorSidefix = session["sourceLSidefix"]
        targetMirror = targetValue.replace(targetSidefix,targetMirrorSidefix)
        if cmds.objExists(targetMirror):
            sourcesMirror = []
            sources = sourceValue.split("\n")
            for source in sources:
                sourceMirror = source.replace(sourceSidefix,sourceMirrorSidefix)
                if cmds.objExists(sourceMirror):
                    sourcesMirror.append(sourceMirror)    
                else:
                    print("No object has name "+sourceMirror)
                    return()
        else:
            print("No object has name "+targetMirror)
            return()
        AddItem(listUI,[targetMirror,("\n").join(sourcesMirror)])           
        
    
    def DeletePair(inputUI,*arr):
        session["pairUI"].pop(inputUI)
        cmds.deleteUI(inputUI)
        
                    

    parentUI = cmds.rowColumnLayout(nc=5,parent=list,bgc=(.2,.2,.2)) 
    session["pairUI"][parentUI]={}
    cmds.rowColumnLayout(nc=1)
    
    if data:
        target = cmds.textField(placeholderText="Bone Name",width=272,height=30,editable=False,text=data[0])
    else:
        target = cmds.textField(placeholderText="Bone Name",width=272,height=30,editable=False)
        sl = cmds.ls(selection=True)
        if sl:
            obj = sl[0]
            if session['ignoreNamespace']:
                obj = obj.split(":")[-1]
            cmds.textField(target,edit=True,text=obj)
    session["pairUI"][parentUI]["target"] = target
    session["pairUI"][parentUI]["sources"] = []
    cmds.setParent("..")
    
    cmds.rowColumnLayout(nc=1)
    cmds.button(label="->", h=30,width=39,c=partial(GetTarget,target))
    cmds.setParent("..")
    
    sources = cmds.rowColumnLayout(nc=1,width=275)    
    if data:        
        sourcesTemp = data[1].split("\n")
        for sourceTemp in sourceTemp:
            AddSource(parentUI,sources,sourceTemp)           
    cmds.setParent("..")
    
    cmds.rowColumnLayout(nc=1)
    cmds.button(label="+",width=37,h=30,c=partial(AddSource,parentUI,sources,""))    
    cmds.setParent("..")
    
    cmds.rowColumnLayout(nc=3)    
    cmds.button(label="X", h=30,width=48,bgc=(0.7, 0.3, 0.3),c=partial(DeletePair,parentUI))   
    cmds.setParent("..")
     
     
    cmds.setParent("..")
    
    #session["pairUI"][parentUI] = [target,sources]




def createUi():
    global session
    
    def PickRoot(inputUI,*arr):
        sl = cmds.ls(selection=True)
        if sl:
            obj = sl[0]
            cmds.textField(inputUI,edit=True,text=obj)
        
    def InorgeNamespace(inputUI,*arr):
        session["ignoreNamespace"] = cmds.checkBox(inputUI,query=True,value=True)   
        
    def GetData(*arr):
        returnData = []
        for pair in session["pairUI"]:
            pairData = session["pairUI"][pair]
            returnData.append(
                [
                   cmds.textField(pairData[0],query=True,text=True),
                   cmds.scrollField(pairData[1],query=True,text=True),
                ]
            )
        return(returnData)
    
    def Save(*args):        
        data = GetData()
        returnData = session
        returnData.pop("pairUI")
        returnData["data"] = data
        for input in ["sourceLSidefix","sourceRSidefix","targetLSidefix","targetRSidefix"]:
                returnData[input] = cmds.textField(input,query=True,text=True)
        returnData["ignoreNamespace"] = cmds.checkBox("ignoreNamespace",query=True,value=True)
        returnData['rootObj'] = cmds.textField("rootObj",query=True,text=True)
        savePath = cmds.fileDialog2(
            fileFilter="JSON (*.json)",
            fileMode=0,
            caption="Save JSON"
        )        
        if not savePath:
            return        
        savePath = savePath[0]
        if not savePath.lower().endswith(".json"):
            savePath += ".json"
        with open(savePath, "w") as f:
            json.dump(returnData, f, indent=4)    
        cmds.confirmDialog(title="Saved", message="JSON saved successfully!")
    
    
    def Load(inputUI,*args):
        global session
        loadPath = cmds.fileDialog2(
            fileFilter="JSON (*.json)",
            fileMode=1,
            caption="Load JSON"
        )        
        if not loadPath:
            return        
        loadPath = loadPath[0]    
        with open(loadPath, "r") as f:
            data = json.load(f)        
        if data:
            session = data
            session["pairUI"] = {}
            for input in ["sourceLSidefix","sourceRSidefix","targetLSidefix","targetRSidefix"]:
                cmds.textField(input,edit=True,text=session[input])
            cmds.checkBox("ignoreNamespace",edit=True, value=session["ignoreNamespace"])
            if "rootObj" in session:
                cmds.textField("rootObj",edit=True,text=session["rootObj"])
            children = cmds.rowColumnLayout(inputUI, query=True, childArray=True) or []
            for child in children:
                cmds.deleteUI(child)
            for i in range(len(data["data"])):
                AddItem(list,data["data"][i])
        
    def ChangeSideFix(inputUI,*arr):
        key = inputUI.split("|")[-1]
        value = cmds.textField(inputUI,query=True,text=True)
        session[key]=value
        
    def BakeToTarget(*arr):
        originRoot = cmds.textField("rootObj",query=True,text=True)
        if originRoot:
            exportPath = cmds.fileDialog2(
                fileFilter="fbx (*.fbx)",
                fileMode=0,
                caption="Save FBX"
            )
            if exportPath:
                exportPath = exportPath[0]
                
                data = GetData()
                keyTimesData = {}    
                allKeys = []    
                for pair in data:
                    sourcesKeytimes = []
                    sources = pair[1].split("\n")    
                    for source in sources:
                        source = source.strip()
                        if not source:
                            continue    
                        sourceKeytimes = cmds.keyframe(source, query=True, timeChange=True)
                        if sourceKeytimes:
                            sourcesKeytimes.extend(sourceKeytimes)    
                    sourcesKeytimes = sorted(set(sourcesKeytimes))
            
                    keyTimesData[pair[0]] = sourcesKeytimes
                    allKeys.extend(sourcesKeytimes)
                allKeys = sorted(set(allKeys))
                
                #CreateJointPreference
                cmds.currentTime(allKeys[0])
               
                bakeNamespace = "BakeAnimation"
                bakeRoot = HierarchyToJoints(originRoot,bakeNamespace)
                bakeRootName = bakeRoot.split(":")[-1] 
                originPrefix = originRoot.replace(bakeRootName,"")
                bakeRootChildren = cmds.listRelatives(bakeRoot,ad=True)
                constraints = []
                for bakeRootChild in bakeRootChildren:
                    originJoint = bakeRootChild.replace(bakeNamespace+":",originPrefix)
                    constraints.append(cmds.parentConstraint(originJoint,bakeRootChild,mo=True)[0])
                
                valueData = {}
                for key in allKeys:
                    valueData[key] = {}
                    cmds.currentTime(key)
                    for bakeRootChild in bakeRootChildren:
                        valueData[key][bakeRootChild] = {}
                        for attr in ['rx','ry','rz','tx','ty','tz','sx','sy','sz']:
                            valueData[key][bakeRootChild][attr] = cmds.getAttr(bakeRootChild+"."+attr)
                
                cmds.currentTime(allKeys[0])
                cmds.delete(constraints)        
                
                for key in allKeys:
                    cmds.currentTime(key)
                    for bakeRootChild in bakeRootChildren:
                        originJoint = bakeRootChild.replace(bakeNamespace+":",originPrefix)
                        for attr in ['rx','ry','rz','tx','ty','tz','sx','sy','sz']:
                            cmds.setAttr(bakeRootChild+"."+attr,valueData[key][bakeRootChild][attr])
                        if originJoint in keyTimesData:
                            if key in keyTimesData[originJoint]:
                                cmds.setKeyframe(bakeRootChild)
                                
                cmds.rename(originRoot,originRoot+"_NLTA")
                cmds.namespace(moveNamespace=(bakeNamespace, ":"), force=True)
                cmds.namespace(removeNamespace=bakeNamespace) 
                                            
                cmds.select(bakeRootName)
                
                if not cmds.pluginInfo('fbxmaya', query=True, loaded=True):
                    cmds.loadPlugin('fbxmaya', quiet=True) 
                mel.eval(f'FBXExport -f "{exportPath}" -s')
                
                cmds.delete(bakeRootName) 
                cmds.rename(originRoot+"_NLTA",originRoot)                  
                            
    if cmds.window(window, exists=True):
        cmds.deleteUI(window)
    cmds.window(window, title="Bone Control Mapper")
    main = cmds.columnLayout(adjustableColumn=True)
    
    mainButtonArea = cmds.rowColumnLayout(nc=1,width=700)
    cmds.setParent("..")   
    
    
    cmds.scrollLayout(height=700)
    
    cmds.rowColumnLayout(nc=5,bgc=(0.2,0.2,0.2))
    cmds.textField(text="Joints",editable=False,width=275,height=30)
    cmds.textField(text="",editable=False,width=40)
    cmds.textField(text="Controls",editable=False,width=275)
    cmds.textField(text="",editable=False,width=40)
    cmds.textField(text="",editable=False,width=50)
    cmds.setParent("..")    
        
    list = cmds.rowColumnLayout(nc=1)
    cmds.setParent("..")
    
    cmds.setParent("..")
    
    
    
    cmds.rowColumnLayout(nc=1,parent=mainButtonArea)    
    
    cmds.rowColumnLayout(nc=1)
    cmds.rowColumnLayout(nc=4)
    cmds.textField(text="Source L Sidefix:",editable=False,width=95,height=30)
    sourceLSidefix = cmds.textField("sourceLSidefix",width=150)
    cmds.textField(sourceLSidefix,edit=True,cc=partial(ChangeSideFix,sourceLSidefix))
    cmds.textField(text="Source R Sidefix:",editable=False,width=95)
    sourceRSidefix = cmds.textField("sourceRSidefix",width=150)
    cmds.textField(sourceRSidefix,edit=True,cc=partial(ChangeSideFix,sourceRSidefix))
    cmds.setParent("..")    
    cmds.rowColumnLayout(nc=4)
    cmds.textField(text="Target L Sidefix:",editable=False,width=95,height=30)
    targetLSidefix = cmds.textField("targetLSidefix",width=150)
    cmds.textField(targetLSidefix,edit=True,cc=partial(ChangeSideFix,targetLSidefix))
    cmds.textField(text="Target R Sidefix:",editable=False,width=95)
    targetRSidefix = cmds.textField("targetRSidefix",width=150)
    cmds.textField(targetRSidefix,edit=True,cc=partial(ChangeSideFix,targetRSidefix))
    cmds.setParent("..")
    cmds.rowColumnLayout(nc=3)
    cmds.textField(text="Root obj:",editable=False,width=95)
    rootObj = cmds.textField("rootObj",width=344)
    cmds.button(label="->", h=30,width = 50,c=partial(PickRoot,rootObj))
    cmds.setParent("..")
    cmds.rowColumnLayout(nc=1)
    nameSpace = cmds.checkBox("ignoreNamespace",label="Ignore namespace", value=False)
    cmds.checkBox(nameSpace,edit=True,cc=partial(InorgeNamespace,nameSpace))
    cmds.setParent("..")
    cmds.setParent("..")    
    
    cmds.separator(height=20, style='in')
    cmds.rowColumnLayout(nc=4)
    cmds.button(label="Add Row", h=30,width = 174, c=partial(AddItem,list,{}))
    cmds.button(label="Save", h=30,width = 174, bgc=(0.3, 0.7, 0.3), c=Save)
    cmds.button(label="Load", h=30,width = 174, bgc=(0.3, 0.7, 0.3), c=partial(Load,list))
    cmds.button(label="Bake", h=30,width = 174, bgc=(0.3, 0.7, 0.3), c=BakeToTarget)   
    cmds.setParent("..")
    
    cmds.setParent("..")
    
    
    cmds.setParent("..")
    cmds.setParent("..")
    cmds.showWindow(window)
    
createUi()

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
    "rootObj":"",
    "data":[],
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
    

def GetTarget(inputUI,*arr):
    sl = cmds.ls(selection=True)
    if sl:
        obj = sl[0]
        if session['ignoreNamespace']:
            obj = obj.split(":")[-1]
        cmds.textField(inputUI,edit=True,text=obj)     

def GetMirrorSide(targetValue):
    for sideInput in ["targetLSidefix","targetRSidefix","sourceLSidefix","sourceRSidefix"]:
        if session[sideInput] == "":
            return(None)
    if (session["targetLSidefix"] not in targetValue) and (session["targetRSidefix"] not in targetValue):
        return(None)
    if session["targetLSidefix"] in targetValue:
        return({
            "targetSidefix":session["targetLSidefix"],
            "targetMirrorSidefix":session["targetRSidefix"],
            "sourceSidefix":session["sourceLSidefix"],
            "sourceMirrorSidefix":session["sourceRSidefix"],
        })          
    elif session["targetRSidefix"] in targetValue:
        return({
            "targetSidefix":session["targetRSidefix"],
            "targetMirrorSidefix":session["targetLSidefix"],
            "sourceSidefix":session["sourceRSidefix"],
            "sourceMirrorSidefix":session["sourceLSidefix"],
        }) 
                
def DeletePair(inputUI,*arr):
    session["pairUI"].pop(inputUI)
    cmds.deleteUI(inputUI)
         
def DeleteMirror(mirrorName,*arr):
    for key in session["pairUI"]:
        targetTempUI = session["pairUI"][key]["target"]
        targetTempValue = cmds.textField(targetTempUI,query=True,text=True)
        if targetTempValue == mirrorName:
            DeletePair(key)

def AddSource(listUI,parentUI,sourcesUI,sourcesName,*arr):
    def RemoveSouceItem(parentUI,sourcesUI,sourceItemUI,sourceItemUIParent,*arr):
        session["pairUI"][parentUI]["sources"].remove(sourceItemUI)
        cmds.deleteUI(sourceItemUIParent)
        CreateMirror(listUI,parentUI)       
        
    def AddSourceItem(parentUI,sourcesUI,sourcesName,*arrr):
        for sourceName in sourcesName:
            sourceItemUIParent = cmds.rowColumnLayout(nc=2,parent=sourcesUI)
            sourceItemUI = cmds.textField(placeholderText="Bone Name",width=240,height=30,editable=False,text=sourceName)            
            session["pairUI"][parentUI]["sources"].append(sourceItemUI)
            cmds.button(label="X",width=30,c=partial(RemoveSouceItem,parentUI,sourcesUI,sourceItemUI,sourceItemUIParent))
            cmds.setParent("..")
        CreateMirror(listUI,parentUI)
        
    if sourcesName != "":
        AddSourceItem(parentUI,sourcesUI,sourcesName)
    else: 
        sl = cmds.ls(selection=True)
        if sl:
            objs = []
            for obj in sl:
                if session['ignoreNamespace']:
                    obj = obj.split(":")[-1]
                objs.append(obj)
            AddSourceItem(parentUI,sourcesUI,objs)
            
doMirror = False                  
def CreateMirror(listUI,parentUI,*arr):        
    targetUI = session["pairUI"][parentUI]["target"]
    sourcesUI = session["pairUI"][parentUI]["sources"]
    targetValue = cmds.textField(targetUI,query=True,text=True)
    mirrorSide = GetMirrorSide(targetValue)
    if mirrorSide:
        targetMirror = targetValue.replace(mirrorSide["targetSidefix"],mirrorSide["targetMirrorSidefix"])
        if cmds.objExists(targetMirror):  
            DeleteMirror(targetMirror)
            
            sources = []
            sourcesMirror = []
            for sourceUI in sourcesUI:
                sourceValue  = cmds.textField(sourceUI,query=True,text=True)
                sources.append(sourceValue)
            for source in sources:
                sourceMirror = source.replace(mirrorSide["sourceSidefix"],mirrorSide["sourceMirrorSidefix"])
                if cmds.objExists(sourceMirror):
                    sourcesMirror.append(sourceMirror)    
                else:
                    print("No object has name "+sourceMirror)
                    return()
            AddItem(listUI,[targetMirror,("\n").join(sourcesMirror)])
        else:
            print("No object has name "+targetMirror)
            return()
            
               
    
def AddItem(list,data,*arr):
    global session
    if data:
        target = data[0]
        sources = data[1].split('\n')
        if not cmds.objExists(target):
            return()
        for source in sources:
            if not cmds.objExists(target):
                return()
        
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
        AddSource(list,parentUI,sources,data[1])
        sourcesTemp = data[1].split("\n")
        AddSource(list,parentUI,sources,sourcesTemp)
    cmds.setParent("..")
    
    cmds.rowColumnLayout(nc=1)
    cmds.button(label="+",width=37,h=30,c=partial(AddSource,list,parentUI,sources,""))    
    cmds.setParent("..")
    
    cmds.rowColumnLayout(nc=3)    
    cmds.button(label="X", h=30,width=48,bgc=(0.7, 0.3, 0.3),c=partial(DeletePair,parentUI))   
    cmds.setParent("..")
     
     
    cmds.setParent("..")

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
            targetUI = pairData["target"]
            sourcesUI = pairData["sources"]
            sourcesArray = []
            for sourceUI in sourcesUI:
                sourcesArray.append(cmds.textField(sourceUI,query=True,text=True))
            returnData.append(
                [
                   cmds.textField(targetUI,query=True,text=True),
                   ("\n").join(sourcesArray),
                ]
            )
        return(returnData)
    
    def Save(*args):        
        data = GetData()
        returnData = session.copy()
        returnData.pop("pairUI")
        returnData["data"] = data
        print(session)
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
        print("Saved at "+savePath)
    
    def LoadSingle(inputUI,data,*arr):
        global session
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
    
    
    def LoadFromFile(inputUI,*arr):
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
            LoadSingle(inputUI,data)
            
    def LoadFromPattern(listUI,inputUI,*arr):
        value = cmds.optionMenu(inputUI,query=True,value=True)
        patternData = {
            "":{
                "pairUI":{},
                "ignoreNamespace":False,
                "sourceLSidefix":"",
                "sourceRSidefix":"",
                "targetLSidefix":"",
                "targetRSidefix":"",
                "rootObj":"",
                "data":[]
            },
            "Advance Skeleton Rig":{
                "pairUI":{},
                "ignoreNamespace":False,
                "sourceLSidefix":"",
                "sourceRSidefix":"",
                "targetLSidefix":"",
                "targetRSidefix":"",
                "rootObj":"",
                "data":[]
            },
            "Mixamo Rig":{
                "pairUI":{},
                "ignoreNamespace":False,
                "sourceLSidefix":"",
                "sourceRSidefix":"",
                "targetLSidefix":"",
                "targetRSidefix":"",
                "rootObj":"",
                "data":[]
            },
            "Rapid Rig":{
                "pairUI":{},
                "ignoreNamespace":False,
                "sourceLSidefix":"",
                "sourceRSidefix":"",
                "targetLSidefix":"",
                "targetRSidefix":"",
                "rootObj":"",
                "data":[]
            },
        }
    
    
        if value in patternData:
            data = patternData[value]
            LoadSingle(listUI,data)
        
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
    
    def SearchOk(ui,*arr):
        value = cmds.textField(ui,query=True,text=True)
        for key in session["pairUI"]:
            cmds.rowColumnLayout(key,edit=True,visible=False)
        for key in session["pairUI"]:
            targetUI = session["pairUI"][key]["target"]
            targetValue = cmds.textField(targetUI,query=True,text=True)
            if value in targetValue:
                cmds.rowColumnLayout(key,edit=True,visible=True)
            sourcesUI = session["pairUI"][key]["sources"]
            for sourceUI in sourcesUI:
                sourceValue = cmds.textField(sourceUI,query=True,text=True)
                if value in sourceValue:
                    cmds.rowColumnLayout(key,edit=True,visible=True)    
                
    def ReplaceTargetOk(textFindUI,textReplaceUI,*arr):
        textFind = cmds.textField(textFindUI,query=True,text=True)
        textReplace = cmds.textField(textReplaceUI,query=True,text=True)
        for key in session["pairUI"]:
            targetUI = session["pairUI"][key]["target"]
            targetValue = cmds.textField(targetUI,query=True,text=True)
            if textFind in targetValue:
                textNew =  targetValue.replace(textFind,textReplace)
                cmds.textField(targetUI,edit=True,text=textNew)
        cmds.textField(textFindUI,edit=True,text="")
        cmds.textField(textReplaceUI,edit=True,text="")
        
    def ReplaceSourceOk(textFindUI,textReplaceUI,*arr):
        textFind = cmds.textField(textFindUI,query=True,text=True)
        textReplace = cmds.textField(textReplaceUI,query=True,text=True)
        for key in session["pairUI"]:
            sourcesUI = session["pairUI"][key]["sources"]
            for sourceUI in sourcesUI:
                sourceValue = cmds.textField(sourceUI,query=True,text=True)
                if textFind in sourceValue:
                    textNew =  sourceValue.replace(textFind,textReplace)
                    cmds.textField(sourceUI,edit=True,text=textNew)
        cmds.textField(textFindUI,edit=True,text="")
        cmds.textField(textReplaceUI,edit=True,text="")
                      
                            
    if cmds.window(window, exists=True):
        cmds.deleteUI(window)
    cmds.window(window, title="Joints Controls Mapper")
    main = cmds.columnLayout(adjustableColumn=True)#START MAIN
    
    # MAIN BUTTON AREA
    mainButtonArea = cmds.rowColumnLayout(nc=2,width=700)
    cmds.setParent("..")   
    
    #SEARCH AREA
    searchArea = cmds.rowColumnLayout(nc=1,width=700)
    cmds.setParent("..")
    
    
    cmds.separator(height=2, style='in')
    
    
    title = cmds.rowColumnLayout(nc=4,width=700)
    cmds.textField(text="JOINTS",editable=False,width=278,height=30)
    cmds.textField(text="",editable=False,width=40)
    cmds.textField(text="CONSTROLS",editable=False,width=275)
    cmds.setParent("..")
    
    
    # SCROLL AREA
    cmds.scrollLayout(height=600)#START SCROLL    
    list = cmds.rowColumnLayout(nc=1)
    cmds.setParent("..")    
    cmds.setParent("..")#END SCROLL
    
    #ADD SEARCH AREA CHILD
    cmds.rowColumnLayout(nc=2,parent=searchArea)
    searchText = cmds.textField(height=35,width=681,pht="Search")
    cmds.textField(searchText,edit=True,tcc=partial(SearchOk,searchText))
    cmds.setParent("..")
    
    #ADD TITLE CHILD
    cmds.rowColumnLayout(nc=1,parent=title)
    cmds.button(label="ADD", bgc=(0.3, 0.7, 0.3), h=30,width = 88, c=partial(AddItem,list,{}))
    cmds.setParent("..")   
    
    
    
    cmds.rowColumnLayout(nc=2,parent=mainButtonArea)#ADD MAIN BUTTON OPTION
    
    #COLUM 1
    cmds.rowColumnLayout(nc=1)   
    
    cmds.rowColumnLayout(nc=2)
    targetRSidefix = cmds.textField("targetRSidefix",width=150,pht="Target R Sidefix")
    cmds.textField(targetRSidefix,edit=True,cc=partial(ChangeSideFix,targetRSidefix))
    targetLSidefix = cmds.textField("targetLSidefix",width=150,height=30,pht="Target L Sidefix")
    cmds.textField(targetLSidefix,edit=True,cc=partial(ChangeSideFix,targetLSidefix))
    cmds.setParent("..")
    
    cmds.rowColumnLayout(nc=2)
    sourceRSidefix = cmds.textField("sourceRSidefix",width=150,pht="Source R Sidefix")
    cmds.textField(sourceRSidefix,edit=True,cc=partial(ChangeSideFix,sourceRSidefix))
    sourceLSidefix = cmds.textField("sourceLSidefix",width=150,height=30,pht="Source L Sidefix")
    cmds.textField(sourceLSidefix,edit=True,cc=partial(ChangeSideFix,sourceLSidefix))
    cmds.setParent("..")   

    
    cmds.rowColumnLayout(nc=2)
    rootObj = cmds.textField("rootObj",width=260,pht="Root obj")
    cmds.button(label="->", h=30,width =39,c=partial(PickRoot,rootObj))
    cmds.setParent("..")
    
    cmds.rowColumnLayout(nc=1)
    nameSpace = cmds.checkBox("ignoreNamespace",label="Ignore namespace", value=False)
    cmds.checkBox(nameSpace,edit=True,cc=partial(InorgeNamespace,nameSpace))
    cmds.setParent("..")
       
    cmds.setParent("..")#END COLUMN 1
    
    #COLUM2
    cmds.rowColumnLayout(nc=1) #START COLUMN 2
    
    cmds.rowColumnLayout(nc=1)    
    cmds.rowColumnLayout(nc=2)
    cmds.textField(text="Load Pattern",editable=False,width=80,height=30)    
    patternsUI = cmds.optionMenu(label="", w=294,height=30)
    cmds.menuItem(label="")
    cmds.menuItem(label="Advance Skeleton Rig")
    cmds.menuItem(label="Mixamo Rig")
    cmds.menuItem(label="Rapid Rig")
    cmds.optionMenu(patternsUI,edit=True,cc=partial(LoadFromPattern,list,patternsUI))
    cmds.setParent("..")
    cmds.rowColumnLayout(nc=2)
    cmds.textField(text="Load File",editable=False,height=30,width=82)
    cmds.button(label="Select File Data", h=30,w=292, c=partial(LoadFromFile,list))
    cmds.setParent("..")
    cmds.setParent("..")
    
    
    cmds.rowColumnLayout(nc=2)
    cmds.rowColumnLayout(nc=1)
    findText = cmds.textField(width=260,pht="Find Text",height=30,)
    replaceText = cmds.textField(width=260,pht="Replace Text",height=30)
    cmds.setParent("..")
    cmds.rowColumnLayout(nc=2)
    cmds.button(label="Replace\nTarget", h=60,width =56,c=partial(ReplaceTargetOk,findText,replaceText))    
    cmds.button(label="Replace\nSource", h=60,width =56,c=partial(ReplaceSourceOk,findText,replaceText))    
    cmds.setParent("..")
    cmds.setParent("..")
    
    cmds.setParent("..")
           
    cmds.setParent("..")#END COLUMN 2
    
    cmds.setParent("..")
    
    
    cmds.separator(height=20, style='in')
    
    cmds.rowColumnLayout(nc=4,width=700)
    cmds.button(label="Save", h=30,width = 348,c=Save)
    
    cmds.button(label="Bake", h=30,width = 348, bgc=(0.3, 0.7, 0.3), c=BakeToTarget)   
    cmds.setParent("..") 
    
    cmds.setParent("..")#END MAIN
    cmds.showWindow(window)
    
createUi()

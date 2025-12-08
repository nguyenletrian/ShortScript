import maya.cmds as cmds
import maya.mel as mel
import json
import os
from functools import partial

window = "BoneControlUI"
UIs = {}
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

def LoadUIsValue():
    for key in UIs:        
        if key in session:
            value = session[key]
            ui = UIs[key]
            if key!= "ignoreNamespace":
                cmds.textField(ui,edit=True,text=value)
            else:
                cmds.checkBox(ui,edit=True,value=value)
            
def LoadFromFile(listUI,searchUI,*arr):
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
        LoadItems(listUI,searchUI)
        LoadUIsValue()

def LoadFromPattern(listUI,inputUI,searchUI,*arr):
    global session
    value = cmds.optionMenu(inputUI,query=True,value=True)
    if value == "":
        session ={
            "ignoreNamespace":False,
            "sourceLSidefix":"",
            "sourceRSidefix":"",
            "targetLSidefix":"",
            "targetRSidefix":"",
            "rootObj":"",
            "pairs":[]
        }
        LoadItems(listUI,searchUI)
        LoadUIsValue()
    else:
        dataPath = CheckPatternsFolder()+"/"+value+".json"
        print(dataPath)
        with open(dataPath, "r") as f:
            data = json.load(f)    
        if data:
            session = data
            LoadItems(listUI,searchUI)
            LoadUIsValue()

def Save(*args):
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
        json.dump(session, f, indent=4)        
    print("Saved at "+savePath)
        

def GetTarget(inputUI,*arr):
    global session
    targetCurrent = cmds.textField(inputUI,query=True,text=True)
    currentIndex = None
    for i in range(len(session["pairs"])):
        if session["pairs"][i][0] == targetCurrent:
            currentIndex = i
            break
    if currentIndex:
        sl = cmds.ls(selection=True)
        if sl:
            obj = sl[0]
            if session['ignoreNamespace']:
                obj = obj.split(":")[-1]
            cmds.textField(inputUI,edit=True,text=obj)
            session["pairs"][currentIndex][0] = obj  

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
        
def ModifyMirror(currentIndex,*arr):
    target = session["pairs"][currentIndex][0]
    mirrorSide = GetMirrorSide(target)
    if mirrorSide:
        targetMirror = target.replace(mirrorSide["targetSidefix"],mirrorSide["targetMirrorSidefix"])    
        if cmds.objExists(targetMirror):
            sources = session["pairs"][currentIndex][1]
            sourceMirrorArray = []
            for source in sources:
                sourceMirror = source.replace(mirrorSide["sourceSidefix"],mirrorSide["sourceMirrorSidefix"])
                if cmds.objExists(sourceMirror):
                    sourceMirrorArray.append(sourceMirror)
            targetMirrorIndex = False
            for i in range(len(session["pairs"])):
                if session["pairs"][i][0] == targetMirror:
                    targetMirrorIndex = i
                    break
            if targetMirrorIndex:
                session["pairs"][targetMirrorIndex][1] = sourceMirrorArray
            else:
                session["pairs"].append([targetMirror,sourceMirrorArray])
            
        
    
def AddSource(listUI,targetUI,searchUI,*arr):
    global session
    objs = cmds.ls(selection=True)
    if objs:
        targetValue = cmds.textField(targetUI,query=True,text=True)
        for i in range(len(session["pairs"])):
            if session["pairs"][i][0] == targetValue:
                sources = session["pairs"][i][1]
                for obj in objs:
                    if obj not in sources:
                        session["pairs"][i][1].append(obj)
                currentIndex = i
                ModifyMirror(currentIndex)
                LoadItems(listUI,searchUI) 
                break
   

def RemoveSource(listUI,targetUI,sourceNameUI,searchUI,*arr):
    global session
    targetValue = cmds.textField(targetUI,query=True,text=True)
    sourceValue = cmds.textField(sourceNameUI,query=True,text=True)
    for i in range(len(session["pairs"])):
        target = session["pairs"][i][0]
        sources = session["pairs"][i][1]
        if target == targetValue and sourceValue in sources:            
            session["pairs"][i][1].remove(sourceValue)
            currentIndex = i
            ModifyMirror(currentIndex)
            LoadItems(listUI,searchUI)
            break

def DeleteItem(listUI,targetUI,searchUI,*arr):
    targetValue = cmds.textField(targetUI,query=True,text=True)
    for i in range(len(session["pairs"])):
        target = session["pairs"][i][0]
        if target == targetValue:
            del session["pairs"][i]
            break
    LoadItems(listUI,searchUI)   
    
def AddItem(listUI,data,searchUI,*arr):
    global session
    if data:
        target = data[0]
        sources = data[1]
        """
        if not cmds.objExists(target):
            return()
        for source in sources:
            if not cmds.objExists(target):
                return()    
        target = data[0]
        sources = data[1]
        """
    else:
        objs = cmds.ls(selection=True)
        if objs:
            target =  objs[0]
            sources = []
            checkExist = False
            for i in range(len(session["pairs"])):
                if session["pairs"][i][0] == target:
                    checkExist = True
                    return()
            if not checkExist:
                session["pairs"].append([target,sources])
                LoadItems(listUI,searchUI)
                return() 
        
    parentUI = cmds.rowColumnLayout(nc=5,parent=listUI,bgc=(.2,.2,.2)) 
    cmds.rowColumnLayout(nc=1)
    targetUI = cmds.textField(placeholderText="Bone Name",width=272,height=30,editable=False,text=target)
    cmds.setParent("..")
    
    cmds.rowColumnLayout(nc=1)
    cmds.button(label="->", h=30,width=39,c=partial(GetTarget,targetUI))
    cmds.setParent("..")
    
    sourcesItemUI = cmds.rowColumnLayout(nc=1,width=275)    
    for source in sources:
        sourceItemUI = cmds.rowColumnLayout(nc=2)
        sourceName = cmds.textField(placeholderText="Bone Name",width=240,height=30,editable=False,text=source)    
        cmds.button(label="X",width=30,c=partial(RemoveSource,listUI,targetUI,sourceName,searchUI))
        cmds.setParent("..")
    cmds.setParent("..")
    
    cmds.rowColumnLayout(nc=1)
    cmds.button(label="+",width=37,h=30,c=partial(AddSource,listUI,targetUI,searchUI))    
    cmds.setParent("..")
    
    cmds.rowColumnLayout(nc=3)    
    cmds.button(label="X", h=30,width=48,bgc=(0.7, 0.3, 0.3),c=partial(DeleteItem,listUI,targetUI,searchUI))   
    cmds.setParent("..")
     
     
    cmds.setParent("..")

def GoToScrollAreaEnd():
    cmds.scrollLayout(UIs["scrollArea"], e=True,scrollPage="down")      

def LoadItems(listUI,searchUI,*arr):    
    children = cmds.rowColumnLayout(listUI, q=True, childArray=True)
    if children:
        for child in children:
            cmds.deleteUI(child)
    searchText = cmds.textField(searchUI,query=True,text=True)
    pairs =  session["pairs"]
    for pair in pairs:
        target = pair[0]
        sources = pair[1]
        searchResult = False
        if searchText in target:
            searchResult = True
        for source in sources:
            if searchText in source:
                searchResult = True
                break
        if searchResult:
            AddItem(listUI,pair,searchUI)
    GoToScrollAreaEnd()

def ReplaceSourceOk(textFindUI,textReplaceUI,listUI,searchUI,*arr):
    global session
    textFind = cmds.textField(textFindUI,query=True,text=True)
    textReplace = cmds.textField(textReplaceUI,query=True,text=True)    
    for a in range(len(session["pairs"])):
        sources = session["pairs"][a][1]
        for b in range(len(sources)):
            sourceName = sources[b]
            sourceNewName = sourceName.replace(textFind,textReplace)
            session["pairs"][a][1][b] = sourceNewName                
    cmds.textField(textFindUI,edit=True,text="")
    cmds.textField(textReplaceUI,edit=True,text="")
    LoadItems(listUI,searchUI)

def ReplaceTargetOk(textFindUI,textReplaceUI,listUI,searchUI,*arr):
    global session
    textFind = cmds.textField(textFindUI,query=True,text=True)
    textReplace = cmds.textField(textReplaceUI,query=True,text=True)    
    for a in range(len(session["pairs"])):
        targetName = session["pairs"][a][0]
        targetNewName = targetName.replace(textFind,textReplace)
        session["pairs"][a][0] = targetNewName
    cmds.textField(textFindUI,edit=True,text="")
    cmds.textField(textReplaceUI,edit=True,text="")
    LoadItems(listUI,searchUI)
    
def BakeToTarget(*arr):
    global session
    originRoot = session["rootObj"]
    if originRoot:
        exportPath = cmds.fileDialog2(
            fileFilter="fbx (*.fbx)",
            fileMode=0,
            caption="Save FBX"
        )
        if exportPath:
            exportPath = exportPath[0]
            
            data = session["pairs"]
            keyTimesData = {}    
            allKeys = []    
            for pair in data:
                sourcesKeytimes = []
                sources = pair[1]
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

def CheckPatternsFolder():
    patternsPath = cmds.internalVar(userAppDir=True)
    patternsPath = (os.path.normpath(patternsPath)).replace("\\",'/') +"/JointsMapControls"
    if not os.path.exists(patternsPath):
        os.makedirs(patternsPath)
    return(patternsPath)
                  
def SavePattern(UI,*arr):
    result = cmds.promptDialog(
        title='Save Pattern',
        message='Pattern Name:',
        button=['OK', 'Cancel'],
        defaultButton='OK',
        cancelButton='Cancel',
        dismissString='Cancel'
    )
    if result == 'OK':
        value = cmds.promptDialog(query=True, text=True)
        patternsPath = CheckPatternsFolder()
        patternPath = patternsPath +"/"+value+".json"
        with open(patternPath, "w") as f:
            json.dump(session, f, indent=4)
        LoadPatternItems(UI)

def LoadPatternItems(UI,*arr):
    cmds.optionMenu(UI, e=True, deleteAllItems=True)
    patternsFolder = CheckPatternsFolder()
    files = [f for f in os.listdir(patternsFolder) if os.path.isfile(os.path.join(patternsFolder, f))]
    cmds.menuItem(label="",p=UI)
    for file_ in files:
        fileNameArray =  file_.split(".")
        fileName = fileNameArray[0]
        fileExt = fileNameArray[1]
        if fileExt == "json":    
            cmds.menuItem(label=fileName,p=UI)
               
def createUI():
    global session
    global UIs
    
    def ChangeSideFix(inputUI,*arr):
        key = inputUI.split("|")[-1]
        value = cmds.textField(inputUI,query=True,text=True)
        session[key]=value
        
    def PickRoot(inputUI,*arr):
        sl = cmds.ls(selection=True)
        if sl:
            obj = sl[0]
            cmds.textField(inputUI,edit=True,text=obj)
            session["rootObj"] = obj
        
    def InorgeNamespace(inputUI,*arr):
        session["ignoreNamespace"] = cmds.checkBox(inputUI,query=True,value=True)                                 
                            
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
    cmds.textField(text="",editable=False,width=88)
    cmds.setParent("..")
    
    
    # SCROLL AREA
    UIs["scrollArea"] = cmds.scrollLayout(height=400)#START SCROLL    
    list = cmds.rowColumnLayout(nc=1)
    cmds.setParent("..")
    cmds.separator(height=50, style='in')
    cmds.setParent("..")#END SCROLL
    
    #ADD SEARCH AREA CHILD
    cmds.rowColumnLayout(nc=2,parent=searchArea)
    searchUI = cmds.textField(height=35,width=681,pht="Search")
    cmds.textField(searchUI,edit=True,tcc=partial(LoadItems,list,searchUI))
    cmds.setParent("..")   
    
    
    cmds.rowColumnLayout(nc=2,parent=mainButtonArea)#ADD MAIN BUTTON OPTION
    
    #COLUM 1
    cmds.rowColumnLayout(nc=1)   
    
    cmds.rowColumnLayout(nc=2)
    targetRSidefix = cmds.textField("targetRSidefix",width=150,pht="Target R Sidefix")
    cmds.textField(targetRSidefix,edit=True,cc=partial(ChangeSideFix,targetRSidefix))
    UIs["targetRSidefix"] = targetRSidefix
    targetLSidefix = cmds.textField("targetLSidefix",width=150,height=30,pht="Target L Sidefix")
    cmds.textField(targetLSidefix,edit=True,cc=partial(ChangeSideFix,targetLSidefix))
    UIs["targetLSidefix"] = targetLSidefix
    cmds.setParent("..")
    
    cmds.rowColumnLayout(nc=2)
    sourceRSidefix = cmds.textField("sourceRSidefix",width=150,pht="Source R Sidefix")
    cmds.textField(sourceRSidefix,edit=True,cc=partial(ChangeSideFix,sourceRSidefix))
    UIs["sourceRSidefix"] = sourceRSidefix
    sourceLSidefix = cmds.textField("sourceLSidefix",width=150,height=30,pht="Source L Sidefix")
    cmds.textField(sourceLSidefix,edit=True,cc=partial(ChangeSideFix,sourceLSidefix))
    UIs["sourceLSidefix"] = sourceLSidefix
    cmds.setParent("..")   

    
    cmds.rowColumnLayout(nc=2)
    rootObj = cmds.textField("rootObj",width=260,pht="Root obj")
    UIs["rootObj"] = rootObj
    cmds.button(label="->", h=30,width =39,c=partial(PickRoot,rootObj))
    cmds.setParent("..")
    
    cmds.rowColumnLayout(nc=1)
    nameSpace = cmds.checkBox("ignoreNamespace",label="Ignore namespace", value=False)
    cmds.checkBox(nameSpace,edit=True,cc=partial(InorgeNamespace,nameSpace))
    UIs["ignoreNamespace"] = nameSpace
    cmds.setParent("..")
       
    cmds.setParent("..")#END COLUMN 1
    
    #COLUM2
    cmds.rowColumnLayout(nc=1) #START COLUMN 2
    
    cmds.rowColumnLayout(nc=1)    
    cmds.rowColumnLayout(nc=2)
    cmds.textField(text="From Pattern",editable=False,width=80,height=30)    
    patternsUI = cmds.optionMenu(label="", w=294,height=30)    
    LoadPatternItems(patternsUI)
    cmds.optionMenu(patternsUI,edit=True,cc=partial(LoadFromPattern,list,patternsUI,searchUI))
    cmds.setParent("..")
    
    cmds.rowColumnLayout(nc=2)
    cmds.textField(text="From File",editable=False,height=30,width=82)
    cmds.button(label="Select File", h=30,w=292, c=partial(LoadFromFile,list,searchUI))
    cmds.setParent("..")
    cmds.setParent("..")
    
    
    cmds.rowColumnLayout(nc=2)
    cmds.rowColumnLayout(nc=1)
    findText = cmds.textField(width=260,pht="Find Text",height=30,)
    replaceText = cmds.textField(width=260,pht="Replace Text",height=30)
    cmds.setParent("..")
    cmds.rowColumnLayout(nc=2)
    cmds.button(label="Replace\nTarget", h=60,width =56,c=partial(ReplaceTargetOk,findText,replaceText,list,searchUI))    
    cmds.button(label="Replace\nSource", h=60,width =56,c=partial(ReplaceSourceOk,findText,replaceText,list,searchUI))    
    cmds.setParent("..")
    cmds.setParent("..")
    
    cmds.setParent("..")
           
    cmds.setParent("..")#END COLUMN 2
    
    cmds.setParent("..")
    
    
    cmds.separator(height=20, style='in')
    
    cmds.rowColumnLayout(nc=4,width=700)
    cmds.button(label="ADD", bgc=(0.3, 0.7, 0.3), h=30,width = 175, c=partial(AddItem,list,None,searchUI))
    cmds.button(label="Save", h=30,width =175,c=Save)
    cmds.button(label="Save Pattern", h=30,width = 175,c=partial(SavePattern,patternsUI))   
    cmds.button(label="Bake", h=30,width = 175, bgc=(0.3, 0.7, 0.3), c=BakeToTarget)   
    cmds.setParent("..") 
    
    cmds.setParent("..")#END MAIN
    cmds.showWindow(window)
    LoadItems(list,searchUI)
createUI()
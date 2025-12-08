import maya.cmds as cmds
from functools import partial
from math import sqrt
import json
import pymel.core as pm
sessionData = {
    "sourceRoot":None,
    "targetRoot":None,
    "sourceRootNamespace":"",
    "targetRootNamespace":"",
    "sourceSidefixRight":"",
    "sourceSidefixLeft":"",
    "targetSidefixRight":"",
    "targetSidefixLeft":"",
    "pair":[]
}

def writeJsonFile(url,data,*arr):
    with open(url,"w") as json_file:
        json.dump(data,json_file,sort_keys=False)
    print("Url export: " + url)

def readJsonFile(url,*arr):
    if os.path.exists(url):
        filePath = cmds.encodeString(url)
        myFile =  open(filePath,'r')
        myObject = myFile.read()
        myFile.close()
        if int(cmds.about(version=True)) < 2022:
            data = json.loads(myObject,'utf-8')
        else:
            data = json.loads(myObject)
        return(data)
    else:
        print("!: File is not exists!")

def GetDistance(obj1, obj2,*arr):
    pos1 = cmds.xform(obj1, query=True, worldSpace=True, translation=True)
    pos2 = cmds.xform(obj2, query=True, worldSpace=True, translation=True)
    distance = sqrt((pos2[0] - pos1[0])**2 + (pos2[1] - pos1[1])**2 + (pos2[2] - pos1[2])**2)
    return(distance)    

def ClearToolSetting(*arr):
    try:
        cmds.delete("NLTA_Scale_Mocap_Group")
    except:pass
    for pair in sessionData["pair"]:
        target = pair[1]
        if sessionData["targetRootNamespace"]!="":
            target = sessionData["targetRootNamespace"]+":"+target
        conn = cmds.listConnections(target+'.rotate',source=True,destination=False,plugs=True)
        if conn:
            cmds.disconnectAttr(conn[0],target+".rotate")
    string = 'NLTA_'
    objs = cmds.ls()
    deletes = [obj for obj in objs if string in obj]
    if deletes:
        cmds.delete(deletes)    

def PrepareScene(*arr):
    obj = "NLTA_Scale_Mocap_Node"
    if not cmds.objExists(obj):
        cmds.createNode('floatConstant', name=obj)
    obj = "NLTA_Scale_Mocap_Group"
    if not cmds.objExists(obj):
        cmds.group(name=obj,empty=True)

def SelectRoot(rootType,*arr):
    selection = cmds.ls(selection=True)
    if selection:
        sessionData[rootType] = selection[0]

def CreateRootTempt(*arr):
    global sessionData
    for obj in ["sourceRoot","targetRoot"]:
        if sessionData[obj]!=None:
            cmds.select(clear=True)
            objWorldLocation = cmds.xform(sessionData[obj],query=True,ws=True,t=True)
            objWorldLocation[1] = 0
            obj = cmds.joint(name='NLTA_'+obj, position=objWorldLocation)
            cmds.parent(obj,"NLTA_Scale_Mocap_Group")
        else:
            return(False)
    return(True)

def TranslateConnectWithScale(objStart,objEnd,objParent,objEffect,scaleValue):
    endDecompose = cmds.createNode("decomposeMatrix",name="NLTA_"+objEnd+"_Decompose")  
    startDecompose =  cmds.createNode("decomposeMatrix",name="NLTA_"+objStart+"_Decompose")
    cmds.connectAttr(objStart+".worldMatrix[0]",startDecompose+".inputMatrix")
    cmds.connectAttr(objEnd+".worldMatrix[0]",endDecompose+".inputMatrix")

    directionAdd = cmds.createNode('plusMinusAverage', name="NLTA_"+objStart+"_"+objEnd+'_Direction')
    cmds.connectAttr(endDecompose+".outputTranslate",directionAdd+".input3D[0]")
    cmds.connectAttr(startDecompose+".outputTranslate",directionAdd+".input3D[1]")
    cmds.setAttr(directionAdd+'.operation',2)

    distance = cmds.createNode('distanceBetween', name="NLTA_"+objStart+"_"+objEnd+'_DistanceBetween')
    cmds.connectAttr(endDecompose+".outputTranslate",distance+".point1")
    cmds.connectAttr(startDecompose+".outputTranslate",distance+".point2")

    vectorProduct = cmds.createNode('vectorProduct', name="NLTA_"+objStart+"_"+objEnd+'_Normalize')
    cmds.setAttr(vectorProduct+'.operation',3)
    cmds.setAttr(vectorProduct+'.normalizeOutput',1)
    cmds.connectAttr(directionAdd+".output3D",vectorProduct+".input1")

    multiScale = cmds.createNode('multiplyDivide', name="NLTA_"+objStart+"_"+objEnd+'_MultiScale')
    cmds.setAttr(multiScale+'.operation', 1)
    cmds.connectAttr(distance+".distance",multiScale+".input1X")
    cmds.setAttr(multiScale+'.input2X',scaleValue)
    cmds.setAttr(multiScale+'.input2Y',scaleValue)
    cmds.setAttr(multiScale+'.input2Z',scaleValue)

    multiAfterScale = cmds.createNode('multiplyDivide', name="NLTA_"+objStart+"_"+objEnd+'_AfterScale')
    cmds.connectAttr(vectorProduct+".output",multiAfterScale+".input1")
    cmds.connectAttr(multiScale+".outputX",multiAfterScale+".input2X")
    cmds.connectAttr(multiScale+".outputX",multiAfterScale+".input2Y")
    cmds.connectAttr(multiScale+".outputX",multiAfterScale+".input2Z")

    effectDecompose = cmds.createNode("decomposeMatrix",name="NLTA_"+objEnd+"_EffectDecompose")
    cmds.connectAttr(objParent+".worldMatrix[0]",effectDecompose+".inputMatrix")

    newPositionAdd = cmds.createNode('plusMinusAverage', name="NLTA_"+objStart+"_"+objEnd+'_NewPositionAdd')
    cmds.connectAttr(multiAfterScale+".output",newPositionAdd+".input3D[1]")
    cmds.connectAttr(effectDecompose+".outputTranslate",newPositionAdd+".input3D[0]")
    
    if objEffect.split(":")[-1] == sessionData["targetRoot"]:  
        multiExtra = cmds.createNode('multiplyDivide', name="NLTA_"+objStart+"_"+objEnd+'_MultiTranslateExtra')
        cmds.connectAttr("NLTA_Scale_Mocap_Node.outFloat",multiExtra+".input2X")
        cmds.connectAttr("NLTA_Scale_Mocap_Node.outFloat",multiExtra+".input2Y")
        cmds.connectAttr("NLTA_Scale_Mocap_Node.outFloat",multiExtra+".input2Z")
        cmds.connectAttr(newPositionAdd+".output3D",multiExtra+".input1")
        cmds.connectAttr(multiExtra+".output",objEffect+".translate")
    else:
        cmds.connectAttr(newPositionAdd+".output3D",objEffect+".translate")
        
    
def ConstraintOrient(source,target):
    constraint = cmds.orientConstraint(source,target,name="NLTA_"+source+"_"+target+"_orientConstraint",maintainOffset=True)[0]
    multiExtra = cmds.createNode('multiplyDivide', name="NLTA_"+source+"_"+target+'_MultiRotateExtra')

    cmds.connectAttr("NLTA_Scale_Mocap_Node.outFloat",multiExtra+".input2X")
    cmds.connectAttr("NLTA_Scale_Mocap_Node.outFloat",multiExtra+".input2Y")
    cmds.connectAttr("NLTA_Scale_Mocap_Node.outFloat",multiExtra+".input2Z")
    cmds.connectAttr(constraint+".constraintRotateX",multiExtra+".input1X")
    cmds.connectAttr(constraint+".constraintRotateY",multiExtra+".input1Y")
    cmds.connectAttr(constraint+".constraintRotateZ",multiExtra+".input1Z")
    cmds.connectAttr(multiExtra+".outputX",target+".rotateX",force=True)
    cmds.connectAttr(multiExtra+".outputY",target+".rotateY",force=True)
    cmds.connectAttr(multiExtra+".outputZ",target+".rotateZ",force=True)

def CreateConnect(*arr):
    PrepareScene()
    CreateRootTempt()
    targetList = []    
    for i in range(len(sessionData["pair"])):
        targetList.append(sessionData["pair"][i][1]) 
    for i in range(len(sessionData["pair"])):
        pair = sessionData["pair"][i]
        source = pair[0]
        target = pair[1]
        if sessionData["sourceRootNamespace"]!= "":
            source = sessionData["sourceRootNamespace"]+":"+source 
        if sessionData["targetRootNamespace"]!= "":
            target = sessionData["targetRootNamespace"]+":"+target
        targetParent = cmds.listRelatives(target,parent=True)
        if targetParent:
            targetParent = targetParent[0]
            targetParentNoNS = targetParent.split(":")[-1]
            if targetParentNoNS in targetList:
                index = targetList.index(targetParentNoNS)
                sourceParentNoNS = sessionData["pair"][index][0]
                if sessionData["sourceRootNamespace"]!= "":
                    sourceParent = sessionData["sourceRootNamespace"]+":"+sourceParentNoNS
                else:
                    sourceParent = sourceParentNoNS
            else:
                targetParent = "NLTA_targetRoot"
                sourceParent = "NLTA_sourceRoot"   
        else:
            targetParent = "NLTA_targetRoot"
            sourceParent = "NLTA_sourceRoot"
        sourceDistance = GetDistance(sourceParent,source)
        targetDistance = GetDistance(targetParent,target)
        if sourceDistance!=0:
            scaleRatio = targetDistance/sourceDistance
        else:
            scaleRatio = targetDistance               
        locator = cmds.spaceLocator(name='NLTA_'+source+"_"+target)[0]
        cmds.matchTransform(locator,target,pos=True,rot=True)                
        TranslateConnectWithScale(sourceParent,source,targetParent,locator,scaleRatio)
        ConstraintOrient(source,target)
        translateLock = False
        for attr in ['tx','ty','tz']:
            if cmds.getAttr(target+'.'+attr,lock=True):
                translateLock = True
                break
        if not translateLock:
            constraint = cmds.pointConstraint(locator,target, maintainOffset=True)
            try:
                cmds.parent(constraint,"NLTA_Scale_Mocap_Group")
            except:pass
            try:
                cmds.parent(locator,"NLTA_Scale_Mocap_Group")           
            except:pass

def ChangePairSource(inputPair,*arr):
    selection = cmds.ls(selection=True)
    if selection:
        obj = selection[0]
        sourceNamespace = sessionData["sourceRootNamespace"]
        if sourceNamespace in obj:
            objName = obj.split(":")[-1]
            for i in range(len(sessionData["pair"])):
                pair = sessionData["pair"][i]
                if inputPair == pair:
                    sessionData["pair"][i][0] = objName
        else:
            print("Please select object have source namspaces!")
    LoadItem()

def ChangePairTarget(inputPair,*arr):
    selection = cmds.ls(selection=True)
    if selection:
        obj = selection[0]
        sourceNamespace = sessionData["sourceRootNamespace"]
        if sourceNamespace in obj:
            objName = obj.split(":")[-1]
            for i in range(len(sessionData["pair"])):
                pair = sessionData["pair"][i]
                if inputPair == pair:
                    sessionData["pair"][i][1] = objName
        else:
            print("Please select object have source namspaces!")
    LoadItem()
            
def DeletePair(inputPair,*arr):
    global sessionData
    arrayTemp = []
    for pair in sessionData["pair"]:
        if pair != inputPair:
            arrayTemp.append(pair)
    sessionData["pair"] = arrayTemp
    LoadItem()

def LoadItem(*arr):
    children = cmds.scrollLayout("NLTA_ItemList", query=True, childArray=True)
    if children:
        for child in children:
            cmds.deleteUI(child)
            
    for pair in sessionData["pair"]:
        source = pair[0]
        target = pair[1]
        cmds.rowColumnLayout(adjustableColumn=True,width=280,parent="NLTA_ItemList",numberOfColumns=5,columnSpacing=[(1,5), (2,5), (3,5)])
        cmds.button( label=source,width=100,c=partial(ChangePairSource,pair))
        cmds.button( label=target,width=100,c=partial(ChangePairTarget,pair))
        cmds.button( label='X',width=25,c=partial(DeletePair,pair))
        cmds.setParent( '..' )
       
def SetPair(*arr):
    global sessionData
    selection = cmds.ls(selection=True,ap=True)
    if len(selection)==2:
        source = selection[0]
        target = selection[1]
        sourceNamespace = sessionData["sourceRootNamespace"]
        targetNamespace = sessionData["targetRootNamespace"]
        if (sourceNamespace in source) and (targetNamespace in target):
            sourceNoNS = source.split(":")[-1] 
            targetNoNS = target.split(":")[-1]
            existFlag = False
            for pair in sessionData["pair"]:
                if pair == [sourceNoNS,targetNoNS]:
                    existFlag =True
            if existFlag!=True:
                sessionData["pair"].append([sourceNoNS,targetNoNS])
            sourceSidefix = [sessionData["sourceSidefixRight"],sessionData["sourceSidefixLeft"]]
            targetSidefix = [sessionData["targetSidefixRight"],sessionData["targetSidefixLeft"]]
            sourceMirror = None
            targetMirror = None
            for side in sourceSidefix:
                if (side != "")  and (side in sourceNoNS):
                    sideIndex = sourceSidefix.index(side)
                    if sideIndex == 0:
                        sideIndexNeg = 1
                    else:
                        sideIndexNeg = 0
                    
                    sourceMirror = sourceNoNS.replace(sourceSidefix[sideIndex],sourceSidefix[sideIndexNeg])
                    targetMirror = targetNoNS.replace(targetSidefix[sideIndex],targetSidefix[sideIndexNeg])
            if sourceMirror and targetMirror:
                existFlag = False
                for pair in sessionData["pair"]:
                    if pair == [sourceMirror,targetMirror]:
                        existFlag =True
                if existFlag!=True:
                    sessionData["pair"].append([sourceMirror,targetMirror])
        else:
            print("Please select correct with namespaces which you set up!~ :>")
    LoadItem()

def SetPairSameName(*arr):
    global sessionData
    selection = cmds.ls(selection=True,ap=True)
    if len(selection)==1:
        obj = selection[0]
        sourceNoNS = obj.split(":")[-1] 
        targetNoNS = obj.split(":")[-1]
        existFlag = False
        for pair in sessionData["pair"]:
            if pair == [sourceNoNS,targetNoNS]:
                existFlag =True
        if existFlag!=True:
            sessionData["pair"].append([sourceNoNS,targetNoNS])
        sourceSidefix = [sessionData["sourceSidefixRight"],sessionData["sourceSidefixLeft"]]
        targetSidefix = [sessionData["targetSidefixRight"],sessionData["targetSidefixLeft"]]
        sourceMirror = None
        targetMirror = None
        for side in sourceSidefix:
            if (side != "")  and (side in sourceNoNS):
                sideIndex = sourceSidefix.index(side)
                if sideIndex == 0:
                    sideIndexNeg = 1
                else:
                    sideIndexNeg = 0
                
                sourceMirror = sourceNoNS.replace(sourceSidefix[sideIndex],sourceSidefix[sideIndexNeg])
                targetMirror = targetNoNS.replace(targetSidefix[sideIndex],targetSidefix[sideIndexNeg])
        if sourceMirror and targetMirror:
            existFlag = False
            for pair in sessionData["pair"]:
                if pair == [sourceMirror,targetMirror]:
                    existFlag =True
            if existFlag!=True:
                sessionData["pair"].append([sourceMirror,targetMirror])
    LoadItem()
   
def ExportData(*arr):
    data = sessionData
    url = cmds.fileDialog2(dialogStyle=2, fileMode=3, caption="Select Folder")
    if url:
        url = url[0]+"/ScaleMocapData.json"
        writeJsonFile(url,data) 

def ImportData(*arr):
    global sessionData
    url = pm.fileDialog2(fileMode=1)
    if url:     
        sessionData = readJsonFile(url[0])
        LoadData()
        LoadItem()

def LoadData(*arr):
    for name in [
        "sourceRoot","targetRoot","sourceRootNamespace","targetRootNamespace",
        'sourceSidefixRight','sourceSidefixLeft','targetSidefixRight','targetSidefixLeft'
    ]:
        cmds.textField(name,edit=True,text=str(sessionData[name]))

def SelectRoot(RootType,*arr):
    global sessionData
    selection = cmds.ls(selection=True)
    if selection:
        obj = selection[0]
        objArray = obj.split(":")
        if len(objArray)==2:
            sessionData[RootType] = objArray[-1]
            sessionData[RootType+"Namespace"]= objArray[0]
        else:
            sessionData[RootType] = obj
            sessionData[RootType+"Namespace"]= ""
    LoadData()
    
def UpdateSidefix(inputName,*arr):
    global sessionData
    sessionData[inputName] = cmds.textField(inputName,query=True,text=True)
    
def UpdateScale(*arr):
    value = round(cmds.floatSlider("ScaleValue",query=True,value=True),4)
    cmds.textField("ScaleValueShow",text=value,edit=True)

def BakeAnimation(*arr):
    targetList = []
    for i in range(len(sessionData["pair"])):
        if sessionData["targetRootNamespace"]!= "":
            targetList.append(sessionData["targetRootNamespace"]+":"+sessionData["pair"][i][1])
        else:
            targetList.append(sessionData["pair"][i][1])
        
    start = cmds.playbackOptions(q=True, min=True)
    end = cmds.playbackOptions(q=True, max=True)

    cmds.bakeResults(
        targetList,
        simulation=True,
        t=(start, end),
        sampleBy=1,
        disableImplicitControl=True,
        preserveOutsideKeys=False,
        sparseAnimCurveBake=False,
        removeBakedAttributeFromLayer=False,
        bakeOnOverrideLayer=False,
        minimizeRotation=True,
        controlPoints=False,
        shape=True
        )


def CreateWindow():
    global sessionData
    sessionData["input"] = {}

    if cmds.window("NLTA_ScaleMocap", exists=True):
        cmds.deleteUI("NLTA_ScaleMocap", window=True)
    
    window = cmds.window("NLTA_ScaleMocap", title="Scale MoCap")    
    cmds.columnLayout(adjustableColumn=True,width=300)
    
    cmds.rowColumnLayout(adjustableColumn=True,width=290,numberOfColumns=4)
    cmds.textField("sourceRoot",width=125,editable=False,pht="Source Root")
    cmds.button( label='>',width=25,c=partial(SelectRoot,"sourceRoot"))
    cmds.textField("targetRoot",width=125,editable=False,pht="Target Root")
    cmds.button( label='>',width=25,c=partial(SelectRoot,"targetRoot"))
    cmds.setParent( '..' )
    
    cmds.rowColumnLayout(adjustableColumn=True,width=290,numberOfColumns=2)
    cmds.textField(width=120,editable=False,pht="Source Namespace:")
    cmds.textField("sourceRootNamespace",width=180)
    cmds.textField(width=120,editable=False,pht="Target Namespace:")
    cmds.textField("targetRootNamespace",width=180)
    cmds.setParent( '..' )
            
    cmds.rowColumnLayout(adjustableColumn=True,width=290,numberOfColumns=3)
    cmds.textField(width=100,editable=False,pht="Source SideFix")
    cmds.textField("sourceSidefixRight",width=100,pht="Right",tcc=partial(UpdateSidefix,"sourceSidefixRight"))
    cmds.textField("sourceSidefixLeft",width=100,pht="Left",tcc=partial(UpdateSidefix,"sourceSidefixLeft"))
    cmds.textField(width=100,editable=False,pht="Target SideFix")
    cmds.textField("targetSidefixRight",width=100,pht="Right",tcc=partial(UpdateSidefix,"targetSidefixRight"))
    cmds.textField("targetSidefixLeft",width=100,pht="Left",tcc=partial(UpdateSidefix,"targetSidefixLeft"))
    cmds.setParent( '..' )

    cmds.separator(height=10, style='in')
    

    cmds.rowColumnLayout(adjustableColumn=True,width=290,numberOfColumns=2)
    cmds.textField(text="List to match",width=250,editable=False)
    cmds.button( label='+',width=50,c=SetPair)
    cmds.button( label='+ Same Name',width=50,c=SetPairSameName)
    cmds.setParent( '..' )
    
    cmds.scrollLayout("NLTA_ItemList",horizontalScrollBarThickness=16,verticalScrollBarThickness=16,height=500)#open scroll
    cmds.setParent( '..' )
    
    cmds.rowColumnLayout(adjustableColumn=True,width=300,numberOfColumns=2)
    cmds.button( label='Import',width=150,c=ImportData)
    cmds.button( label='Export',width=150,c=ExportData)
    cmds.setParent( '..' )
    
    cmds.rowColumnLayout(adjustableColumn=True,width=300,numberOfColumns=2)
    cmds.button( label='Clear Tool Setting',width=150,c=ClearToolSetting)
    cmds.button( label='Create Connect',width=150,c=CreateConnect)
    cmds.button( label='Bake Animation',width=150,c=BakeAnimation)
    cmds.setParent( '..' )
    
    """
    cmds.rowColumnLayout(adjustableColumn=True,width=300,numberOfColumns=3)
    cmds.textField(text="Scale",width=50,editable=False)
    cmds.floatSlider("ScaleValue",min=0, max=10, value=1, step=0.1,sbm=True,width=150,dc=UpdateScale)
    cmds.textField("ScaleValueShow",text="1",width=100,editable=False)
    cmds.setParent( '..' )
    """
    
    cmds.setParent( '..' )      
    cmds.showWindow( window )
    #LoadItem()
      
CreateWindow()

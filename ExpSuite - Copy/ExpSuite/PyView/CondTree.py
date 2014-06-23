import wx
from framework import *
import  wx.lib.rcsizer  as Table

# Constructor map for Conditions
typesMap = {'Null':Conditions.NullCon, 'Time Limit':Conditions.TimeLimit, 
            'Max Trials':Conditions.TrialsLimit, 'Max Rewards':Conditions.RewardsLimit, 
            'Max Consecutive Rewards':Conditions.ConRwLimit, 'Random Switch':Conditions.BiasRandom, 
            'Not':Conditions.Noty, 'Or':Conditions.Ory, 'And':Conditions.Andy, 'Xor':Conditions.Xory}

def createTreePanel(parent,clist,mc=None):
    """Return wx.Panel that is used to make/edit conditional trees"""
    tp = TreePanel(parent,mc)
    tp.makeUseTypes(clist)
    return tp

class TreePanel(wx.Panel):
    """Extends Panel for tree control widgets"""
    def __init__(self,parent,mc):
        wx.Panel.__init__(self,parent)
        # Make components
        typeText = wx.StaticText(self,-1,"Condition Type:")
        self.typeField = wx.Choice(self,-1)
        self.useTypes = []
        self.willow = Conditions.NullCon()
        self.limitText = wx.StaticText(self,-1,"Limit:")
        self.limitField = wx.TextCtrl(self,value="0")
        
        self.tree = wx.TreeCtrl(self, 1, wx.DefaultPosition, (200,100), wx.TR_DEFAULT_STYLE)
        self.treeMap = []
        self.willow = mc
        self.buildTree()
        self.activeNode = None
        
        # Bind components
        self.Bind(wx.EVT_CHOICE, self.handleTopSelect, self.typeField)
        self.Bind(wx.EVT_TREE_SEL_CHANGED, self.OnTreeSel, self.tree)
        self.Bind(wx.EVT_TEXT, self.onLimitChange, self.limitField)
        #self.Bind(wx.EVT_BUTTON,self.printMC, printbtn)
        
        # Add components to sizer
        tbl = Table.RowColSizer()
        tbl.SetMinSize((200,-1))
        tbl.Add(typeText,row=1,col=1)
        tbl.Add(self.typeField,row=1,col=2)
        tbl.Add(self.limitText,row=2,col=1)
        tbl.Add(self.limitField,row=2,col=2)
        tbl.Add(self.tree,row=3,col=1,colspan=2,rowspan=2)
        self.SetSizerAndFit(tbl)
    
    def makeUseTypes(self,condylist):
        """Add used Condition types in this panel to the pulldown menu
        condylist: list of Condition objects
        """
        for c in condylist:
            self.typeField.Append(c.type)
            self.useTypes.append(c.type)
        self.typeField.Select(0)

    def binder(self,body,mind):
        """ Binds the index ID to each node in tree
        Args:
            body: TreeCtrl node
            mind: index in treeMap array
        """
        i = len(self.treeMap)
        self.tree.SetPyData(body,i)
        self.treeMap.append(mind)
    
    def expandSubtree(self,po,node):
        """Create create subtree from node
        Args:
             po: parent node
             node: node to add to TreeCtrl
         """
        if po:
            if node.leaf:
                body = self.tree.AppendItem(po,node.toString())
            else:
                body = self.tree.AppendItem(po,node.type)
        else:
            if node.leaf:
                body = self.tree.AddRoot(node.toString())
            else:
                body = self.tree.AddRoot(node.type)
        self.binder(body, node)
        if not(node.leaf):
            self.expandSubtree(body, node.c1)
            if not(isinstance(node, Conditions.Noty)):
                self.expandSubtree(body, node.c2)        
    
    
    def buildTree(self):
        """Build TreeCtrl from a Condition tree or constructs a Null root if it == None"""
        if self.willow:
            self.expandSubtree(None, self.willow)
        else:
            root = self.tree.AddRoot('Null')
            self.binder(root,Conditions.NullCon())
    
    def OnTreeSel(self, event):
         """Responds when a node on the TreeCtrl is selected"""
         self.activeNode =  self.tree.GetSelection()
         key = self.tree.GetPyData(self.activeNode)
         val = self.treeMap[key]
         if val:
            ind = 0
            try:
                 ind = self.useTypes.index(val.type)
                 self.typeField.Select(ind)
            except ValueError:
                pass
            if issubclass(val.__class__, Conditions.Ender) and not(isinstance(val,Conditions.NullCon)):
                 self.limitText.Show(True)
                 self.limitField.Show(True)
                 self.limitField.SetValue(str(val.limit))
         else:
             self.typeField.Select(0)
             self.limitText.Show(False)
             self.limitField.Show(False)      
    
    def handleTopSelect(self,evt):
        """Responds when we make selection from dropdown menu"""
        cstr = evt.GetString()
        cobj = typesMap[cstr]()
        if issubclass(cobj.__class__, Conditions.Ender):
            if isinstance(cobj,Conditions.NullCon):
                self.limitText.Show(False)
                self.limitField.Show(False)
                if self.activeNode:
                    self.tree.DeleteChildren(self.activeNode)
                    self.tree.SetItemText(self.activeNode,'Null')
            else:
                self.limitText.Show(True)
                self.limitField.Show(True)
                self.addConds(cobj)
        else:
            self.limitText.Show(False)
            self.limitField.Show(False)
            self.addConds(cobj)
    
    def addConds(self, state=None):
        """Figure out how to create new node and where to place it"""
        sel = self.activeNode
        if not(sel):
            sel = self.tree.GetRootItem()
        key = self.tree.GetPyData(sel)
        self.tree.DeleteChildren(sel)
        if issubclass(state.__class__,Conditions.Klaus):
            state.setNull()
            self.tree.SetItemText(sel,state.type)
            
            c1 = self.tree.AppendItem(sel,state.c1.type)
            self.binder(c1,state.c1)
            
            if issubclass(state.__class__,Conditions.Bik):
                c2 = self.tree.AppendItem(sel,state.c2.type)
                self.binder(c2,state.c2)
            
        elif issubclass(state.__class__, Conditions.Ender) and not(isinstance(state,Conditions.NullCon)):
            pval = float(self.limitField.GetValue())
            if issubclass(state.__class__,Conditions.Inter):
                pval = int(pval)
            state.limit = pval
            state.parent = self.treeMap[key].parent
            self.tree.SetItemText(sel,state.toString())
            self.activeNode = sel
        else:
            pass
        if self.treeMap[key].parent:
            self.treeMap[key].morph(state)
        self.treeMap[key] = state
            
    def onLimitChange(self,evt):
        """Responds to limit text field"""
        sel = self.activeNode
        if not(sel):
            sel = self.tree.GetRootItem()
        key = self.tree.GetPyData(sel)
        c = self.treeMap[key]
        if c:
            try:
                c.limit = float(self.limitField.GetValue())
                if not(isinstance(c, Conditions.TimeLimit)) and not(isinstance(c, Conditions.BiasRandom)):
                    c.limit = int(c.limit)
                self.tree.SetItemText(sel,c.toString())
            except ValueError:
                pass
    
    def saveWillow(self):
        """Turn TreeCtrl tree into Conditions tree"""
        sel = self.tree.GetRootItem()
        key = self.tree.GetPyData(sel)
        self.willow = self.treeMap[key]
        if isinstance(self.willow, Conditions.NullCon):
            self.willow = None
    
    def printMC(self,evt):
        """print Master Conditions tree"""
        self.saveWillow()
        print self.willow.toString()
       
    def getMasterCondition(self):
        """Get Condition Tree """
        self.saveWillow()
        return self.willow

    def setMasterCondition(self,condi):
        """Set Condition Tree"""
        self.willow = condi

def testRun():
    """test TreePanel function"""
    app = wx.App(False)
    frame = wx.Frame(None,-1,"Condition Tree Editor",size=(300, 400))
    clist = [Conditions.NullCon(), Conditions.TimeLimit(), 
            Conditions.TrialsLimit(),Conditions.RewardsLimit(), 
            Conditions.ConRwLimit(), Conditions.BiasRandom(), 
            Conditions.Noty(), Conditions.Ory(), Conditions.Andy(), Conditions.Xory()]
    frame.panel = createTreePanel(frame,clist)
    frame.Centre()
    frame.Show(True)
    app.MainLoop()
#testRun()
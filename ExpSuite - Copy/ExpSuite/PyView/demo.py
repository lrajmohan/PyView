__author__ = 'raj'

'''
import time
a = False
if not(a):
 print time.clock()

import wx

class StaticTextFrame(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, None, -1, 'Static Text Example', size=(400, 300))
        panel = wx.Panel(self, -1)
        wx.StaticText(panel, -1, "This is an example of static text", (100, 10))
        center = wx.StaticText(panel, -1, "align centeralign centeralign center", (100, 50), (160, -1), wx.ALIGN_CENTER)
        center.SetForegroundColour('white')
        center.SetBackgroundColour('black')
        if 2%2 ==0:
          f = center.SetLabel("hellllooooooo")

app = wx.PySimpleApp()
frame = StaticTextFrame()
frame.Show()
app.MainLoop()

for num in range(10,20):
    print(num)

    '''


dict = {'Name': 'Zara', 'Age': 7, 'Class': 'First'};

print "dict['Name']: ", dict[1];
print "dict['Age']: ", dict['Age'];
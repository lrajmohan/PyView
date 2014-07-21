import math

ToneNames = ['Freq.1','Freq.2','Freq.3', 'Freq.4']
ToneFreq = [2000,4000,4200,8000]

ttlMap = {'Lever Press': '00000200', 'Mark Time':'00000400','New Trial':'00000800', 'Pulse':'00001000',
          'Valve 1':'00000001','Valve 2':'00000002','Valve 3':'00000004','Valve 4':'00000008', 'Valve 5':'00000010',
          'Freq1':'00000020','Freq2':'00000040','Freq3':'00000080', 'Freq4':'00000100'}

TasteNames = ['Valve 1','Valve 2','Valve 3', 'Valve 4','Valve 5']
TasteColors= ["#6666FF","#c16fd6","#b73bd6","#ad08d6","#a55fb7"]

iColors = {'Wait':'#aeaeae','Tone':'#00ff00','Reward':'#FF9966','Nogo':'#FFFF99'}
aColors = {'Taste':'#FF9999','Restart':'#009966','Jump':'#3366FF','ChangeIntDur':'#669999','SwitchJump':'#667788'}

HEX = '0123456789abcdef'

# convert Hexcolor code to RGB
def rgb(triplet):
    if '#' in triplet:
        triplet = triplet[1:]
    triplet = triplet.lower()
    return (HEX.index(triplet[0])*16 + HEX.index(triplet[1]),
            HEX.index(triplet[2])*16 + HEX.index(triplet[3]),
            HEX.index(triplet[4])*16 + HEX.index(triplet[5]))
# helper function for rgb()
def triplet(rgb):
    return hex(rgb[0])[2:] + hex(rgb[1])[2:] + hex(rgb[2])[2:]

# convert RGB to Hexcolor
def rgbHexcode(rgb):
    hexi ='#'
    for c in rgb:
        ch = hex(c)
        ch = ch[2:]
        ch = ch.rjust(2,'0')
        hexi+=ch

    return hexi

# Figure out the frequency color in the scale [lime-aqua]
def freq2color(freq):
    f = int((freq-960)/40)
    b = int(math.floor(f/18))
    b*=18
    rs = int(f*150/255)
    rs - 150 - rs
    r = int(math.floor(rs/11))
    r*=11
    return rgbHexcode((r,255,b))

# RC_Remote_client_UDP by Wayne Andrews, aka CurryKitten, released 17/03/2013
#
# Simple program to take input from a 4 axis joystick (this is built around a PS3 controller), show the display
# of the sticks graphically, and then send this information as percentage references over a UDP socket to a server
# process which will create a PPM signal from them and send them to an RC tx via an Arduino board
#
# It should be run from the command line as -
#     python RC_Remote_client_UDP.py remote-ip-address remote-port
#
# Where remote-ip-address is the ip or hostname of the host you want to connect to, and remote-port is the UDP
# port number.  If these aren't specified then there are defaults - which you should alter to cater to your own
# config.
#
# There is much to fix and basically make to work better

import sys
import pygame
import struct
from socket import *

def curAxis(axisNum):
    if (axisNum == 0):
        return "L stick X Axis"
    if (axisNum == 1):
        return "L stick Y Axis"
    if (axisNum == 2):
        return "R stick X Axis"
    if (axisNum == 3):
        return "R stick Y Axis"
    if (axisNum == 4):
        return "Unassigned"


# Define some colors
black    = (   0,   0,   0)
white    = ( 255, 255, 255)
ltgrey   = ( 75, 75, 75)
ltgrey2  = ( 150, 150, 150)
green    = (   0, 255,   0)
red      = ( 255,   0,   0)

# Using a default host and port number, unless this is overridden by arguments
remHost = '82.21.21.19'
remPort = 6666

# Override the defaults
if (len(sys.argv) > 1):
    if (sys.argv[1]):
        remHost = sys.argv[1]
    if (len(sys.argv) > 2):
        if (sys.argv[2]):
            remPort = sys.argv[2]

print "Connecting to " + remHost + " on port " + str(remPort)
remAddr = (remHost, remPort)
remSock = socket(AF_INET, SOCK_DGRAM)

pygame.init()
clock=pygame.time.Clock()

# Some debug just to ensure we've found an appropriate joystick
if (pygame.joystick.get_init()):
    print "Joystick is initialised"
else:
    print "Joystick not initialised"
    
numJoys = pygame.joystick.get_count()
print "Number of joysticks: " + str(numJoys)
joy = pygame.joystick.Joystick(numJoys - 1)
joy.init()
    
joyAxis = joy.get_numaxes()
print "Joystick name: ." + joy.get_name() + "."
print "Num of axis: " + str(joyAxis)

# Set the width and height of the screen [width,height]
size=[640,480]
screen=pygame.display.set_mode(size)
pygame.display.set_caption("Transmitter Stick display - Client")
done=False

# Hold the positions of the sticks on the screen
ch1pos=0
ch2pos=0
ch3pos=0
ch4pos=0
chstring=""

# Array containing the list of PPM values
channel = [7568, 1079, 1079, 1079, 1079, 1079, 1079, 1079, 1079]

# The raw axis values for the joystick        
joyAxisValue = [0.0, 0.0, 0.0, 0.0]
joyAxisAssign = [0, 1, 2, 3]

# The percentage values of the joystick
percent = [0.0, 0.0, 0.0, 0.0]

# Previous percentage values - only send if they've changed
prevpercent = [0, 0, 0, 0]


# -------- Main Program Loop -----------
while done==False:
    # ALL EVENT PROCESSING SHOULD GO BELOW THIS COMMENT
    for event in pygame.event.get(): # User did something
        if event.type == pygame.QUIT: # If user clicked close
            done=True
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                done=True
            elif event.key == pygame.K_1:
                if (joyAxisAssign[0] == 4):
                    joyAxisAssign[0] = 0
                else:
                    joyAxisAssign[0] = joyAxisAssign[0] + 1
            elif event.key == pygame.K_2:
                if (joyAxisAssign[1] == 4):
                    joyAxisAssign[1] = 0
                else:
                    joyAxisAssign[1] = joyAxisAssign[1] + 1
            elif event.key == pygame.K_3:
                if (joyAxisAssign[2] == 4):
                    joyAxisAssign[2] = 0
                else:
                    joyAxisAssign[2] = joyAxisAssign[2] + 1
            elif event.key == pygame.K_4:
                if (joyAxisAssign[3] == 4):
                    joyAxisAssign[3] = 0
                else:
                    joyAxisAssign[3] = joyAxisAssign[3] + 1
    
    # Read the joystick axis positions (range of -1 to 1)
    for i in range(joyAxis):
        # Now correct the joystick Axis, as these seem to vary on every joystick
        if (joyAxisAssign[i] != 4):
            joyAxisValue[joyAxisAssign[i]] = joy.get_axis(i)   
            
            # With the PS3 sticks, I found it necessary to invert most of the axis 
            if (joy.get_name() == "PLAYSTATION(R)3 Controller"):
                if (i != 2):
                    joyAxisValue[i] = joyAxisValue[i] * -1
                    
            percent[joyAxisAssign[i]] = (joyAxisValue[joyAxisAssign[i]] * 50) + 50
        
    # Lots of debug to check our positional data in multiple representation
    percentstring = "S1A1%: " + str(int(percent[0])) + " S1A2%: " + str(int(percent[1])) + " S2A1%: " + str(int(percent[2])) + " S2A2%: " + str(int(percent[3]))
    
    # Check that our percentage value has changed - else we are sending data for no reason
    if (int(percent[0]) != prevpercent[0] or 
        int(percent[1]) != prevpercent[1] or 
        int(percent[2]) != prevpercent[2] or 
        int(percent[3]) != prevpercent[3]):
        prevpercent[0] = int(percent[0])
        prevpercent[1] = int(percent[1])
        prevpercent[2] = int(percent[2])
        prevpercent[3] = int(percent[3])
        
        # Need to pack the 6 bytes together to send as a single packet
        # Use 0xff to indicate a start of the data stream, and 0xfe to complete it
        myPacket = struct.pack("BBBBBB", 255, prevpercent[0], prevpercent[1], prevpercent[2], prevpercent[3], 254)
        remSock.sendto(myPacket, remAddr)
    
    # The Axis don't correspond to the right channel numbers, so correct these
    for i in range(4):
        ch = 0 
        if (i == 0):
            ch = 4
        if (i == 1):
            ch = 3
        if (i == 2):
            ch = 1
        if (i == 3):
            ch =2
        
        # Apply a scaling calculation to work out PPM value, note that there's a different range above and below mid stick
        if (percent [i] <= 50):
            channel[ch] = int(percent[i] * 8.28 + 665)
        else:
            channel[ch] = int((percent[i] - 50) * 7.22 + 1079)
        
    # Channel 0 is the sync pulse, calculate this relative to the other channel values so the full frame is 16200
    channel[0] = 16200 - (channel[1] + channel[2] + channel[3] + channel[4] + channel[5] + channel[6] + channel[7] + channel[8])
    # ALL GAME LOGIC SHOULD GO BELOW THIS COMMENT

    chstring = "SYNC: " + str(channel[0]) + " CH1:" + str(channel[1]) + " CH2:" + str(channel[2]) + " CH3:" + str(channel[3]) + " CH4:" + str(channel[4])

    # Work out the screen position of the sticks
    ch1pos = 475 - ((150/float(820)) * (1450 - int(channel[1])))
    ch2pos = 100 + ((150/float(820)) * (1450 - int(channel[2])))
    ch3pos = 100 + ((150/float(820)) * (1450 - int(channel[3])))
    ch4pos = 125 + ((150/float(820)) * (1450 - int(channel[4])))

    # Create the text strings to blit to our screen
    S1A1String = "(1) Stick 1 Axis 1 : " + curAxis(joyAxisAssign[0])
    S1A2String = "(2) Stick 1 Axis 2 : " + curAxis(joyAxisAssign[1])
    S2A1String = "(3) Stick 2 Axis 1 : " + curAxis(joyAxisAssign[2])
    S2A2String = "(4) Stick 2 Axis 2 : " + curAxis(joyAxisAssign[3])

    # Setup text to print
    font = pygame.font.SysFont("monospace", 20)
    text = font.render(chstring,True,white)
    text3 = font.render(percentstring, True, white)
    S1A1Text = font.render(S1A1String,True,white)
    S1A2Text = font.render(S1A2String,True,white)
    S2A1Text = font.render(S2A1String,True,white)
    S2A2Text = font.render(S2A2String,True,white)
    

    # The draw loop - Pygame likes to keep this all together
    screen.fill(black)
    pygame.draw.rect(screen, white, [80,20,440,380],2)
    pygame.draw.rect(screen, white, [125,100,150,150],2)
    pygame.draw.rect(screen, white, [325,100,150,150],2)
    pygame.draw.circle(screen, white, [200,175], 75, 2)
    pygame.draw.circle(screen, white, [400,175], 75, 2)
    pygame.draw.circle(screen, white, [int(ch4pos),int(ch3pos)], 10, 2)
    pygame.draw.circle(screen, white, [int(ch1pos),int(ch2pos)], 10, 2)
    screen.blit(text, [60,455])
    screen.blit(text3, [70,415])
    screen.blit(S1A1Text, [90,280])
    screen.blit(S1A2Text, [90,300])
    screen.blit(S2A1Text, [90,320])
    screen.blit(S2A2Text, [90,340])
    
    # End of the draw loop
     
    # Go ahead and update the screen with what we've drawn.
    pygame.display.flip()
 
    # Limit to 30 frames per second
    clock.tick(30)
         
# Close the window and quit.
pygame.quit ()


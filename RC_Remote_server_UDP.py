# RC_Remote_server_UDP by Wayne Andrews, aka CurryKitten, released 17/03/2013
#
# This code sets up a simple UDP server and takes reads client joystick input from the socket which is
#Êconverted to PPM and sent over the serial port to an Arduino card which in turns needs to be connected
# to an RC transmitter.
#
# This code should be altered to your own machine so that the serial port the Arduino card is on, and the
# IP address to listen on are your own, you can also change the port number if you like
#
# It should be run from the command line as -
#     python RC_Remote_server_UDP.py 
#

import serial
import serial.tools.list_ports
import struct
from socket import *
import pygame

# Define some colors
black    = (   0,   0,   0)
white    = ( 255, 255, 255)
ltgrey   = ( 75, 75, 75)
ltgrey2  = ( 150, 150, 150)
green    = (   0, 255,   0)
red      = ( 255,   0,   0)

# The serial interface is going to change on a system to system basis, and may change on the same machine
print "Available Serial Ports:"
print serial.tools.list_ports.comports()
ser = serial.Serial('/dev/tty.usbmodemfd141', 9600) 

# Print more stuff out if debuging
debug = False

# Lets get a socket to listen on
myHost = '192.168.1.100'
myPort = 6666
buff = 1024
myAddr = (myHost, myPort)
serversock = socket(AF_INET, SOCK_DGRAM)
serversock.bind(myAddr)
serversock.setblocking(0)

        
pygame.init()
clock=pygame.time.Clock()

# Set the width and height of the screen [width,height]
size=[640,480]
screen=pygame.display.set_mode(size)
pygame.display.set_caption("Transmitter Stick display - Server")
done=False

# Hold the positions of the sticks on the screen
ch1pos=0
ch2pos=0
ch3pos=0
ch4pos=0
chstring=""

# Array containing the list of PPM values
channel = [7568, 1079, 1079, 1079, 1079, 1079, 1079, 1079, 1079]

# The percentage values of the joystick
percent = [0.0, 0.0, 0.0, 0.0]

# Previous percentage values - only send if they've changed
prevpercent = [0, 0, 0, 0]

# String to hold the value for debug
percentstring = ""

# Varaibles to hold whether the axis of the joysticks are reversed 
lxReversal = False
lyReversal = False
rxReversal = False
ryReversal = False

# Add a dual rate for the throttle, 100 is full range, 50 is half etc
scaleThrottle = 50

# Add a dual rate the other way for turning, as the diagonal is rounded on PSX joysticks
# meaning you can't do a full lock to steer and apply throttle, so 75 would mean only
# 75% of the stick movement would give 100% of the actual value

scaleSteering = 100

# How we quit out of Pygame
while done==False:
    # ALL EVENT PROCESSING SHOULD GO BELOW THIS COMMENT
    for event in pygame.event.get(): # User did something
        if event.type == pygame.QUIT: # If user clicked close
            done=True
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                done=True
            elif event.key == pygame.K_1:
                if (lxReversal):
                    lxReversal = False
                else:
                    lxReversal = True
            elif event.key == pygame.K_2:
                if (lyReversal):
                    lyReversal = False
                else:
                    lyReversal = True
            elif event.key == pygame.K_3:
                if (rxReversal):
                    rxReversal = False
                else:
                    rxReversal = True
            elif event.key == pygame.K_4:
                if (ryReversal):
                    ryReversal = False
                else:
                    ryReversal = True
            elif event.key == pygame.K_i:
                if (scaleThrottle < 100):
                    scaleThrottle = scaleThrottle + 5
            elif event.key == pygame.K_d:
                if (scaleThrottle > 25):
                    scaleThrottle = scaleThrottle - 5
            elif event.key == pygame.K_a:
                if (scaleSteering < 200):
                    scaleSteering = scaleSteering + 5
            elif event.key == pygame.K_r:
                if (scaleSteering > 100):
                    scaleSteering = scaleSteering - 5
               
    
    # Read the UDP socket to get Joystick percentages
    try:
        UDPStuff = serversock.recvfrom(buff)
        data = UDPStuff[0]
        fromAddr = UDPStuff[1]
        if (len(data) >= 6):
            if (len(data) > 6):
                print "Discarding " + str((len(data)-6) / 6) + " earlier messages"
                data = data[-6:] 
            # Our data should be 6 bytes in length, with the format 255 stick1x% stick1y% stick2x% stick2y% 254
            print struct.unpack("BBBBBB", data)
            byteArray = struct.unpack("BBBBBB", data)
            if (byteArray[0] == 255 and byteArray[5] == 254):
                percent[0] = byteArray[1]
                percent[1] = byteArray[2]
                percent[2] = byteArray[3]
                percent[3] = byteArray[4]
            else:
                print "Incorrect packet Header/Footer, ignoring"
        else:
            print "Packet length of " + str(len(data)) + " recieved, ignoring"
        
        # Handle any channel reversals
        if (lxReversal):
            percent[0] = 100 - percent[0]
        if (lyReversal):
            percent[1] = 100 - percent[1]
        if (rxReversal):
            percent[2] = 100 - percent[2]
        if (ryReversal):
            percent[3] = 100 - percent[3]    
        
        # Decide if we need to calculate a scaled throttle percentage based on our dual rate
        if (scaleThrottle != 100):
            if (percent[3] < 50):
                newThrottle = 50.0 - float(percent[3])
                newThrottle = 50 - (newThrottle / 100) * scaleThrottle
                percent[3] = int(newThrottle)
            if (percent[3] > 50):
                newThrottle = float(percent[3]) - 50
                newThrottle = ((newThrottle / 100) * scaleThrottle) + 50
                percent[3] = int(newThrottle)

        # Check if we need to use the dual rate on the steering (but in the other way to throttle)
        if (scaleSteering != 100):
            if (percent[2] < 50):
                newSteer = 50.0 - float(percent[2])
                newSteer = 50 - (newSteer / 100) * scaleSteering
                percent[2] = int(newSteer)
            if (percent[2] > 50):
                newSteer = float(percent[2]) - 50
                newSteer = ((newSteer / 100) * scaleSteering) + 50
                percent[2] = int(newSteer)
                
            # Do some bounds checking on the new calculated percentage 
            if (percent[2] > 100):
                percent[2]= 100
            if (percent[2] < 0):
                percent[2] = 0

        # Lots of debug to check our positional data in multiple representation
        percentstring = "LX%: " + str(int(percent[0])) + " LY%: " + str(int(percent[1])) + " RX%: " + str(int(percent[2])) + " RY%: " + str(int(percent[3]))
    
    
        # Check that our percentage value has changed - else we are sending data for no reason
        if (int(percent[0]) != prevpercent[0] or 
            int(percent[1]) != prevpercent[1] or 
            int(percent[2]) != prevpercent[2] or 
            int(percent[3]) != prevpercent[3]):
            prevpercent[0] = int(percent[0])
            prevpercent[1] = int(percent[1])
            prevpercent[2] = int(percent[2])
            prevpercent[3] = int(percent[3])
            # Use ff to indicate a start of the data stream, and fe to complete it
            ser.write(bytes(chr(255)))
            ser.write(bytes(chr(prevpercent[0])))
            ser.write(bytes(chr(prevpercent[1])))
            ser.write(bytes(chr(prevpercent[2])))
            ser.write(bytes(chr(prevpercent[3])))
            ser.write(bytes(chr(254)))
    
        # The Axis don't corraspond to the right channel numbers, so correct these
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
    
    # We need to ignore exceptions from this block, as they should be assosiated with no data coming in, so rather than 
    # block, python raises a timeout exception    
    except:
        pass
        
        
    # Channel 0 is the sync pulse, calculate this relative to the other channel values so the full frame is 16200
    channel[0] = 16200 - (channel[1] + channel[2] + channel[3] + channel[4] + channel[5] + channel[6] + channel[7] + channel[8])
    chstring = "SYNC: " + str(channel[0]) + " CH1:" + str(channel[1]) + " CH2:" + str(channel[2]) + " CH3:" + str(channel[3]) + " CH4:" + str(channel[4])
    
    # Create the text strings to blit to our screen
    lxString = "(1) Left Stick X axis : "
    if (lxReversal):
        lxString = lxString + "Reversed"
    else:
        lxString = lxString + "Normal"
    
    lyString = "(2) Left Stick Y axis : "
    if (lyReversal):
        lyString = lyString + "Reversed"
    else:
        lyString = lyString + "Normal"
        
    rxString = "(3) Right Stick X axis: "
    if (rxReversal):
        rxString = rxString + "Reversed"
    else:
        rxString = rxString + "Normal"
        
    ryString = "(4) Right Stick Y axis: "
    if (ryReversal):
        ryString = ryString + "Reversed"
    else:
        ryString = ryString + "Normal"
        
    scaleThString = "(i)ncrease/(d)ecrease Throttle Dual Rate: " + str(scaleThrottle)
    scaleStString = "(a)dd/(r)educe Steering Duale Rate      : " + str(scaleSteering)
    # Work out the screen position of the sticks
    ch1pos = 475 - ((150/float(820)) * (1450 - int(channel[1])))
    ch2pos = 100 + ((150/float(820)) * (1450 - int(channel[2])))
    ch3pos = 100 + ((150/float(820)) * (1450 - int(channel[3])))
    ch4pos = 125 + ((150/float(820)) * (1450 - int(channel[4])))

    # Setup text to print
    font = pygame.font.SysFont("monospace", 20)
    text = font.render(chstring,True,white)
    text3 = font.render(percentstring, True, white)
    lxText = font.render(lxString,True,white)
    lyText = font.render(lyString,True,white)
    rxText = font.render(rxString,True,white)
    ryText = font.render(ryString,True,white)
    scaleThText = font.render(scaleThString,True,white)
    scaleStText = font.render(scaleStString,True,white)

    # Draw the radio, stick positions and the text
    # Pygame is very fussy about having it's draw loop, which starts here
    screen.fill(black)
    pygame.draw.rect(screen, white, [80,20,440,380],2)
    pygame.draw.rect(screen, white, [125,100,150,150],2)
    pygame.draw.rect(screen, white, [325,100,150,150],2)
    pygame.draw.circle(screen, white, [200,175], 75, 2)
    pygame.draw.circle(screen, white, [400,175], 75, 2)
    pygame.draw.circle(screen, white, [int(ch4pos),int(ch3pos)], 10, 2)
    pygame.draw.circle(screen, white, [int(ch1pos),int(ch2pos)], 10, 2)
    if (debug):
        screen.blit(text, [60,455])
        screen.blit(text3, [70,415])
        
    screen.blit(lxText, [100,280])
    screen.blit(lyText, [100,300])
    screen.blit(rxText, [100,320])
    screen.blit(ryText, [100,340])
    screen.blit(scaleThText, [50,420])
    screen.blit(scaleStText, [50,440])
        
    # The end of Pygames draw loop
     
    # Go ahead and update the screen with what we've drawn.
    pygame.display.flip()
 
    # Limit to 30 frames per second
    clock.tick(30)
         
# On close of the program, close the sockets, and quit pygame
serversock.close()
pygame.quit ()
#!/usr/bin/env python
#
# Test SDL_DS3231
# John C. Shovic, SwitchDoc Labs
# 08/03/2014
#
#

# imports

import sys
import time
import datetime
import random
import SDL_DS3231

# Main Program

print ("Test SDL_DS3231 Version 1.1 - SwitchDoc Labs")
print ("HAPI SDL_DS3231 Version 1.0 - John Archbold")
print ("Modified for cheap DS3231 modules with eeprom address = 0x57")
print ("Program Started at: "+ time.strftime("%Y-%m-%d %H:%M:%S"))
print ("")

filename = time.strftime("%Y-%m-%d%H:%M:%SRTCTest") + ".txt"
starttime = datetime.datetime.utcnow()

## Initialize DS3231 board (with on-board AT24C32)
ds3231 = SDL_DS3231.SDL_DS3231(1, 0x68, 0x57)
print ("DS3231 RTC= 0x%x" % (ds3231._addr))
print ("DS3231 EEP= 0x%x" % (ds3231._at24c32_addr))

#Change to ''True' on the next line to initialize the clock
if False:
    print ("Setting the time")
    ds3231.write_now()

# Main Loop - sleeps 10 seconds, then reads and prints values of all clocks
# Also reads two bytes of EEPROM and writes the next value to the two bytes

# do the AT24C32 eeprom
# Note that the eeprom has a limited number of write cycles
# See the data sheet for more information
# Change to ''True'' on the next line to test the EEPROM
if False:
    print ("Test the AT24C32 EEPROM")
    print ("  writing 16 addresses with random data")
    for x in range(0, 16):
        value = random.randint(0, 255)
        print ("address = %i writing value=%i" % (x, value))
        ds3231.write_AT24C32_byte(x, value)
    print ("  reading 16 addresses")
    for x in range(0, 16):
        print ("address = %i value = %i" % (x, ds3231.read_AT24C32_byte(x)))


while True:
    currenttime = datetime.datetime.utcnow()
    deltatime = currenttime - starttime
    print ("")
    print ("Pi     Time\t" + time.strftime("%Y-%m-%d %H:%M:%S"))
    print ("DS3231 Time\t%s" % ds3231.read_datetime())
    print ("DS3231 Temp\t%5.2f" % ds3231.getTemp())
    time.sleep(10.0)

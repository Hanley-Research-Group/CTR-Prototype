### HOW TO RUN

## 1. Set OHM and AMP values

# Setting OHM value
1. Hook up the leads of the part to a known, preferably high-watt-tolerant resistor. 3W or above works well. 
2. Power the board with a power supply that is set to 12v and at a limited current. I set my limit to 0.5A.
3. Grab a multimeter and set it to voltage read mode.
4. You will need to activate the system, which will send the max current through the resistor. WHILE it is active, probe either side of the resistor to get the voltage drop. To activate, run the command CAP 25000 (which will run current through the resistor for 25 seconds).
5. Look at the output in the serial monitor. It will tell you the raw voltage value the ADC read for "raw ohms in volts".
6. Find the ohm cal value by inputting these values into the following function: 
OHM_CAL = RAW_OHMS_IN_VOLTS/(12-MULTIMETER_VALUE)
7. Put the value OHM_CAL into the system by typing OHM [OHM_CAL] in the serial monitor (see commands.md).

# Setting AMP value
1. Hook up the leads of the part to a known, preferably high-watt-tolerant resistor. 3W or above works well. 
2. Power the board with a power supply that is set to 12v and at a limited current. I set my limit to 0.5A.
3. Grab a multimeter and set it to current-read mode.
4. You will need to take the power lead, run it through the multimeter, and then out to the part to read the current running through it. Set it up this way, then run CAP 25000 (see commands.md) and read what the multimeter says and mark it down.
5. Look at the output in the serial monitor. It will tell you the raw voltage value the ADC read for "raw amps in volts".
6. Find the amp cal value by inputting these values into the following function: 
AMP_CAL = RAW_AMPS_IN_VOLTS/MULTIMETER_VALUE
7. Put the value AMP_CAL into the system by typing AMP [AMP_CAL] in the serial monitor (see commands.md).

# Verifying Accuracy
1.  Hook up the leads of the part to a known, preferably high-watt-tolerant resistor. 3W or above works well. 
2. Power the board with a power supply that is set to 12v and at a limited current. I set my limit to 0.5A.
3. Run the command CAP 25000
4. See that the finished calculated resistance value matches the value of your resistor. If it does not, some of the math in previous steps was incorrect.

## 2. Set ROOM and ROHM values

# Setting Room Value
1. Find the most accurate reading for the current temperature of your environent.
2. Input it (IN CELCIUS!) to the system by using the ROOM command (see commands.md)

# Setting ROHM value
1. Run the ROHM command and wait for it to finish (see commands.md)

## 3. Clamp Tubing into Mold
1. Carefully slot in the nitinol tubing into the mold, ensuring that there is at least a centimeter of tube left on either side.
2. Because of the high spring force present in the tube, you may have to clamp it into the mold.

## 4. Hook Up Leads

Note: The side of the board with TWO sets of screw terminals facing out will be referred to as the "front" of the board, while the side of the board with one set of screw terminals facing out will be referred to as the "back".
# OUT leads
On the front side of the board, On the OUTER screw terminals (meaning the leftmost one and the rightmost one), connect leads with high-watt rated clamps and clamp them to the outside of the nitinol tubing. These leads are the OUT leads that will carry current through the tube. Clamp them to the outer edges of the nitinol tube. Ensure that the nitinol is not sagging out of the mold when you attatch them.
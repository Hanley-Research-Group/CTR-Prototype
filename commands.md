### COMMANDS
## Send these commands over serial to activate functions in the microcontroller.

# CAP [int]
Runs electricity through the subject for [int] milliseconds, then prints the average values of the raw voltage in the ADS and the calculated voltage after applying the calibration factors. Useful for testing if the system is working and gathering data.
# OHM [float]
Sets voltage-drop calibration value to [float].
# AMP [float]
Sets current-flow calibration value to [float].
# ROOM [float]
Sets current room temperature to [float] degrees CELCIUS.
# ROHM
Sets the resistance of the part at room temperature. This is critical for determining accurate temperature of part as resistance changes. voltage-drop and current-flow calibration values need to be accurate along with room temperature to calculate properly.
# RUN
Heats part to desired temperature, pulses for a preset amount of time, and maintains heat for a preset amount of time before stopping.
# PRNT
Print current set values. All need to be set properly for RUN command to function correctly.
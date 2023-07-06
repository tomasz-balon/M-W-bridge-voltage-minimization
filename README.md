# Project 4
Title: Maxwell-Wien bridge voltage minimization on RaspBerryPI, with the use of 8 PWMs
and results (voltage medium-straightened - 4 channels) read by REPL interface.

## DECISIONS:
- 8 PWMs
- 4 voltage measurements channels
- algorithm has to read current PWM settings to act accordingly

### Protocol:
- PWM1: aXXXX\n
- PWM2: bXXXX\n
- PWM3: cXXXX\n
- PWM4: dXXXX\n
- PWM5: eXXXX\n
- PWM6: fXXXX\n
- PWM7: gXXXX\n
- PWM8: hXXXX\n

where:
- a - 'shortcut' for PWM number
- XXXX - number to set, e.g. for PWM1 - a1000\n
- \n - newline/end byte


SIMULATION:
- Python script to simulate Maxwell-Wien bridge
- Python script to read file/buffer containing precise data describing voltages/PWMs/whatever

Reference: http://zmpsw.traffic.eu.org/index.cgi/r2020/proj_4/


### Workflow:
- Assign tickets on JIRA
- Every change needs to be committed as new branch with name proj4_X,
  where X stands for JIRA ticked ID, e.g. proj4_ZMPSW-7, DO NOT push to master
- Do not force push (if there's an error, there is a reason for that)
- Write comments (they can be both in code or in ticket) and description - it will be easier to understand each other
- After finishing the ticket, move it to "Review" state instead of "Done" and reassign it to me
- In case of any questions/issues, feel free to ask me, we will think of solution


### Project structure
- requirements.txt - file with all required libraries and their versions
- src/config.py - file containing all constants (preferably stored in 
- src/reader.py (name can be changed to more appropriate) - file to read data from buffer/file, includes algorithm to find voltage minimum
- src/bridge_simulator.py - script which simulates bridge behavior
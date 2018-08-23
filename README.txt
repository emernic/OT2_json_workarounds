This small repository contains two scripts for converting OpenTrons OT2 JSON protocols into OT2 Python protocols. These should only be used to enable testing of programs that write OT2 JSON protocols before the JSON protocol format is officially released (and can be accepted by the app directly).

json_to_py.py simply takes one argument (a JSON protocol file) and prints the equivalent Python protocol.

universal_template.py is a Python protocol for the OT2 robot that requires a json protocol to be pasted in at the top under the variable name jp={"a giant": "json protocol"}. It then executes the corresponding commands when it is run on the robot.

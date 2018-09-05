"""
This is a workaround for the fact that the new OT2 JSON schema is not officially out yet (8/23/2018)
It effectively converts protocols made using the schema as described here: https://github.com/Opentrons/opentrons/blob/391dcebe52411c432bb6f680d8aa5952a11fe90f/shared-data/protocol-json-schema/protocol-schema.json
into a Python protocol that can be run in the OT2 app.

This version also adds the ability to read from custom container definitions in the JSON protocols (not part of official schema).

To use:
	1.) Write your JSON protocol following the schema linked above.
	2.) Paste that JSON protocol into a file prepended with "jp=". In other words, create a file with one variable hard-coded
		at the top of it which contains your json protocol.
	3.) Paste the contents of this script into the same file. This script expects a variable named jp that contains the 
		json protocol.
	4.) Save your newly created file and drag it into the OT2 app.
"""


# jp={
#   "protocol-schema":"1.0.0",
#   "metadata":{
#     "protocol-name":"Example Protocol",
#     "author":"Ian",
#     "description":"An example of how JSON protocols will look. Does a multi-dispense then delays 1.5sec before dropping tip.",
#     "created":1519916981999,
#     "last-modified":1519917009476,
#     "category":"basic pipetting",
#     "subcategory":"sample prep",
#     "tags":[
#       "simple",
#       "example"
#     ]
#   },
#   "robot":{
#     "model":"OT-2 Standard"
#   },
#   "pipettes":{
#     "pipette1Id":{
#       "mount":"right",
#       "model":"p300_single_v1"
#     }
#   },
#   "labware-definitions": [
#     {
#       ......a labware definition......
#     }
#   ],
#   "labware":{
#     "tiprack1Id":{
#       "slot":"7",
#       "model":"tiprack-200ul",
#       "display-name":"Tip rack"
#     },
#     "custom-1.5-rack":{
#       "slot":"10",
#       "model":"trough-12row",
#       "display-name":"Source (Buffer)"
#     },
#     "destPlateId":{
#       "slot":"11",
#       "model":"96-flat",
#       "display-name":"Destination Plate"
#     },
#     "trashId":{
#       "slot":"12",
#       "model":"fixed-trash",
#       "display-name":"Trash"
#     }
#   },
#   "procedure":[
#     {
#       "annotation":{
#         "name":"Distribute 1",
#         "description":"Distribute source well to destination wells"
#       },
#       "subprocedure":[
#         {
#           "command":"pick-up-tip",
#           "params":{
#             "pipette":"pipette1Id",
#             "labware":"tiprack1Id",
#             "well":"A1"
#           }
#         },
#         {
#           "command":"aspirate",
#           "params":{
#             "pipette":"pipette1Id",
#             "volume":200,
#             "labware":"sourcePlateId",
#             "well":"A1"
#           }
#         },
#         {
#           "command":"touch-tip",
#           "params":{
#             "pipette":"pipette1Id",
#             "labware":"sourcePlateId",
#             "well":"A1"
#           }
#         },
#         {
#           "command":"dispense",
#           "params":{
#             "pipette":"pipette1Id",
#             "volume":50,
#             "labware":"destPlateId",
#             "well":"B1"
#           }
#         },
#         {
#           "command":"dispense",
#           "params":{
#             "pipette":"pipette1Id",
#             "volume":50,
#             "labware":"destPlateId",
#             "well":"B2"
#           }
#         },
#         {
#           "command":"dispense",
#           "params":{
#             "pipette":"pipette1Id",
#             "volume":50,
#             "labware":"destPlateId",
#             "well":"B3"
#           }
#         },
#         {
#           "command":"blowout",
#           "params":{
#             "pipette":"pipette1Id",
#             "labware":"trashId",
#             "well":"A1",
#             "position": {
#               "anchor": "top",
#               "offset": {
#                 "z": 2
#               }
#             }
#           }
#         }
#       ]
#     },
#     {
#       "annotation":{
#         "name":"Delay then drop tip",
#         "description":""
#       },
#       "subprocedure":[
#         {
#           "command":"delay",
#           "params":{
#             "wait":1.5,
#             "message":"hello robot operator, this is an example of the delay command"
#           }
#         },
#         {
#           "command":"drop-tip",
#           "params":{
#             "pipette":"pipette1Id",
#             "labware":"trashId",
#             "well":"A1"
#           }
#         }
#       ]
#     }
#   ]
# }

ROBOT_MODELS = ["OT-2 Standard"]

PIPETTE_MODELS = {
	"p10_single_v1": "P10_Single",
	"p10_multi_v1": "P10_Multi",
	"p50_single_v1": "P50_Single",
	"p50_multi_v1": "P50_Multi",
	"p300_single_v1": "P300_Single",
	"p300_multi_v1": "P300_Multi",
	"p1000_single_v1": "P1000_Single",
	"p1000_multi_v1": "P1000_Multi"
}


ASP_DISP_CMDS = {
	"aspirate": "aspirate",
	"dispense": "dispense",
	"air-gap": "air_gap"
}

TIP_CMDS = {
	"pick-up-tip": "pick_up_tip",
	"drop-tip": "drop_tip",
	"touch-tip": "touch_tip",
	"blowout": "blow_out"
}

DELAY_CMDS = {
	"delay": "delay"
}

TEMP_CMDS = {
	"set-temp": "set_temperature",
	"wait-temp": "wait_for_temp"
}

import json
from opentrons import instruments, labware, robot, modules
# from opentrons.data_storage import labware_definitions as ldef

#TODO: validate against schema first
#TODO: validate schema version

if jp['robot']['model'] not in ROBOT_MODELS:
	raise ValueError('Unsupported robot model: {0}. Accepted models: {1}'.formnat(jp['robot']['model'], ROBOT_MODELS))

# # TODO: this is not a good thing to do as this function is not a standard API endpoint.
# if jp['labware-definitions']:
# 	for labware_definition in jp['labware-definitions']:
# 		ldef.save_user_definition(json.dumps(labware_definition))

pipette_dict = {}
for name, pipette in jp['pipettes'].items():
	if pipette['model'] in PIPETTE_MODELS.keys():
		method_name = PIPETTE_MODELS[pipette['model']]
		method = getattr(instruments, method_name)
		pipette_dict[name] = method(mount=pipette['mount'])
	else:
		raise ValueError("Unsupported pipette model: {0}. Accepted models: {1}".formnat(pipette['model'], PIPETTE_MODELS.keys()))

#TODO: custom labware

#TODO: share should be False, but this throws errors because of trash so it's set for true for now.

labware_dict = {}
for name, item in jp['labware'].items():
	if "display-name" in item.keys():
		labware_dict[name] = labware.load(item['model'], item['slot'], item['display-name'], share=True)
	else:
		labware_dict[name] = labware.load(item['model'], item['slot'], share=True)

modules_dict = {}
for name, item in jp['modules'].items():
	modules_dict[name] = modules.load(item['model'], item['slot'])

# Merge all commands into a giant list and strip annotations
all_commands = []
for subprocedure in jp['procedure']:
	all_commands += subprocedure['subprocedure']

for command in all_commands:
	method_name = command['command']

	if method_name in ASP_DISP_CMDS.keys():
		method = getattr(pipette_dict[command['params']['pipette']], ASP_DISP_CMDS[method_name])
		wells_method = getattr(labware_dict[command['params']['labware']], 'wells')
		well = wells_method(command['params']['well'])
		
		#TODO: Support for offsets other than z... Not in OpenTrons Python api yet.
		if "position" in command['params'].keys():
			position_method = getattr(well, command['params']['position']['anchor'])
			well = position_method(command['params']['position']['offset']['z'])
		
		method(command['params']['volume'], well)

	elif method_name in TIP_CMDS:
		method = getattr(pipette_dict[command['params']['pipette']], TIP_CMDS[method_name])
		wells_method = getattr(labware_dict[command['params']['labware']], 'wells')
		well = wells_method(command['params']['well'])
		
		#TODO: Support for offsets other than z... Not in OpenTrons Python api yet.
		if "position" in command['params'].keys():
			position_method = getattr(well, command['params']['position']['anchor'])
			wells = position_method(command['params']['position']['offset']['z'])
		
		method(well)

	elif method_name in DELAY_CMDS:
		# Checks for BOOLEAN True (which means wait forever), not just that x exists.
		if command['params']['wait'] is True:
			robot.pause()
		else:
			# For whatever reason, the delay command is a method for Pipette in the Python API... so we will just pick a pipette.
			method = getattr(next(iter(pipette_dict.values())), DELAY_CMDS[method_name])
			method(seconds=command['params']['wait'])

	elif method_name in TEMP_CMDS:
		method = getattr(modules_dict[command['params']['module']], TEMP_CMDS[method_name])
		if method_name == 'wait-temp':
			method()
		elif method_name == 'set-temp':
			method(command['params']['temp'])
		else:
			raise ValueError("Only wait for temp and set temp supported for temp deck.")

	else:
		raise ValueError("Unkown command: {0}. Known commands: {1}".format(method_name, ASP_DISP_CMDS+TIP_CMDS+DELAY_CMDS))
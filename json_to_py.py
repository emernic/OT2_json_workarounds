import argparse
import json

parser = argparse.ArgumentParser(
	description="""
	This is a workaround for the fact that the new OT2 JSON schema is not officially out yet (8/23/2018)
	It converts protocols made using the schema as described here: https://github.com/Opentrons/opentrons/blob/391dcebe52411c432bb6f680d8aa5952a11fe90f/shared-data/protocol-json-schema/protocol-schema.json
	into a Python protocol that can be run in the OT2 app.
	To use:
		1.) Write your JSON protocol following the schema linked above.
		2.) Open up the command line in the folder containing this script.
		3.) Type "python json_to_py.py my_json_protocol.json > my_json_protocol.py" 
			(without quotes. obviously replace "my_json_protocol" with your own filename).

	Warning: Don't use this for protocols generate from sources you don't trust.
	""")
parser.add_argument('json_protocol', help='The json OT2 protocol file you wish to convert into Python.')
args = parser.parse_args()

with open(args.json_protocol) as json_protocol:
	jp = json.loads(json_protocol.read())

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

#TODO: validate against schema first
#TODO: validate schema version

if jp['robot']['model'] not in ROBOT_MODELS:
	raise ValueError('Unsupported robot model: {0}. Accepted models: {1}'.formnat(jp['robot']['model'], ROBOT_MODELS))

print("from opentrons import robot, labware, instruments\n")

print("pipette_dict = {}")
for name, pipette in jp['pipettes'].items():
	if pipette['model'] in PIPETTE_MODELS.keys():
		print("pipette_dict[\"{0}\"] = instruments.{1}(mount=\"{2}\")\n".format(name, PIPETTE_MODELS[pipette['model']], pipette['mount']))
	else:
		raise ValueError("Unsupported pipette model: {0}. Accepted models: {1}".formnat(pipette['model'], PIPETTE_MODELS.keys()))

#TODO: custom labware

#TODO: share should be False, but this throws errors because of trash so it's set for true for now.

print("labware_dict = {}")
for name, item in jp['labware'].items():
	if "display-name" in item.keys():
		print("labware_dict[\"{0}\"] = labware.load(\"{1}\", \"{2}\", \"{3}\", share=True)\n".format(name, item['model'], item['slot'], item['display-name']))
	else:
		print("labware_dict[\"{0}\"] = labware.load(\"{1}\", \"{2}\", share=True)\n".format(name, item['model'], item['slot']))

# Merge all commands into a giant list and strip annotations
all_commands = []
for subprocedure in jp['procedure']:
	all_commands += subprocedure['subprocedure']

for command in all_commands:
	method_name = command['command']

	if method_name in ASP_DISP_CMDS.keys():
		well = "labware_dict[\"{0}\"].wells(\"{1}\")".format(command['params']['labware'], command['params']['well'])

		if "position" in command['params'].keys():
			#TODO: Support for offsets other than z... Not in OpenTrons Python api yet.
			print("pipette_dict[\"{0}\"].{1}({2}, {3}.{4}({5}))\n".format(command['params']['pipette'], ASP_DISP_CMDS[method_name], command['params']['volume'], well, command['params']['position']['anchor'], command['params']['position']['offset']['z']))
		else:
			print("pipette_dict[\"{0}\"].{1}({2}, {3})\n".format(command['params']['pipette'], ASP_DISP_CMDS[method_name], command['params']['volume'], well))

	elif method_name in TIP_CMDS:
		well = "labware_dict[\"{0}\"].wells(\"{1}\")".format(command['params']['labware'], command['params']['well'])

		if "position" in command['params'].keys():
			#TODO: Support for offsets other than z... Not in OpenTrons Python api yet.
			print("pipette_dict[\"{0}\"].{1}({2}.{3}({4}))\n".format(command['params']['pipette'], TIP_CMDS[method_name], well, command['params']['position']['anchor'], command['params']['position']['offset']['z']))
		else:
			print("pipette_dict[\"{0}\"].{1}({2})\n".format(command['params']['pipette'], TIP_CMDS[method_name], well))

	elif method_name in DELAY_CMDS:
		# Checks for BOOLEAN True (which means wait forever), not just that x exists.
		if command['params']['wait'] is True:
			print("robot.pause()\n")
		else:
			# For whatever reason, the delay command is a method for Pipette in the Python API... so we will just pick a pipette.
			print("next(iter(pipette_dict.values())).{0}(seconds={1})\n".format(DELAY_CMDS[method_name], command['params']['wait']))

	else:
		raise ValueError("Unkown command: {0}. Known commands: {1}".format(method_name, ASP_DISP_CMDS+TIP_CMDS+DELAY_CMDS))
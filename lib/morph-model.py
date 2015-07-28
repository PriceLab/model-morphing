# This is the script that initiates the model morphing function. Interfacing to be addressed soon. TODO: Fix this description as you determine what this file will actioally do

#import necesary services
from biokbase.workspace.client import Workspace 
from biokbase.workspace.client import ServerError 
from biokbase.GenomeComparison.Client import GenomeComparison
from biokbase.fbaModelServices.Client import fbaModelServices
from biokbase.userandjobstate.client import UserAndJobState
# TODO remove these imports
# from biokbase.workspace.ScriptHelpers import user_workspace

import random
import sys
import argparse
import time
desc1 = '''
NAME
	 mm-morphmodel - 'Morph' a model an existing model to fit a related genome

SYNOPSIS
'''
desc2 = '''
DESCRIPTION
	Takes a Model/Genome for a 'source' organism and 'morphs' it to the 'target' organism. It keeps reactions from the 'source' model for which there is at least one matching gene feature, and attempts to remove those in the source model that do not have BLAST hits in the second genome. It also adds reactions annotated within the target genome that are unique to the target organism. The model is never broken in the process, such that the Biomass reaction and any other specified reaction [insert how you flag this option] must always carry flux. If a reaction can't be removed without breaking the model, it is flagged again and a few options are available for handling these reactions [insert said options] 
'''
	#TODO: Fill in EXAMPLES section with actual model/genomek
desc3 = '''
EXAMPLES
      Generate 'morphed' model for : 
      > mm-morph-model kb|m.1.model kb|g.0.genome 
AUTHORS
	Brendan King, Vangelis Simeonidis, Matt Richards
'''

# =================================================================================================
# 						Functions
# 
# functions used in the algorithm script TODO: make these private
# =================================================================================================

# label reactions in each model
def label_reactions():
	model_rxn_ids = set()
	for rxn in model['reactions']:
		model_rxn_ids.add(rxn['reaction'])
	for mdlrxn in recon['reactions']:
		if mdlrxn['reaction'] in model_rxn_ids:
			for ftr in mdlrxn['features']:
				if ftr in model_reactions[mdlrxn]['features']:
					print ftr
# Parses Command Line arguments and TODO: assigns all values to ids for ease of use
def parse_arguments():
	#TODO: replace sys.argv with appropriate replacement from bash script interface
	#FIXME: make it so arguments can be passed as names, then find a way to convert interior to IDs
	parser = argparse.ArgumentParser(formatter_class = argparse.RawDescriptionHelpFormatter, prog='mm-morph-model', epilog=desc3)	
	parser.add_argument('model', type=int, help='ID of the Model object', action='store', default=None)
	parser.add_argument('genome', type=int,  help='ID of the Genome object', action='store', default=None)
	parser.add_argument('protcomp', type=int,  help='ID of the Proteome Comparison object', action='store', default=None)
	parser.add_argument('--genomews', type=int, help='Workspace of the Genome object', action='store', default=None, dest='genomews')
	parser.add_argument('--modelws', type=int, help='Workspace of the Model object', action='store', default=None, dest='modelws')
	parser.add_argument('--protcompws', type=int, help='Workspace of the Proteome Comparison object', action='store', default=None, dest='protcompws')
		#TODO: ADD OTHER OPTION ARGUMENTS
	usage = parser.format_usage()
	parser.description = desc1 + '	' + usage + desc2
	parser.usage = argparse.SUPPRESS
	input_args = parser.parse_args()
	
	#Prepare the argument dictionary
	args = dict()
	args['genome'] = input_args.genome
	args['model'] = input_args.model
	args['protcomp'] = input_args.protcomp
	if input_args.genomews is None:
	#FIXME: fix this functionality
	# 	args['genomews'] = user_workspace()
		args['genomews'] = 8730
	else:
		args['genomews'] = input_args.genomews
	if input_args.modelws is None:
	#	args['modelws'] = user_workspace()
		args['modelws'] = 8730
	else:
		args['modelws'] = input_args.modelws
	if input_args.protcompws is None:
	#	args['protcompws'] = user_workspace()
		args['protcompws'] = 8730
	else:
		args['protcompws'] = input_args.protcompws
	return args

#Initiate Clients Objects for Function
def init_clients():
	clients = dict()
	clients['ws'] = Workspace()
		# Get FBA Model Services URL parameter
	with open (".kbase_fbaModelServicesURL", "r") as myfile:
		url = myfile.read().replace('\n','')
	clients['fba'] = fbaModelServices(url)
		# Get Genome Comparison URL parameter
	with open (".kbase_genomecomparisonURL", "r") as myfile:
		url = myfile.read().replace('\n','')
	clients['gencomp'] = GenomeComparison(url)
	clients['ujs'] = UserAndJobState()
	return clients

# initiate MMws workspace and clone in all needed objects
def init_workspace():
	ws_conflict = True
	global ws_name
	global ws_id
	ws_name = 'MMws'
	while (ws_conflict):
		create_ws_params = {'workspace' : ws_name, 'globalread' : 'r', 'description' : "A workspace for storing the FBA's and meta data of the algorithm"}
		# Try to create a workspace, catch an error if the name is already in use
		try:
			new_ws = ws_client.create_workspace(create_ws_params)
			# new_ws is type workspace_info, a tuple where 0, 1 are id, name
			ws_id = new_ws[0]
			ws_name = new_ws[1]
			ws_conflict = False
		except ServerError:
			 ws_name += str(random.randint(1,9))

#Prepare Proteome Comparison: Sets the args['protcomp'] reference to the protcomp dictionary AND sets the model field if no prot comp exists (saves comp time)
def blast_proteomes():
	global model
	if args['protcomp'] is None:
		# Set up parameters
		blast_proteomes_params = dict()
		blast_proteomes_params['genome1ws'] = args['genomews']
		blast_proteomes_params['genome1id'] = args['genome'] #genome 1 = the input genome
		get_models_params = {'models' : [args['model']], 'workspaces' : [args['modelws']]}
		model = fba_client.get_models(get_models_params)[0]
		[genome2ws, genome2id] = model['genome_ref'].split('/')[0:2] # genome_ref's take the form: "ws_id/obj_id/(some number that didnt seem important)"
		blast_proteomes_params['genome2ws'] =  genome2ws
		blast_proteomes_params['genome2id'] =  genome2id
		blast_proteomes_params['output_ws'] =  ws_id
		blast_proteomes_params['output_id'] =  '42' #FIXME: THIS WILL BREAK IF THERE IS AN OBJ 42 ALREADY IN WS
		jobid = gencomp_client.blast_proteomes(blast_proteomes_params)
		while ujs_client.get_job_status({'job' : jobid})[1] != 'completed' and ujs_client.get_job_status({'job' : jobid})[1] != 'error':
			time.sleep(20)
		if (ujs_client.get_job_status({'job' : jobid}) == 'error'):
			raise Exception
		else:
			protcomp = ws_client.get_objects([{'wsid' : ws_id , 'objid' : '42'}])
	else:
		protcomp_ref = args['protcomp']
		protcomp = ws_client.get_objects([{'wsid' : args['protcompws'], 'objid' : protcomp_ref}])[0] #get objects returns a list, [0] is the first object
	return protcomp['data']

# Get the reactions for the comparison 'recon' model in Genome B
def build_models():
	global recon
	global model
	if model is None:
		get_models_params = {'models' : [args['model']], 'workspaces' : [args['modelws']]}
		model = fba_client.get_models(get_models_params)[0]
	recon_params = {'genome' : args['genome'], 'genome_workspace' : args['genomews'], 'workspace' : ws_id}
	recon_id = fba_client.genome_to_fbamodel(recon_params)[0]
	get_models_params = {'models' : [recon_id], 'workspaces' : [ws_id]}
	recon = fba_client.get_models(get_models_params)[0]

# Finishing/Cleanup  Steps 
def finish():
	ws_client.delete_workspace({'id' : ws_id})

# =================================================================================================
# 						Script
#
# the scripted algorithm steps in order
# =================================================================================================
# init variables
model = None
recon = None
#parse command args
args = parse_arguments()

#initiate clients
clients = init_clients()
fba_client = clients['fba']
ws_client = clients['ws']
gencomp_client = clients['gencomp']
ujs_client = clients['ujs']
#initiate Model Morphing workspace
init_workspace() # creates global vars ws_name and ws_id

#Blast Proteomes
args['protcomp'] = blast_proteomes()
build_models()
label_reactions()
finish()
# Clean up/Finish

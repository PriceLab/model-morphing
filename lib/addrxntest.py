from biokbase.workspace.client import Workspace
from biokbase.workspace.client import ServerError
from biokbase.GenomeComparison.Client import GenomeComparison
from biokbase.fbaModelServices.Client import fbaModelServices
from biokbase.userandjobstate.client import UserAndJobState

import copy
import random
import sys
import argparse
import time
from operator import itemgetter

# Get FBA Model Services URL parameter
with open (".kbase_fbaModelServicesURL", "r") as myfile:
    url = myfile.read().replace('\n','')
fba_client = fbaModelServices(url)
rxns = [('rxn01316', 'c0','<',)]
params = {'model' : '9', 'model_workspace' : '9145', 'output_id' : 'testmodel', 'workspace' : '9145', 'reactions' : rxns}
output = fba_client.add_reactions(params)
fba_client.runfba({'model' : '9', 'model_workspace' : '9145', 'workspace' : '9145', 'fba' : 'testFBAaddReaction'})
ws_client = Workspace()
model = ws_client.get_objects([{'objid' : '9' , 'wsid' : '9145'}])[0]['data']
print model.keys()
for i in model['modelreactions']:
    for key in i.keys():
        print str(key) + ': ' + str(i[key])
rxns = ['rxn00670']
params = {'model' : '9', 'model_workspace' : '9145', 'output_id' : 'testmodel', 'workspace' : '9145', 'reactions' : rxns}
output = fba_client.remove_reactions(params)
print '\n'
for key in output:
    print str(key)
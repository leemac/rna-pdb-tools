#!/usr/bin/python

"""rmsd_calc_rmsd_to_target
--------------------------------------------------------------------------------
Usage: rmsd_calc_to_target.py [<options>] <pdb files (test_data/*)>

Options:
  -h, --help            show this help message and exit
  -t TARGET_FN, --target_fn=TARGET_FN
                        pdb file
  --target_selection=TARGET_SELECTION
                        selection, e.g. A:10-16+20, caution: it works like in
                        Python, 16 it's not included
  --target_ignore_selection=TARGET_IGNORE_SELECTION
                        A/10/O2'
  --model_selection=MODEL_SELECTION
                        selection, e.g. A:10-16+20, caution: it works like in
                        Python, 16 it's not included
  --model_ignore_selection=MODEL_IGNORE_SELECTION
                        A/10/O2'
  -o RMSDS_FN, --rmsds_fn=RMSDS_FN
                        ouput, matrix

.. caution:: this version if BioPython free == should be super fast! """

from rna_pdb_tools.utils.rmsd_calc.lib.rmsd.calculate_rmsd import *
import sys
from rna_pdb_tools.pdb_parser_lib import select_pdb_fragment
from rna_pdb_tools.utils.extra_functions.select_fragment import select_pdb_fragment_pymol_style
import optparse
import sys
import math
import glob
import re
import os

def get_rna_models_from_dir(files):
    """
    :param models: a list of filenames 

    Example of the list::

       ['test_data/rp17/2_restr1_Michal1.pdb_clean.pdb', 'test_data/rp17/2a_nonrestr2_Michal1.pdb_clean.pdb', 
       'test_data/rp17/3_nonrestr1_Michal1.pdb_clean.pdb', 'test_data/rp17/5_restr1_Michal3.pdb_clean.pdb']"""

    models = []
    #if not os.path.exists(directory):
    #    raise Exception('Dir does not exist! ', directory)
    #files = glob.glob(directory + "/*.pdb")
    files_sorted = sort_nicely(files)
    for f in files_sorted:
        models.append(f)
    return models

def sort_nicely( l ):
   """ Sort the given list in the way that humans expect.

   http://blog.codinghorror.com/sorting-for-humans-natural-sort-order/
   """
   convert = lambda text: int(text) if text.isdigit() else text
   alphanum_key = lambda key: [ convert(c) for c in re.split('([0-9]+)', key) ]
   l.sort( key=alphanum_key )
   return l

def calc_rmsd(a,b, selection_model, target_ignore_selection, selection_target, model_ignore_selection):
    """
    :params: a = filename of structure a
    :params: b = filename of structure b

    :return: rmsd, number of atoms
    """
    atomsP, P = get_coordinates(a, selection_model, target_ignore_selection, 'pdb', True)
    atomsQ, Q = get_coordinates(b, selection_target, model_ignore_selection, 'pdb', True)
    if atomsQ != atomsP:
        sys.exit('Error: # of atoms is not equal target:' + str(atomsP) + ' vs model:' + str(atomsQ))
    # Calculate 'dumb' RMSD
    normal_rmsd = rmsd(P, Q)

    # Create the centroid of P and Q which is the geometric center of a
    # N-dimensional region and translate P and Q onto that center.
    # http://en.wikipedia.org/wiki/Centroid
    Pc = centroid(P)
    Qc = centroid(Q)
    P -= Pc
    Q -= Qc

    if False:
        V = rotate(P, Q)
        V += Qc
        write_coordinates(atomsP, V)
        quit()

    return kabsch_rmsd(P, Q), atomsP

# main
if __name__ == '__main__':
    print 'rmsd_calc_rmsd_to_target'
    print '-' * 80
    
    optparser=optparse.OptionParser(usage="%prog [<options>] <pdb files (test_data/*)>")

    optparser.add_option('-t',"--target_fn", type="string",
                         dest="target_fn",
                         default='',
                         help="pdb file")

    optparser.add_option('',"--target_selection", type="string",
                         dest="target_selection",
                         default='',
                         help="selection, e.g. A:10-16+20, caution: it works like in Python, 16 it's not included")

    optparser.add_option('',"--target_ignore_selection", type="string",
                         dest="target_ignore_selection",
                         default='',
                         help="A/10/O2\'")
    
    optparser.add_option('',"--model_selection", type="string",
                         dest="model_selection",
                         default='',
                         help="selection, e.g. A:10-16+20, caution: it works like in Python, 16 it's not included")

    optparser.add_option('',"--model_ignore_selection", type="string",
                         dest="model_ignore_selection",
                         default='',
                         help="A/10/O2\'")
    
    optparser.add_option('-o',"--rmsds_fn", type="string",
                         dest="rmsds_fn",
                         default='rmsds.csv',
                         help="ouput, matrix")
    
    (opts, args)=optparser.parse_args()

    if len(sys.argv) == 1:
        print optparser.format_help() #prints help if no arguments
        sys.exit(1)

    input_files = args[:] # opts.input_dir
    rmsds_fn = opts.rmsds_fn
    target_fn = opts.target_fn

    target_selection = select_pdb_fragment(opts.target_selection)
    model_selection = select_pdb_fragment(opts.model_selection)
    print '  target_selection: ', opts.target_selection
    print '  model_selection:  ', opts.model_selection

    if opts.target_ignore_selection:
        target_ignore_selection = select_pdb_fragment_pymol_style(opts.target_ignore_selection)
    else:
        target_ignore_selection = None
        
    if opts.model_ignore_selection:
        model_ignore_selection = select_pdb_fragment_pymol_style(opts.model_ignore_selection)
    else:
        model_ignore_selection = None

    print '  target_ignore_selection: ', opts.target_ignore_selection
    print '  model_ignore_selection:  ', opts.model_ignore_selection

    models = get_rna_models_from_dir(input_files)        

    print '# of models:', len(models)

    f = open(rmsds_fn, 'w')
    #t = 'target:' + os.path.basename(target_fn) + ' , rmsd_all\n'
    t = 'fn,rmsd_all\n'

    c = 1
    for r1 in models:
        rmsd_curr, atoms = calc_rmsd(r1, target_fn, target_selection, target_ignore_selection, model_selection, model_ignore_selection)
        t += os.path.basename(r1) + ',' + str(round(rmsd_curr,3)) + ' '
        c += 1
        t += '\n'
            
    f.write(t)
    f.close()

    print t.strip() # matrix

    print '# of atoms used:', atoms
    if opts.rmsds_fn:
        print 'csv was created! ', rmsds_fn
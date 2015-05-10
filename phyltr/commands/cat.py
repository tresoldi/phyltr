"""Usage:
    phyltr cat [<options>] [<files>]

Extract phylogenetic trees from the specified files and print them as a treestream.  The trees may contain trees formatted as a phyltr treestream or a NEXUS file.

OPTIONS:

    -b, --burnin
        Percentage of trees from each file to discard as "burnin".  Default is 0.
        
    -s, --subsample
        Frequency at which to subsample trees, i.e. "-s 10" will include
        only every 10th tree in the treestream.  Default is 1.
        
    files
        A whitespace-separated list of filenames to read treestreams from.
        Use a filename of "-" to read from stdin.  If no filenames are
        specified, the treestream will be read from stdin.
"""

import fileinput
import sys

import ete2

import phyltr.utils.phyoptparse as optparse

def run():

    # Parse options
    parser = optparse.OptionParser(__doc__)
    parser.add_option('-b', '--burnin', action="store", dest="burnin", type="int", default=0)
    parser.add_option('-s', '--subsample', action="store", dest="subsample", type="int", default=1)
    options, files = parser.parse_args()
    if not files:
        files = ["-"]

    # Read files
    for filename in files:
        if filename == "-":
            fp = sys.stdin
        else:
            fp = open(filename, "r")

        tree_strings = []
        firstline = True
        for line in fp:
            # Skip blank lines
            if not line:
                continue
            
            # Detect Nexus file format by checking first line
            if firstline:
                if line.strip() == "#NEXUS":
                    isNexus = True
                    inTranslate = False
                    nexus_trans = {}
                else:
                    isNexus = False
                firstline = False

            # Detect beginning of Nexus translate block
            if isNexus and "translate" in line.lower():
                inTranslate = True
                continue

            # Handle Nexus translate block
            if isNexus and inTranslate:
                # Detect ending of translate block...
                if line.strip() == ";":
                    inTranslate = False
                # ...or handle a line of translate block
                else:
                    if line.strip().endswith(";"):
                        line = line[:-1]
                        inTranslate = False
                    index, name = line.strip().split()
                    if name.endswith(","):
                        name = name[:-1]
                    nexus_trans[index] = name

            # Attempt to parse the first whitespace-separated chunk on the line
            # which starts with an opening bracket.  Fail silently.
            chunks = line.split()
            for chunk in chunks:
                if chunk.startswith("("):
                    if chunk.count("(") == chunk.count(")"):
                        # Smells like a tree!
                        tree_strings.append(chunk)
                        break

        burnin = int(round((options.burnin/100.0)*len(tree_strings)))
        tree_strings = tree_strings[burnin::options.subsample]

        for tree_string in tree_strings:
           try:
               t = ete2.Tree(tree_string)
           except ete2.parser.newick.NewickError:
               continue
           if isNexus and nexus_trans:
               for node in t.traverse():
                   if node.name != "NoName" and node.name in nexus_trans:
                       node.name = nexus_trans[node.name]
           print t.write()

    # Done
    return 0

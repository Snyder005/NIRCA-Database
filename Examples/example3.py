#!/usr/bin/env python

"""
In this example the fuzzy string matching functionality of the NIRCAdb
package is demonstrated as well as additional SQLAlchemy ORM functions.

This script takes a team name as an input and is run using:

    python example3.py 'runner name'

Note: If the runner name is multiple words, quotation marks must be used

This example demonstrates the second method of looking up runners or teams
in the database.  Using the search.py module, we search the database using a 
a name, and return the best 5 matches.  The results are printed out along with 
the metric for fuzzy string comparison (100 being the best match, 0 being the
worst).  Finally we print the race results in the database for the best match.

"""

import argparse
import NIRCAdb as ndb
from NIRCAdb.search import runner_search

################################################################################
##
## Example 3: Runner Search and Results printing
##
################################################################################

def main(runner_name):

    with ndb.db_session('sqlite:///test.db') as f:

        ## Search the database for runners and return 5 search results.
        ## The results are a list of tuples (runner, ratio).
        search_results = runner_search(runner_name, limit=5, session=f)

        ## Print the results of the search as well as the ratio (0-100) used
        ## to calculate how close the matches are.
        print 'Search Results:\n'
        for search_result in search_results:
            runner = search_result[0]
            ratio = search_result[1]
            print "{0}, {1}".format(runner.name, ratio)

        ## For the best result, print the races
        best_match = search_results[0][0]
        print "\nBest Match: {0}".format(best_match.name)

        ## Print the results
        for result in best_match.results:
            print str(result)
            return

if __name__ == '__main__':

    ## Initialize argument parser
    parser = argparse.ArgumentParser()
    parser.add_argument('name', help='runner name to search')

    ## Pass arguments to the main function
    args = parser.parse_args()
    runner_name = args.name
    
    main(runner_name)


            

        

    

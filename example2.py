"""
In this example the SQLAlchemy ORM capabilities are shown in conjunction
with the NIRCA database to query the database for a team and print some of 
the attributes of the runners on the team.

This script takes an optional team name as an input and is run using:

    python example2.py 'team name'

Note: If the team name is multiple words, quotation marks must be used

As in the first example, we use our context manager to safely interface with 
the database.  This time we query the database using the 'names' filter and 
return the result.  The runners on the team are sorted by their speed ratings.
Finally each runner's name, gender and speed rating are printed.

As before, if no results are found, the program will raise an error.  A list 
of teams can be obtained using .

"""

import argparse
import NIRCAdb as ndb
from sqlalchemy import exc

################################################################################
##
## Example 2: Print Runners from Queried Team
##
################################################################################

def main(team_name):

    with ndb.db_session('sqlite:///test.db') as f:
    
        try:
            ## Query the database for the specific team using the name filter.
            ## It is important to know that the query always returns a list.
            team = ndb.Team.from_db(f, names=team_name)[0]
            print 'Team: {0}\n'.format(team.name)

            ## Sort runners using sort method
            team.sort_runners(key='rating')
            
            ## Print runners and their ratings from the first team
            for runner in team.runners:
                print ('Runners: {0} ({1})\n' +
                       'Speed Rating: {2}').format(runner.name, runner.gender,
                                                  runner.rating)

            return True

        ## Query found nothing, display name.
        except ndb.errors.QueryError:
            print "No team found with name '{0}'.".format(team_name)
            return False

        ## Some other error occurred, display the traceback
        except exc.SQLAlchemyError as e:
            print e
            return False

if __name__ == '__main__':

    ## Initialize argument parser
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--team', help='team name to query',
                        default='Stanford University')

    ## Pass arguments to the main function
    args = parser.parse_args()
    team_name = args.team
    
    main(team_name)

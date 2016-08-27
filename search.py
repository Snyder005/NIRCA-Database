"""Fuzzy string search module for NIRCAdb Package.

This contains the code that controls fuzzy string search of the runner 
database.  In contrast to simple Query functions, these functions attempt to 
match runners in the database to string queries.

"""

################################################################################
##
## Modules and Packages
##
################################################################################

import jellyfish as jf

import NIRCAdb as Ndb
from NIRCAdb import Team, Runner
from ndb_errors import SearchError

################################################################################
##
## Fuzzy String Matching Functions
##
################################################################################

def team_search(session, name_search, threshold=0.8, **kwargs):

    ## Query database for list of teams
    team_list = Team.from_db(session)
    
    ## Look for matches for the team
    results = []
    for team in team_list:
        cost = jf.jaro_distance(unicode(name_search), unicode(team.name))

        ## Check if perfect match, else append
        if cost == 1.0:
            return team
        elif cost > thershold:
            results.append((team, cost))

    ## Return closest match
    if len(results) > 1:
        results.sort(key=lambda x: x[1], reverse=True)
        return results[0][0]
    else:
        raise SearchError('No match found for {0}'.format(name_search))

def runner_search(session, name_search, team_name=None, threshold=0.8, **kwargs):

    ## Filter by team, if known
    if team_name is not None:
        runner_list = Runner.from_db(session, team_list = [team_name])
    else:
        runner_list = Runner.from_db(session)

    ## Look for matches for the runner
    results = []
    for runner in runner_list:
        cost = jf.jaro_distance(unicode(name_search), unicode(runner.name))

        ## Check if perfect match, else append
        if cost == 1.0:
            return runner
        elif cost > threshold:
            results.append((runner, cost))

    ## Return closest match
    if len(results) > 1:
        results.sort(key=lambda x: x[1], reverse=True)
        return results[0][0]
    else:
        raise SearchError('No match found for {0}'.format(name_search))

################################################################################
##
## Debug Code
##
################################################################################

def main():

    pass

if __name__ == '__main__':
    main()

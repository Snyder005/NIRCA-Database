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

from fuzzywuzzy import fuzz, process

from database import Team, Runner

################################################################################
##
## Fuzzy String Matching Functions
##
################################################################################

def team_search(name_search, limit=3, **kwargs):
    """Search database for a team by team name.

    Args:
        session (Session): Database session object.
        name_search (str): Team name to search for.
        threshold (int, optional): Levenshtein ratio cutoff.  Defaults to 
            80.

    Returns:
        Team object from database that matches the name.

    Raises:
        SearchError: If no match above 'threshold' is found.
    """

    ## Query database or use provided team list
    session = None
    team_list = None
    if "team_list" in kwargs:
        team_list = kwargs['team_list']
    elif "session" in kwargs:
        session = kwargs['session']
        team_list = Team.from_db(session)
    else:
        raise TypeError('Must provided either session=' +
                        'or team_list= parameters')
    
    ## Look for matches for the team
    choices = [team.name for team in team_list]
    matches = process.extract(name_search, choices, limit=limit)

    ## Get corresponding Team object for the results
    search_results = []
    for match in matches:
        for team in team_list:
            if team.name == match[0]:
                search_results.append((team, match[1]))

    ## Sort results
    search_results.sort(key=lambda x: x[1], reverse=True)
    return search_results

def runner_search(name_search, limit=5, **kwargs):
    """Search database for a team by team name.

    Args:
        session (Session): Database session object.
        name_search (str): Runner name to search for.
        team_name (str, optional): Team name for team filter in query.
            Defaults to None.
        thershold (int, optional): Levenshtein ratio cutoff.  Defaults to
            70.

    Returns:
        Runner object from database that matches the name.

    Raises:
        SearchError: If no match above 'threshold' is found.
    """

    ## Query database or use provided team list
    session = None
    runner_list = None
    if "runner_list" in kwargs:
        runner_list = kwargs['runner_list']
    elif "session" in kwargs:
        session = kwargs['session']
        runner_list = Runner.from_db(session)
    else:
        raise TypeError('Must provided either session=' +
                        'or runner_list= parameters')
    
    ## Look for matches for the team
    choices = [runner.name for runner in runner_list]
    matches = process.extract(name_search, choices, limit=limit)

    ## Get corresponding Team object for the results
    search_results = []
    for match in matches:
        for runner in runner_list:
            if runner.name == match[0]:
                search_results.append((runner, match[1]))

    ## Sort results
    search_results.sort(key=lambda x: x[1], reverse=True)
    return search_results

################################################################################
##
## Debug Code
##
###########################################################x#####################

def main():

    import NIRCAdb as Ndb

    with Ndb.db_session('sqlite:///test.db') as f:
        results = team_search('Stanford', session=f, limit=5)
        for result in results:
            print result[0].name, result[1]
        

if __name__ == '__main__':
    main()

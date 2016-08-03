"""NIRCAdb Package Version 7.0rc2 source code.

This contains the source code for what will be NIRCAdb Version 7.0.  It is
currently under construction.  Once completed this will serve as base python
package. Additionally a GUI will be created using the code developed in this
package. Version 6.1 is a stand alone GUI and is functional, though it can be 
unstable and is out-of-date. 

Features:
    Version 6.1 has the following features:

    * Single Runner Querying: Query the database, using a GUI, by runner names. 

    * Multiple Runner Querying: Query the database, using a GUI, filtering by
          team names, runner status, and runner gender. GUI interface allows 
          sorting by runner name, team names, runner gender, runner Speed 
          Rating, and runner status.

    * Team Ranking: Rank multiple teams using the runners' Speed Ratings.

    * Race Simulation: Basic support for simulating races between teams and 
          displaying average results

    * Result Formatting: Format a list of results from a single race to be
          processed by hand.

    * Upload Processed Results: Upload processed results and update the
          database

New Features:  
    In addition to the above features, Version 7.0 will include the following,
    some of which will supercede features in Version 6.1.

    * Region Filter: NIRCA region will be added as a filter for multiple runner
          queries, and simulated races.

    * Roll-over Database: Add functionality to update database for the next 
          season, i.e., remove inactive runners and remove all results

    * Improved Result Formatting: Improvements to the runner/result matching to
          improve result formatting.

    * MCMC Result Processing: Processing of results automatically using MCMC
          techniques.

    * Integrated Results Uploading: Streamline and integrate result formatting,
          processing, and final upload.

Todo:

    * QOL changes for printing runners, results and teams

    * Build GUI for Query. (5.0)

    * Program and implement MCMC result processing. (3.0)
 
    * Fix result formatting, processing and uploading issues. (4.0)

    * Add Result Uploading features to GUI (6.0)

.. NIRCAdb 7.0rc2
   http://github.com/Snyder005/NIRCAdb

"""

__version__ = "7.0rc2"

################################################################################
##
## Modules and Packages
##
################################################################################

import sys
import datetime

import sqlalchemy as sql
import numpy as np

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref, sessionmaker, reconstructor
from scipy import stats
from contextlib import contextmanager

Base = declarative_base()
Session = sessionmaker()

@contextmanager
def db_session(database):
    """Create a session bound to the given database.

    Args:
        database (str): Database filepath.
    """
    
    try:
        engine = sql.create_engine(database, echo=False)
        Base.metadata.create_all(engine)
        Session.configure(bind=engine)
        session = Session()
        yield session
        session.commit()
    except:
        session.rollback()
        raise Exception # Placeholder
    finally:
        session.close()

################################################################################
##
## Database Objects
##
################################################################################

class Runner(Base):
    """Represents a runner contained in the database.

    Attributes:
        name (str): Name of runner.
        team_id (int): Team ID for team this runner is on.
        gender (str): Gender of runner.
        rating (float): Speed Rating for the runner.
        status (bool): True if runner is active, False if inactive.
        results (list): List of Result objects for the runner.
        average (float): Average of race results. Initialy 'None'.
        ratings_list (list): List of generated ratings. Initialy empty.
        races_simulated (bool): True if races simulated, else False.
    """

    __tablename__ = 'runners'

    ## Runner attributes stored in database
    id = sql.Column(sql.Integer, primary_key=True)
    name = sql.Column(sql.String, index=True)
    team_id = sql.Column(sql.Integer, sql.ForeignKey('teams.id'))
    gender = sql.Column(sql.String)
    rating = sql.Column(sql.Float)
    status = sql.Column(sql.Boolean)

    ## Create one-to-many relationship with Results table
    results = relationship("Result", backref=backref('runner'))

    @reconstructor
    def init_on_load(self):
        """Initialize instance attributes."""
        
        self._average = None
        self._ratings_list = []
        self._races_simulated = False

    @classmethod
    def from_db(cls, session, names = [], team_list=[], gender=None, status=None):        

        query = session.query(cls)

        ## If list of names, ignore other filters
        if not isinstance(names, list):
            names = [names]

        if len(names) > 0:
            if len(names) == 1:
                query = query.filter(cls.name == names[0])
            elif len(names) > 1:
                query = query.filter(cls.name.in_(names))
        
        else:
            ## Filter by gender
            if gender in ['Male', 'Female']:
                query = query.filter(cls.gender == gender)

            ## Filter by status
            if status is not None:
                query = query.filter(cls.status == status)

            ## Filter by team
            if not isinstance(team_list, list):
                team_list = [team_list]

            if len(team_list) == 1:
                query = query.join(Team).filter(Team.name == team_list[0])
            elif len(team_choice) > 1:
                query = query.join(Team).filter(Team.name.in_(team_list))

        ## Determine proper return value
        runners = query.all()
        if len(runners) == 1:
            return runners[0]
        else:
            return runners

    @property
    def average(self):
        return self._average

    @property
    def ratings_list(self):
        return self._ratings_list
        
    @property
    def races_simulated(self):
        return self._races_simulated

    def add_to_db(self, session):
        """Add runner to database.

        Args:
            session (Session): Database session object.
        """

        session.add(self)

    def add_result(self, session, result):
        """Add result to database and update runner Speed Rating.

        Args:
            session (Session): Database session object.
            result (Result): Result object to be added.
        """

        result.runner_id = self.id
        session.add(result)

        ## Update Speed Rating in database
        if runner.rating == None or runner.status == False:
            runner.status = True
            runner.rating = round(result.rating, 3)
        else:
            diff = abs(result.rating - runner.rating)
            if diff >= 40:
                new = max(result.rating, runner.rating)*0.9 + \
                      min(result.rating, runner.rating)*0.1
            elif 30 <= diff < 40:
                new = max(result.rating, runner.rating)*0.85 + \
                      min(result.rating, runner.rating)*0.15
            elif 20 < diff < 30:
                new = max(result.rating, runner.rating)*0.8 + \
                      min(result.rating, runner.rating)*0.75
            else:
                new = max(result.rating, runner.rating)*0.75 + \
                      min(result.rating, runner.rating)*0.25
            self.rating = round(new_rating, 3)

    def sim_races(self, num_races, mode='maxwell', **kwargs):
        """Simulate Speed Ratings based on a particular method.

        Args:
            num_races (int): Number of desired race simulations.
            mode (str): Method used to generate new Speed Ratings.
            **kwargs: Keyword arguments for 'mode'.

        Returns:
            List of generated ratings and their average as a tuple. 

        Raises:
            KeyError: If 'mode' is not valid.
        """

        ## Initialize by clearing previous data
        self._average = 0
        self._ratings_list = []

        ## Generate ratings using a reflected and translated maxwell
        if mode == 'maxwell':
            factor = kwargs.get('factor', 4)
            prob_mean = stats.maxwell.mean(scale=factor)
            new_ratings = self.rating + prob_mean - \
                          np.array(stats.maxwell.rvs(scale=factor,
                                                     size=num_races))

        ## Generate ratings by drawing from a Gaussian
        elif mode == 'norm':
            scale = kwargs.get('scale', 1)
            new_ratings = stats.norm.rvs(loc=self.rating, scale=scale,
                                         size=num_races)
        else:
            raise KeyError("Incorrect mode: '{0}'".format(mode))
            
        self._ratings_list = new_ratings
        self._average = np.mean(new_ratings)
        self._races_simulated = True

        return self.ratings_list, self.average

    def __str__(self):
        return "{0} \n".format(self.name)
        

class Result(Base):
    """Represents a race result by a particular runner, contained in 
    the database.

    Attributes:
        name (str): Name of race.
        date (Date): Date of race.
        distance (int): Length of race in meters.
        rating (int): Speed Rating for the result.
        time (str): Race result in HH:MM:SS.ms format.
        runner_id (int): Runner ID for runner who ran this result.
    """

    __tablename__ = 'results'

    ## Result attributes stored in database
    id = sql.Column(sql.Integer, primary_key=True)
    name = sql.Column(sql.String, index=True)
    date = sql.Column(sql.Date)
    distance = sql.Column(sql.Integer)
    rating = sql.Column(sql.Float)
    time = sql.Column(sql.String)
    runner_id = sql.Column(sql.Integer, sql.ForeignKey('runners.id'))

    def __str__(self):
        """Return a string representation of the race result.  

        The format is legacy from the earliest versions of the database;
        a command line program using a text file.  This representation can
        be used for output to Qt display widgets.

        Returns:
            Formatted string.
        """
        
        attributes = [self.name, str(self.date), self.distance, self.time,
                      "{:.2f}".format(self.rating)]

        return "{:<30} {:<10} {:<10} {:<10} {:>8} \n".format(*row)

class Team(Base):
    """Represents a NIRCA club team contained in the database.

    Attributes:
        name (str): Name of team.
        region (str): NIRCA region the team is in.
        runners (list): List of runners on the team.
        average (float): Average of team race results.
        result_list (list): List of generated team results as tuples
                            (int 'place', int 'score)
        races_simulated (bool): True if races simulated, else False.
    """

    __tablename__ = 'teams'

    ## Team attributes stored in database
    id = sql.Column(sql.Integer, primary_key=True)
    name = sql.Column(sql.String, index=True)
    region = sql.Column(sql.String)

    ## Create one-to-many relationship with Runners table
    runners = relationship("Runner", backref=backref('team'))

    @classmethod
    def from_db(cls, session, names = [], regions=[]):
        """Query database and return Teams depending on given filter.

        Args:
            session (Session): Database Session object.
            names (list): Team name(s) to filter by.
            regions (list): Region(s) to filter by.

        Raises:
            
        """

        ## Check that list objects are given
        if not isinstance(names, list):
            names = [names]           
        if not isinstance(regions, list):
            regions = [regions]

        query = session.query(cls)

        ## Filter by team name(s)
        if len(names) == 1:
            query = query.filter(cls.name == names[0])
        elif len(names) > 1:
            query = query.filter(cls.name.in_(names))

        ## Filter by region(s)
        if len(regions) == 1:
            query = query.filter(cls.region == regions[0])
        elif len(regions) > 1:
            query = query.filter(cls.region.in_(regions))

        ## Determine proper return value
        teams = query.all()
        if len(teams) == 1:
            return teams[0]
        else:
            return teams

    @reconstructor
    def init_on_load(self):
        """Initialize instance attributes."""
        
        self._average = None
        self._result_list = []
        self._races_simulated = False

    @property
    def average(self):
        return self._average

    @property
    def result_list(self):
        return self._result_list

    @property
    def races_simulated(self):
        return self._races_simulated

    def sort_by_rating(self):
        """Sort runners on the team by Speed Rating from highest to lowest."""
        
        self.runners.sort(key=lambda x:float(x.rating), reverse=True)

    def size(self):
        """Determine number of runners on the team.

        Returns:
            Length of 'runners' array.
        """

        return len(self.runners)

    def sim_races(self, num_races, mode='maxwell', **kwargs):
        """Simulate Speed Ratings for each runner on the team.

        Args:
            num_races (int): Number of desired race simulations.
            mode (str): Method used to generate new Speed Ratings.
            **kwargs: Keyword arguments for 'mode'.
        """

        self._average = 0
        self._result_list = []

        for runner in self.runners:
            runner.sim_races(num_races, mode, **kwargs)          

################################################################################
##
## Simulator Object
##
################################################################################

class Sim:
    """Represents a race simulation consisting of runners from a team(s).

    Attributes:
        teams (list): List of teams in the race.
        runners (list): List of all runners in the race. May be empty.
    """

    def __init__(self, teams):

        ## Format teams to include only top 7 and ignore ineligible teams
        if not isinstance(teams, list):
            teams = [teams]
        for team in teams:
            team.sort_by_rating()
        self.teams = [Team(id=t.id, name=t.name, runners=t.runners[0:7]) \
                      for t in teams if t.size() >=5]

        self.runners = []
        self._is_simulated = False

    @property
    def is_simulated(self):
        return self._is_simulated

    def run(self, num_races, mode='maxwell', **kwargs):
        """Simulate a number of races between teams.

        Args:
            num_races (int): Number of desired race simulations.
            mode (str): Method used to generate new Speed Ratings.
            **kwargs: Keyword arguments for 'mode'.
        """
            

        ## Generates ratings for every runner on each team
        for team in self.teams:
            team.sim_races(num_races, mode, **kwargs)

        self.runners = [runner for team in self.teams for runner in \
                        team.runners]

        ## For each race calculate each teams score
        for i in range(num_races):
            self.runners.sort(key=lambda x: x.ratings_list[i], reverse=True)
            for team in self.teams:
                places = [1 + self.runners.index(runner) for runner \
                          in self.runners if team.name == runner.team.name]
                team.result_list.append([0, sum(places[:5])])
                
            self.teams.sort(key=lambda x: x.result_list[i][1])
            
            for team in self.teams:
                team.result_list[i][0] = self.teams.index(team) + 1

        ## Calculate the average score for each team
        for team in self.teams:
            team._average = round(np.mean([result[1] for result in \
                                          team.result_list]))
            
        self.teams.sort(key=lambda x: x.average)
        self._is_simulated = True

        ## Legacy code to print to Qt display widget
        #print_string = ''
        #for i, team in enumerate(self.teams):
        #    print_string += '\n' + str(i+1).rjust(6) + ' ' + \
        #    team.show_result()
        #print_string += '\n'
        #for i, runner in enumerate(self.runners):
        #    print_string += '\n' + str(i+1).rjust(6) + '  ' + \
        #    runner.show_result()
        #
        #return print_string

################################################################################
##
## Functions to incorporate into a new Database/Query Class
##
################################################################################

def get_team_match(session, lookup_name, threshold=0.8):  ## Move to matching module

    team_list = get_teams(session)

    matches = []
    for team in team_list:
        cost = jf.jaro_distance(unicode(lookup_name), unicode(team.name))

        if cost < threshold:
            matches.append((team, cost))

    if len(matches) > 1:
        matches.sort(key=lambda x: x[1], reverse=True)
    elif len(matches) == 0:
        raise Exception

    return matches[0][0]
    

################################################################################
##
## Race Object
##
################################################################################

class Race:
    """Represents a race.

    This Python object will eventually perform all the processing to add
    race results to the database.

    Attributes:
        name (str): Name of the race.
        date (Date): Date of race.
        distance (int): Race distance in meters.
        filename (str): Name of file with race results
    """

    def __init__(self, name, date, distance):

        self.name = name
        self.date = date
        self.distance = distance

    def generate_ratings(self):
        """Generate ratings using a MCMC technique."""
        pass
        
    def export_to_database(self):
        """Export ratings to a SQL database."""
        pass

################################################################################
##
## Main Function
##
################################################################################
        
def main():
    pass
    

if __name__ == '__main__':

    main()

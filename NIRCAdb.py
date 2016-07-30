"""NIRCAdb Package Version 7.0rc1 source code.

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

    * Add and debug query functions. These will most likely go into a new class 
      to streamline integration with the GUI display. (2.0)

    * Build GUI for Query. (5.0)

    * Program and implement MCMC result processing. (3.0)
 
    * Fix result formatting, processing and uploading issues. (4.0)

    * Add Result Uploading features to GUI (6.0)

.. NIRCAdb 7.0rc1
   http://github.com/Snyder005/NIRCAdb

"""

__version__ = "7.0rc1"

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

Base = declarative_base()
Session = sessionmaker()

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

    @property
    def average(self):
        return self._average

    @property
    def ratings_list(self):
        return self._ratings_list
        
    @property
    def races_simulated(self):
        return self._races_simulated

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
## Race Simulator Object
##
################################################################################

class Race:
    """Represents a hypothetical race consisting of runners from a team(s).

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
## Main Function
##
################################################################################
        
def main():

    ## Initialize sqlite database
    engine = sql.create_engine('sqlite:///test.db', echo=False)
    Base.metadata.create_all(engine)
    Session.configure(bind=engine)
    

    ## Qt Stuff will go here

    ## Debugging here
    session = Session()
    team1 = session.query(Team).filter_by(name = 'University of Illinois').first()
    team2 = session.query(Team).filter_by(name = 'Cal Poly').first()
    team3 = session.query(Team).filter_by(name = 'Stanford University').first()

    race = Race([team1, team2, team3])
    race.run(1)
    for team in race.teams:
        print team.name, team.result_list
    for runner in race.runners:
        print runner.name, runner.team.name, runner.ratings_list
    

if __name__ == '__main__':

    main()

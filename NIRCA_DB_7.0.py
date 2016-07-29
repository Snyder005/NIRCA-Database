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
from sqlalchemy.orm import relationship, backref, sessionmaker
from scipy.stats import maxwell

# No longer import:
#    Column
#    Integer
#    String
#    Float
#    Boolean
#    Date
#    ForeignKey
#    create_engine

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
        rating (str): Speed Rating for the runner.
        status (bool): Indicates if runner is active (True) or inactive (False)
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
    results = relationship("Result", backref=backref('runners'))

    def sim_races(self, num_races, mode='maxwell', **kwargs):
        """Simulate Speed Ratings based on a particular method."""

        self.average = 0
        self.result_list = []

        ## Generate ratings using a reflected and translated maxwell
        if mode == 'maxwell':
            factor = kwargs.pop('factor', 4)
            prob_mean = maxwell.mean(scale=factor)
            new_ratings = self.rating + prob_mean - \
                          np.array(maxwell.rvs(scale=factor, size=num_races))

        self.result_list = new_ratings
        self.average = np.mean(new_ratings)

        return result_list, average
        

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
    """

    __tablename__ = 'teams'

    ## Team attributes stored in database
    id = sql.Column(sql.Integer, primary_key=True)
    name = sql.Column(sql.String, index=True)
    region = sql.Column(sql.String)

    ## Create one-to-many relationship with Runners table
    runners = relationship("Runner", backref=backref('teams'))

    def sort_by_rating(self):
        """Sort runners on the team by Speed Rating from highest to lowest."""
        
        self.runners.sort(key=lambda x:float(x.rating), reverse=True)

    def size(self):
        """Return number of runners on the team."""

        return len(team.runners)

    def sim_races(self, num_races, mode='maxwell', **kwargs):
        """Simulate Speed Ratings for each runner on the team."""

        self.average = 0
        self.result_list = []

        for runner in self.runners:
            runner.sim_races(num_races, mode, **kwargs)

################################################################################
##
## Race Simulator Object
##
################################################################################

class Race:
    """Represents a hypothetical race consisting of runners from a team(s)."""

    def __init__(self, teams):

        ## Format teams to include only top 7 and ignore ineligible teams
        for team in teams:
            team.sort_by_rating()
        self.team_results = [(Team(id=t.id, name=t.name,
                                   runners=t.runners[0:7]), 0, []) \
                             for t in teams if t.size() >=5]

    def run(self, num_races):

        ## Generates ratings for every runner on each team
        for team in self.teams:
            team.sim_races(num_races)

        self.runners = [runner for team in self.teams for runner in team.runners]

        ## For each race calculate each teams score
        for i in range(num_races):
            self.runners.sort(key=lambda x: x.result_list[i], reverse=True)
            for team in self.teams:
                places = [1 + self.runners.index(runner) for runner \
                          in self.runners if team.name == runner.team.name]
                team.result_list.append([0, sum(places[:5])])
                
            self.teams.sort(key=lambda x: x.result_list[i][1])
            
            for team in self.teams:
                team.result_list[0][i] = self.teams.index(team) + 1

        ## Calculate the average score for each team
        for team in self.teams:
            team.average = round(np.mean([result[1] for result in team.result_list]))
            
        self.teams.sort(key=lambda x: x.average)

        ## Legacy code to print to Qt display widget
        #print_string = ''
        #for i, team in enumerate(self.teams):
        #    print_string += '\n' + str(i+1).rjust(6) + ' ' + team.show_result()
        #print_string += '\n'
        #for i, runner in enumerate(self.runners):
        #    print_string += '\n' + str(i+1).rjust(6) + '  ' + runner.show_result()
        #
        #return print_string

################################################################################
##
## Main Function
##
################################################################################
        
def main():

    ## Initialize sqlite database
    engine = sql.create_engine('sqlite:///NIRCA_test.db', echo=False)
    Base.metadata.create_all(engine)
    Session.configure(bind=engine)

    ## Qt Stuff will go here

if __name__ == '__main__':

    main()

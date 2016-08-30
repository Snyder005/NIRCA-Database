"""Database objects for use with the NIRCAdb Package.

This contains the database entry Objects Runner, Team and Results, that 
interface with the NIRCA database.  In addition a context manager is provided
to allow easy database session use.

"""

__version__ = "7.0rc2"

################################################################################
##
## Modules and Packages
##
################################################################################

import sqlalchemy as sql
import numpy as np
import datetime

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref, sessionmaker, reconstructor
from scipy import stats
from contextlib import contextmanager

from errors import QueryError

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
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()

################################################################################
##
## Runner Object
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

    def __str__(self):
        return "{0} \n".format(self.name)

    @reconstructor
    def init_on_load(self):
        """Initialize instance attributes."""
        
        self._average = None
        self._ratings_list = []
        self._races_simulated = False

    @classmethod
    def from_db(cls, session, names = [], team_list=[], gender=None, status=None):
        """Initialize Runner objects from database using a query.

        Args:
            session (Session): Database session object.
            names (list, optional): List of names (str) to filter by. Defaults 
                to empty list.
            team_list (list, optional): List of teams (str) to filter by. Defaults
                to empty list.
            gender (str, optional): Gender filter choice. Defaults to 'None'.
            status (bool, optional): Status filter choice. Defaults to 'None'.

        Returns:
            Either a list of Runner objects, or a single Runner object, depending
            on results of the query.
        """

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
            elif len(team_list) > 1:
                query = query.join(Team).filter(Team.name.in_(team_list))

        ## Check that query returned non-empty list
        runners = query.all()
        if len(runners) == 0:
            raise QueryError('No runners found.')
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
            mode (str, optional): Method used to generate new Speed Ratings.
                Defaults to 'maxwell'.
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

################################################################################
##
## Result Object
##
################################################################################

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

        return "{:<30} {:<10} {:<10} {:<10} {:>8} \n".format(*attributes)

################################################################################
##
## Team Object
##
################################################################################
    
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
            names (list, optional): Team name(s) (str)  to filter by. 
                Defaults to empty list.
            regions (list, optional ): Region(s) (str) to filter by. 
                Defaults to empty list.

        Returns:
            Either list of Team objects or single Team object, depending 
            on results of the query.            
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
        if len(teams) == 0:
            raise QueryError('No teams found.')
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

    def sort_runners(self, key):
        """Sort runners depending on specified key."""

        if key == 'rating':
            self.runners.sort(key=lambda x: float(x.rating), reverse=True)
        elif key == 'name':
            self.runners.sort(key=lambda x: x.name)
        else:
            raise KeyError("'{0}' is not a valid sorting key.".format(key))

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

    with db_session('sqlite:///test.db') as f:

        test = Team.from_db(f)
        print test[0].name

if __name__ == '__main__':

    main()

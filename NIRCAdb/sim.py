"""Simulation objects and processes for use with NIRCAdb Package.

This contains the objects that control the simulation processes.

"""

from database import Team, Runner

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

    def __init__(self, teams, gender='M'):

        if not isinstance(teams, list):
            teams = [teams]

        ## Find teams with at least five active runners
        self.teams = []
        self.runners = []

        for team in teams:
            active_runners = [runner for runner in team.runners \
                              if runner.status == True \
                              if runner.gender == gender]


            ## If more than 5, add team to the Sim list of teams
            if len(active_runners) >= 5:
                self.teams.append(team)
                active_runners.sort(key=lambda x: float(x.rating),
                                             reverse=True)
                scorers = active_runners[0:7]
                self.runners += scorers

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

    def predict(self):

        ## For each race calculate each teams score
        self.runners.sort(key=lambda x: x.rating, reverse=True)
        for team in self.teams:
            places = [1 + self.runners.index(runner) for runner \
                      in self.runners if team.name == runner.team.name]
            team.result_list.append([0, sum(places[:5])])
                
        self.teams.sort(key=lambda x: x.result_list[0][1])
            
        for team in self.teams:
            team.result_list[0][0] = self.teams.index(team) + 1

        for i, team in enumerate(self.teams):
            print "{0},  {1},  {2}".format(i+1, team.name, team.result_list[0])

        for i, runner in enumerate(self.runners):
            print "{0}, {1}, {2}, {3}".format(i+1, runner.name,
                                           runner.team.name,
                                           runner.rating)

        

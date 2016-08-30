"""Simulation objects and processes for use with NIRCAdb Package.

This contains the objects that control the simulation processes.

"""

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

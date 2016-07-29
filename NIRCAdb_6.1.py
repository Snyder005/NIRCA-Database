import sys
from PySide.QtGui import *
from PySide.QtCore import *

from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Float, Boolean, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref, sessionmaker

from scipy.stats import maxwell
import numpy as np
import datetime
import csv

import jellyfish as jf

Base = declarative_base()
Session = sessionmaker()

######################################################################################################
#
# Developer Notes
#
######################################################################################################

"""Last update 8/21/2014

8/21/2014, 2:00 PM -  Currently debugging simulation program.  Program runs without errors but copies race results to all teams.
This causes the averaging to malfunction and messes up the final scoring feature.

8/21/2014, 4:00 PM - Finished debugging the scoring and simulation program. Next update will separate the search and scoring function.
Search function will be built from a tab widget with tabs devoted to different ways of searching.

1. Search by Name (will feature link to results table) 
2. Search by Team, Gender, Status
3. Browse database (Tree structure) **This will be implemented last

If time remains, I will begin implementing a fuzzy string comparison for the Search by Name.

8/21/2014,  7:00 PM - Add fuzzy string matching to search function. Threshold and matching function can be adjusted.

8/27/2014,  8:30 PM - Need to debug Select page.  Currently the table does not reset when a search is done a second time.

8/28/2014,  7:45 PM - Debugged Select page so table resets and dynamically adds/removes rows.  Need to add code to resize columns to fit.

8/30/2014,  2:00 AM - Added the results wizard.  Currently unable to share constructed variables between pages.
                      Once that is set, the final page confirmation will be made, then results added.

9/10/2014,  5:00 PM - Implemented button to change matched teams in the Add Race wizard.  May have to revisit QDialog implementation.
                      Will have to do the same for matched runners.

                      Additionally: must modify QFileDialog in Add Race Wizard to restrict bad inputs

9/10/2014, 11:30 PM - QDialog implementation updated, and dialog to change match runners created

                      Additionally: must change date input in QWizard to QDateWidget with QCalendar popup, then this must be
                      converted to sqlalchemy's date/time format and implemented

9/12/2014, 8:00 PM - Added scroll bars to widget pages. Minor changes to Add/New Dialog.

                     MAJOR PROBLEM: Errors when adding results, from adding new runners to a current team. Perhaps must use append instead

To Do List:

1. Write additional printing functions for runner, team, and result, that are not
   reliant on the one-to-many relationships.

2. Write code to automatically generate ratings for each race, currently only matching is done

3. Create placeholder rating, for new runners with no past results and implement within step 4 code.
"""

######################################################################################################
#
# Table Object Definitions
#
######################################################################################################

class Runner(Base):
    __tablename__ = 'runners'

    # Runner attributes stored in SQL database
    id = Column(Integer, primary_key=True)
    name = Column(String, index=True)
    team_id = Column(Integer, ForeignKey('teams.id'))
    gender = Column(String)
    rating = Column(Float)
    status = Column(Boolean)

    # Join with Team table, via team name
    team = relationship("Team", backref=backref('runners', order_by=id))

    def start_for_race(self):
        # Non SQL attributes
        self.average = 0
        self.result_list = []

    def __repr__(self):
        return "<Runner(name='%s', id='%s')>" % (self.name, self.id)

    def show_runner(self):
        try:
            row = [self.name, self.gender, self.team.name, "{:.2f}".format(self.rating), self.status]
            return "{: <30} {:<2} {:<50} {:>8} {:>2}".format(*row)
        except:
            return "Can't print runner: Missing attributes"

    def show_result(self):
        try:
            row = [self.name, self.gender, self.team.name, "{:.2f}".format(self.average), self.status]
            return "{: <30} {:<2} {:<50} {:>8} {:>2}".format(*row)
        except:
            return "Can't print runner result: Missing attributes"

    def gen_race_rating(self, factor=4, num_races=1):

        # Generate an array of ratings via a function (to be improved on later)
        prob_mean = maxwell.mean(scale=factor)
        new_ratings = self.rating + prob_mean - np.array(maxwell.rvs(scale=factor, size=num_races))                              

        return new_ratings

class Result(Base):
    __tablename__ = 'results'

    id = Column(Integer, primary_key=True)
    name = Column(String, index=True)
    date = Column(Date)
    distance = Column(Integer)
    rating = Column(Float)
    time = Column(String)
    runner_id = Column(Integer, ForeignKey('runners.id'))

    runner = relationship("Runner", backref=backref('results', order_by=id))

    def __repr__(self):
        row = [self.name, str(self.date), self.distance, self.time, "{:.2f}".format(self.rating)]
        return "{:<30} {:<10} {:<10} {:<10} {:>8} \n".format(*row)

class Team(Base):
    __tablename__ = 'teams'

    # Team attributes stored in SQL database
    id = Column(Integer, primary_key=True)
    name = Column(String, index=True)

    def start_for_race(self):        
        self.average = 0
        self.result_list = []

    def __repr__(self):
        return "<Team(name='%s')>" % self.name

    def show_result(self):
        try:
            row = [self.name, int(self.average)]
            return "{: <50} {:>4}".format(*row)
        except:
            return "Error printing team results!"

    def sortRating(self):
        self.runners.sort(key=lambda x: float(x.rating), reverse=True)

class Race:

    def __init__(self, teams):

        # Format teams to include only top 7 and ignore ineligible teams
        for team in teams:
            team.sortRating()
        self.teams = [Team(id=team.id,
                           name=team.name,
                           runners=team.runners[0:7]) for team in teams if len(team.runners) >= 5]

        # Add runners from eligible teams to a separate array
        self.runners = [runner for team in self.teams for runner in team.runners]

    def startlist(self):

        # Sort by rating from highest to lowest
        self.runners.sort(key=lambda x:  float(x.rating), reverse=True)

        # Score each team and calculate the average
        for team in self.teams:
            team.start_for_race()
            places = [1 + self.runners.index(runner) for runner in self.runners if team.name == runner.team.name]
            team.average = sum(places[:5])

        # Sort and construct the return string to be printed/saved
        self.teams.sort(key=lambda x: x.average)

        print_string = ''
        for i, team in enumerate(self.teams):
            print_string += '\n' + str(i+1).rjust(6) + ' ' + team.show_result()
        print_string += '\n'
        for i, runner in enumerate(self.runners):
            print_string += '\n' + str(i+1).rjust(6) + '  ' + runner.show_runner()
        return print_string

    def run(self, num_races):

        for team in self.teams:
            team.start_for_race()

        # Simulate race by generating ratings for each runner
        for runner in self.runners:
            runner.start_for_race()
            runner.result_list = runner.gen_race_rating(4, num_races)
            runner.average = np.mean(runner.result_list)

        # For each race, calculate each teams score and set the results attribute
        for i in range(num_races):
            self.runners.sort(key=lambda x: x.result_list[i], reverse=True)
            for team in self.teams:
                places = [1 + self.runners.index(runner) for runner in self.runners if team.name == runner.team.name]
                team.result_list.append([0, sum(places[:5])])

            self.teams.sort(key=lambda x: x.result_list[i][1])
            for team in self.teams:
                team.result_list[i] = (self.teams.index(team) + 1, team.result_list[i][1])

        # Calculate the average score for each team
        for team in self.teams:
            team.average = round(np.mean([result[1] for result in team.result_list]))

        # Sort and construct the return string to be printed/saved
        self.teams.sort(key=lambda x: x.average)
       
        print_string = ''
        for i, team in enumerate(self.teams):
            print_string += '\n' + str(i+1).rjust(6) + ' ' + team.show_result()
        print_string += '\n'
        for i, runner in enumerate(self.runners):
            print_string += '\n' + str(i+1).rjust(6) + '  ' + runner.show_result()

        return print_string

######################################################################################################
#
# Format Results Wizard Widget
#
######################################################################################################

class formatWizard(QWizard):
    """This is the QWizard that will hold the pages of the wizard"""

    def __init__(self):
        super(formatWizard, self).__init__()

        # Add Wizard Pages to the QWizard
        self.addPage(setRacePage())
        self.addPage(setTeamMatches())
        self.addPage(setRunnerMatches())
        self.addPage(finalConfirmation())
        self.addPage(finalFormat())

        # Set geometry and show
        self.setWindowTitle("Race Wizard Test")
        self.resize(640, 480)
        self.show()

class setRacePage(QWizardPage):
    """This is the first page of the Wizard. It is used to accept user input for values such as
       race name, date, distance, gender, and the corresponding data file, in order to open and process
       the race data."""

    def __init__(self):
        super(setRacePage, self).__init__()

        # Create labels and buttons, with connected slots
        self.name_label = QLabel("Name: ")
        self.date_label = QLabel("Date: ")
        self.gender_label = QLabel("Gender: ")
        self.distance_label = QLabel("Race Distance: ")
        self.file_button = QPushButton("Get Filename")
        self.file_button.clicked.connect(self.getFile)

        # Create text boxes for entering values
        self.name_edit = QLineEdit()
        self.date_edit = QDateEdit(QDate.currentDate())
        self.date_edit.setDisplayFormat("yyyy-MM-dd")
        self.date_edit.setCalendarPopup(True)
        self.gender_combo = QComboBox()
        self.gender_combo.addItem("Choose Gender")
        self.gender_combo.addItem("Men")
        self.gender_combo.addItem("Women")
        self.distance_combo = QComboBox()
        self.distance_combo.addItem("Choose Race Distance (meters)")
        self.distance_combo.addItem("4000")
        self.distance_combo.addItem("5000")
        self.distance_combo.addItem("6000")
        self.distance_combo.addItem("8000")
        self.file_edit = QLineEdit()
        self.file_edit.setReadOnly(True)

        # Create the grid layout, add widgets and set as the layout
        grid = QGridLayout()
        grid.addWidget(self.name_label, 1, 0)
        grid.addWidget(self.date_label, 2, 0)
        grid.addWidget(self.gender_label, 3, 0)
        grid.addWidget(self.distance_label, 4, 0)
        grid.addWidget(self.name_edit, 1, 1)
        grid.addWidget(self.date_edit, 2, 1)
        grid.addWidget(self.gender_combo, 3, 1)
        grid.addWidget(self.distance_combo, 4, 1)
        grid.addWidget(self.file_button, 5, 0)
        grid.addWidget(self.file_edit, 5, 1)        
        self.setLayout(grid)

        # Register the fields to use values in other Wizard pages
        self.registerField("race_name*", self.name_edit)
        self.registerField("race_date", self.date_edit, "date", "dateChanged")
        self.registerField("race_gender*", self.gender_combo)
        self.registerField("race_distance*", self.distance_combo, "currentText", "currentIndexChanged")
        self.registerField("filename*", self.file_edit)

    def getFile(self):

        filename, filtr = QFileDialog.getOpenFileName(self,
                                                      "Select file",
                                                      "",
                                                      "Text Files (*.csv *.dat *.txt)",
                                                      "Text Files (*.csv *.dat *.txt)")

        if filename:
            self.file_edit.clear()
            self.file_edit.insert(filename)


class setTeamMatches(QWizardPage):
    """This is the second page of the Wizard. It processes the team data to find database matches and
       prompts the user to make any changes before confirmation."""

    def setTeamList(self, new_list):
        """Set QProperty team_list function"""

        # Set the list of matches
        self.team_match_list_val = new_list

        # Check if list has changed and emit signal
        if self.team_match_list_val != []:
            self.listChanged.emit()

    def updateTeamListItem(self, new_match, index):
        """Update QProperty team_list specific value function"""
        self.team_match_list_val[index] = new_match
        self.listChanged.emit()
        
    def readTeamList(self):
        """Read QProperty team_list function"""
        return self.team_match_list_val    
    
    def __init__(self):
        super(setTeamMatches, self).__init__()
        self.team_match_list_val = []

        # Initialize scroll and container widgets
        self.container = QWidget()
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(False)
        
        # Set labels
        self.name_label = QLabel("Names: ")
        self.match_label = QLabel("Matched Name: ")

        # Confirmation/Cancel buttons and options
        self.confirm_check= QCheckBox("Confirm")

        # Create the grid layout, add widgets and set as the layout
        self.grid = QGridLayout()
        self.grid.setSpacing(20)
        self.grid.addWidget(self.name_label, 1, 0)
        self.grid.addWidget(self.match_label, 1, 1)
        self.setLayout(self.grid)

        # Scroll Area Properties
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(False)

        # Register the fields to use values in other Wizard pages
        self.registerField("team_check*", self.confirm_check)
        self.registerField("team_match_list", self, "team_match_list")

    def initializePage(self):

        # Initialize all empty lists/sets
        race_team_names = set()
        team_dict = dict()
        team_matches = []
        
        self.match_displays = []

        # Get filename field, open and read teams from file
        filename = self.field("filename")
        fin = open(filename, "r")
        result_data = fin.readlines()
        for result in result_data:
            one_line = str.split(result, ',')
            race_team_names.add(one_line[1])
        race_team_names = list(race_team_names)

        # Query the database for list of teams
        session = Session()
        self.team_name_list = get_team_names(session)
        session.close()

        # Create matches for each team in the race   
        for race_team_name in race_team_names:
            matched_team_name = find_match(race_team_name, self.team_name_list)
            one_match = [race_team_name, matched_team_name]
            team_matches.append(one_match)

        # Initialize signalMapper
        signalMapper = QSignalMapper(self)
            
        # For each match create labels and display
        for i, match in enumerate(team_matches):

            # Create displays and buttons
            name_display = QLabel(match[0])
            match_display = QLineEdit(match[1])
            match_display.setReadOnly(True)
            new_team_button = QPushButton("Select New Team")

            # Connect button to signalMapper
            signalMapper.setMapping(new_team_button, i)
            new_team_button.clicked.connect(signalMapper.map)

            # Add match_display to list of displays
            self.match_displays.append(match_display)

            # Add to grid layout
            self.grid.addWidget(name_display, i+2, 0)
            self.grid.addWidget(match_display, i+2, 1)
            self.grid.addWidget(new_team_button, i+2, 2)

        # Connect signalMapper to change_add function
        signalMapper.mapped.connect(self.change_add)
            
        # Add Confirmation check box
        self.grid.addWidget(self.confirm_check, len(team_matches)+3, 0)

        # Set the final list of team matches
        self.setTeamList(team_matches)

        # Set up scroll area and assign as main layout
        self.container.setLayout(self.grid)
        self.scroll.setWidget(self.container)
        vLayout = QVBoxLayout(self)
        vLayout.addWidget(self.scroll)        
        self.setLayout(vLayout)

    def change_add(self, index):

        # Get new match name
        new_match, ok = ChangeTeamDialog.getMatch(self.team_match_list_val[index][0], self.team_name_list)

        if ok:
            # Update match list
            self.match_displays[index].setText(new_match)
            self.team_match_list_val[index][1] = new_match

    # Define the list of matches as a Q_Property
    team_match_list = Property(list, readTeamList, setTeamList)
    listChanged = Signal()   

class setRunnerMatches(QWizardPage):
    """This is the third page of the Wizard. It uses the confirmed matches to query the database in order to match runners
       for each result and prompts the user to confirm the matches"""

    def setRunnerList(self, new_list):

        # Set the list of matches
        self.runner_match_list_val = new_list

        # Check if list has changed and emit signal
        if self.runner_match_list_val != []:
            self.listChanged.emit()

    def readRunnerList(self):
        return self.runner_match_list_val
    
    def __init__(self):
        super(setRunnerMatches, self).__init__()
        self.runner_match_list_val = []

        # Initialize scroll and container widgets
        self.container = QWidget()
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(False)
        
        # Set labels
        self.name_label = QLabel("Names: ")
        self.match_label = QLabel("Matched Name: ")

        # Confirmation/Cancel buttons and options
        self.confirm_check= QCheckBox("Confirm")

        # Create the grid layout, add widgets and set as the layout
        self.grid = QGridLayout()
        self.grid.setSpacing(20)
        self.grid.addWidget(self.name_label, 1, 0)
        self.grid.addWidget(self.match_label, 1, 1)
        self.setLayout(self.grid)

        # Register the fields to use values in other Wizard pages
        self.registerField("runner_check*", self.confirm_check)
        self.registerField("runner_match_list", self, "runner_match_list")

    def initializePage(self):

        # Initialize all empty lists
        team_dict = dict()
        runner_matches = []

        self.match_displays = []

        # Get relevant fields from past pages
        race_gender_key = self.field("race_gender")
        gender_dict = {1 : 'M', 2 : 'W'}
        race_gender = gender_dict[race_gender_key]
        team_matches = self.field("team_match_list")

        # Construct dictionary of teams
        for match in team_matches:
            team_dict[match[0]] = match[1]

        # Add new teams
        session = Session()
        for team_name in team_matches:
            if not session.query(Team).filter_by(name=team_name[1]).first():
                new_team = Team(name=team_name[1])
                session.add(new_team)
                session.commit()
            
        # Query database for list of runners
        names = [team_name for team_name in list(team_dict.values())]
        runner_query = session.query(Runner.name, Team.name).filter_by(gender = race_gender).join(Team).filter(Team.name.in_(names))
        self.runner_name_list = runner_query.all()

        # Get filename field, open and read teams from file
        filename = self.field("filename")
        fin = open(filename, "r")
        result_data = fin.readlines()

        # Create matches for each runner in the race
        for result in result_data:
            one_line = str.split(result, ',')

            # Get result data from each line in the data
            race_team_name = team_dict[one_line[1]]
            race_time = one_line[2]

            # For each line, match the runner name with a runner in the database
            race_runner_name = one_line[0]
            search_list = [runner[0] for runner in self.runner_name_list if runner[1] == race_team_name]
            matched_runner_name = find_match(race_runner_name, search_list)

            #Assign each match and add to the list
            one_match = [matched_runner_name, race_runner_name, race_team_name, race_time]
            runner_matches.append(one_match)

        # Initialize signalMapper
        signalMapper = QSignalMapper(self)
    
        # For each match create labels and display
        for i, match in enumerate(runner_matches):
            
            name_display = QLabel(match[1])
            match_display = QLineEdit(match[0])
            match_display.setReadOnly(True)
            
            new_runner_button = QPushButton("Select New Runner")

            # Connect button to signalMapper
            signalMapper.setMapping(new_runner_button, i)
            new_runner_button.clicked.connect(signalMapper.map)

            # Add match_display to list of displays
            self.match_displays.append(match_display)

            self.grid.addWidget(name_display, i+2, 0)
            self.grid.addWidget(match_display, i+2, 1)
            self.grid.addWidget(new_runner_button, i+2, 2)

        # Connect signalMapper to change_add function
        signalMapper.mapped.connect(self.change_add)

        # Add confirmation checkbox
        self.grid.addWidget(self.confirm_check, len(runner_matches)+3, 0)

        # Set up scroll area and assign as main layout
        self.container.setLayout(self.grid)
        self.scroll.setWidget(self.container)
        vLayout = QVBoxLayout(self)
        vLayout.addWidget(self.scroll)        
        self.setLayout(vLayout)

        # Set the final list of runner matches
        session.close()
        self.setRunnerList(runner_matches)

    def change_add(self, index):

        # Get current match information
        team_name = self.runner_match_list_val[index][2]
        possible_matches = [runner[0] for runner in self.runner_name_list if runner[1] == team_name]

        # Get new match name
        new_match_name, ok = ChangeRunnerDialog.getMatch(self.runner_match_list_val[index][1], possible_matches)

        if ok:
            # Update match list
            self.match_displays[index].setText(new_match_name)
            self.runner_match_list_val[index][0] = new_match_name
            
    # Define the list of matches as a Q_Property
    runner_match_list = Property(list, readRunnerList, setRunnerList)
    listChanged = Signal()

class finalConfirmation(QWizardPage):
    """This is the fourth page of the Wizard. It displays the text that will be saved as a csv."""

    def setResultList(self, new_list):

        # Set the list of matches
        self.result_list_val = new_list

        # Check if list has changed and emit signal
        if self.result_list_val != []:
            self.listChanged.emit()

    def readResultList(self):
        return self.result_list_val
    
    def __init__(self):
        super(finalConfirmation, self).__init__()
        self.result_list_val = []

        # Set labels
        self.label = QLabel("All runners have been assigned.  New runners/teams have been added to the database")
        self.race_display = QTextEdit()
        self.race_display.setFixedWidth(900)
        self.race_display.setReadOnly(True)
        self.race_display.setStyleSheet("font: 10pt \"Courier\";")

        # Confirmation/Cancel buttons and options
        self.confirm_check= QCheckBox("Confirm")

        # Create the grid layout, add widgets and set as the layout
        self.grid = QGridLayout()
        self.grid.setSpacing(20)
        self.grid.addWidget(self.label, 1, 0)
        self.grid.addWidget(self.race_display, 3, 0, 5, 6)
        self.grid.addWidget(self.confirm_check, 8, 1)
        self.setLayout(self.grid)

        self.registerField("final_check*", self.confirm_check)
        self.registerField("result_list", self, "result_list")

    def initializePage(self):

        self.race_display.clear()
        
        # Initialize empty lists
        new_result_list = []

        # Get relevant fields
        race_name = self.field("race_name")
        race_date = self.field("race_date")
        race_gender_key = self.field("race_gender")
        gender_dict = {1 : 'M', 2 : 'W'}
        race_gender = gender_dict[race_gender_key]
        race_distance = self.field("race_distance")
        result_matches = self.field("runner_match_list")

        session = Session()

        file = QFile("/Users/adamsnyder/Documents/NIRCA_Database/Result_CSV_Files/%s-%s.csv" % (race_name, race_gender))
        file.open(QIODevice.WriteOnly | QIODevice.Text)

        race_info = str(race_name) + ',' + str(race_date.toString('dd/MM/yyyy')) + ',' + str(race_distance) + '\n'
        
        file.write(race_info)        

        for result_match in result_matches:

            runner = session.query(Runner).filter_by(name = result_match[0]).first()
            
            if not runner:
                new_runner = Runner(name = result_match[0],
                                    status = True,
                                    gender = race_gender)
                t = session.query(Team).filter(Team.name == result_match[2]).first()
                t.runners.append(new_runner)
                session.commit()

                runner = new_runner

            time_in_sec = sum(float(x) * 60 ** i for i,x in enumerate(reversed(result_match[3].split(":"))))
            
            new_str = str(runner.id)+ ',' + str(result_match[2]) + ',' + str(time_in_sec) + ',' + str(runner.rating) + '\n' 
            self.race_display.insertPlainText(new_str)

        print self.race_display.toPlainText()
        file.write(self.race_display.toPlainText())
        file.close

        session.close()
        
class finalFormat(QWizardPage):
    """This is the final page of the Wizard. It saves the matched runners as a csv file."""
    
    def __init__(self):
        super(finalFormat, self).__init__()

        # Set labels
        self.label = QLabel("The race has been formatted and saved.")

        # Create the grid layout, add widgets and set as the layout
        self.grid = QGridLayout()
        self.grid.setSpacing(20)
        self.grid.addWidget(self.label, 1, 0)
        self.setLayout(self.grid)

class ChangeTeamDialog(QDialog):

    def __init__(self, name_to_match, possible_matches):
        super(ChangeTeamDialog, self).__init__()

        self.possible_matches = possible_matches

        layout = QVBoxLayout(self)

        self.select_label = QLabel("Select Team")
        self.team_combo = QComboBox()
        self.team_combo.addItems(sorted(possible_matches))
        self.new_label = QLabel("Add Team: (%s)" % name_to_match)
        self.new_edit = QLineEdit()
        self.new_edit.setPlaceholderText("Enter new name")
        
        layout.addWidget(self.select_label)
        layout.addWidget(self.team_combo)
        layout.addWidget(self.new_label)
        layout.addWidget(self.new_edit)

        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
                                        Qt.Horizontal, self)

        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

        layout.addWidget(self.buttons)

    def NewMatch(self):
        new_match_name = self.team_combo.currentText()
        if not self.new_edit.isModified():
            new_match = [team for team in self.possible_matches if team == new_match_name]
            return new_match[0]
        else:
            new_match = self.new_edit.text()
            return new_match

    @staticmethod
    def getMatch(name_to_match, possible_matches):
        dialog = ChangeTeamDialog(name_to_match, possible_matches)
        result = dialog.exec_()
        match = dialog.NewMatch()
        return (match, result == QDialog.Accepted)

class ChangeRunnerDialog(QDialog):

    def __init__(self, name_to_match, possible_matches):
        super(ChangeRunnerDialog, self).__init__()

        self.possible_matches = possible_matches

        layout = QVBoxLayout(self)

        self.select_label = QLabel("Select Runner")
        self.team_combo = QComboBox()
        self.team_combo.addItems(sorted(possible_matches))
        self.new_label = QLabel("Add Runner: (%s)" % name_to_match)
        self.new_edit = QLineEdit()
        self.new_edit.setPlaceholderText("Enter new name")
        
        layout.addWidget(self.select_label)
        layout.addWidget(self.team_combo)
        layout.addWidget(self.new_label)
        layout.addWidget(self.new_edit)

        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
                                        Qt.Horizontal, self)

        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

        layout.addWidget(self.buttons)

    def NewMatch(self):
        new_match_name = self.team_combo.currentText()
        if not self.new_edit.isModified():
            return new_match_name
        else:
            new_match_name = self.new_edit.text()
            return new_match_name

    @staticmethod
    def getMatch(name_to_match, possible_matches):
        dialog = ChangeRunnerDialog(name_to_match, possible_matches)
        result = dialog.exec_()
        match = dialog.NewMatch()
        return (match, result == QDialog.Accepted)

######################################################################################################
#
# Add Result Wizard Widget
#
######################################################################################################

class addWizard(QWizard):
    """This is the QWizard that will hold the pages of the add wizard"""

    def __init__(self):
        super(addWizard, self).__init__()

        # Add Wizard Pages to the QWizard
        self.addPage(addFilePage())
        self.addPage(addConfirmation())
        self.addPage(finalCommit())

        # Set geometry and show
        self.setWindowTitle("Race Wizard Test")
        self.resize(640, 480)
        self.show()

class addFilePage(QWizardPage):

    def __init__(self):
        super(addFilePage, self).__init__()

        # Create labels and buttons, with connected slots
        self.main_label = QLabel("Enter filename for processed results data")
        self.file_button = QPushButton("Get Filename")
        self.file_button.clicked.connect(self.getFile)

        self.file_edit = QLineEdit()
        self.file_edit.setReadOnly(True)

        # Create the grid layout, add widgets and set as the layout
        grid = QGridLayout()
        grid.addWidget(self.main_label, 1, 0)
        grid.addWidget(self.file_button, 2, 0)
        grid.addWidget(self.file_edit, 2, 1)        
        self.setLayout(grid)

        # Register the fields to use values in other Wizard pages
        self.registerField("filename*", self.file_edit)

    def getFile(self):

        filename, filtr = QFileDialog.getOpenFileName(self,
                                                      "Select file",
                                                      "",
                                                      "Text Files (*.csv *.dat *.txt)",
                                                      "Text Files (*.csv *.dat *.txt)")

        if filename:
            self.file_edit.clear()
            self.file_edit.insert(filename)

class addConfirmation(QWizardPage):

    def setResultList(self, new_list):

        # Set the list of matches
        self.result_list_val = new_list

        # Check if list has changed and emit signal
        if self.result_list_val != []:
            self.listChanged.emit()

    def readResultList(self):
        return self.result_list_val
    
    def __init__(self):
        super(addConfirmation, self).__init__()

        self.result_list_val = []

        # Set labels
        self.label = QLabel("The following results will be added to the database.")
        self.race_display = QTextEdit()
        self.race_display.setFixedWidth(900)
        self.race_display.setReadOnly(True)
        self.race_display.setStyleSheet("font: 10pt \"Courier\";")

        # Confirmation/Cancel buttons and options
        self.confirm_check= QCheckBox("Confirm")

        # Create the grid layout, add widgets and set as the layout
        self.grid = QGridLayout()
        self.grid.setSpacing(20)
        self.grid.addWidget(self.label, 1, 0)
        self.grid.addWidget(self.race_display, 3, 0, 5, 6)
        self.grid.addWidget(self.confirm_check, 8, 1)
        self.setLayout(self.grid)

        self.registerField("final_check*", self.confirm_check)
        self.registerField("result_list", self, "result_list")

    def initializePage(self):

        filename = self.field("filename")        

        # Open file with results
        fin = open(filename, "r")

        results_data = []
        new_result_list = []
        lines = fin.readlines()

        # Split lines by comma
        for line in lines:
            results_data.append(str.split(line, ','))

        # Get race information from first line
        
        race_name = results_data[0][0]
        race_date = results_data[0][1]
        race_distance = results_data[0][2]

        # Construct the results from the runner matches
        for line in results_data[1:]:
            # fix rating by removing \n character
            new_result = Result(name = race_name,
                                date = datetime.date(int(race_date[6:]), int(race_date[3:5]), int(race_date[:2])),
                                distance = int(race_distance),
                                rating = float(line[3]),
                                time = "%s:%05.2f" % (int(float(line[2])/60), round(float(line[2]) % 60, 2))) 
            new_result_list.append([line[0], new_result])
            self.race_display.insertPlainText(str(new_result))

        self.setResultList(new_result_list)

    result_list = Property(list, readResultList, setResultList)
    listChanged = Signal()

class finalCommit(QWizardPage):
    """This is the final page of the Wizard. It saves the matched runners as a csv file."""
    
    def __init__(self):
        super(finalCommit, self).__init__()

        # Set labels
        self.label = QLabel("The results have been added to the database.")

        # Create the grid layout, add widgets and set as the layout
        self.grid = QGridLayout()
        self.grid.setSpacing(20)
        self.grid.addWidget(self.label, 1, 0)
        self.setLayout(self.grid)

    def initializePage(self):

        # Get relevant fields
        result_list = self.field("result_list")

        session = Session()
        # Construct the results from the runner matches
        for result in result_list:
            r = session.query(Runner).filter(Runner.id == result[0]).first()
            r.results.append(result[1])
            update_runner(r, result[1])
        session.commit()
        session.close()

######################################################################################################
#
# Race Simulation Widget
#
######################################################################################################

class raceSimulation(QWidget):
    """ This will display the menu to search for a single runner"""

    def __init__(self):
        super(raceSimulation, self).__init__()

        # Create the labels
        self.team_label = QLabel('Select Teams:')        
        self.gender_label = QLabel('Select Gender:')
        self.status_label = QLabel('Select Status:')

        # Create display to input gender
        self.gender_cbox = QComboBox()
        self.gender_dict = {'Men' : 'M', 'Women' : 'W'}
        self.gender_cbox.addItems(['Men', 'Women'])

        # Create display to input status
        self.status_cbox = QComboBox()
        self.status_dict = {'Active' : 1, 'Not Active' : 0, 'Both' : None}
        self.status_cbox.addItems(['Active', 'Both', 'Not Active']) # Change to active when season starts

        # Create display to input teams
        self.team_list = QListWidget()

        session = Session()
        team_name_list = [team.name for team in get_teams(session)]
        team_name_list.sort()
        session.close()
        
        self.team_array = ["All Teams"] + team_name_list
        self.team_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.team_list.setMaximumSize(800, 400)
        self.team_list.addItems(self.team_array)
        self.team_list.setCurrentRow(0)

        # Create display to show search results (keep)
        self.runner_display = QTextEdit()
        self.runner_display.setFixedWidth(1600)
        self.runner_display.setReadOnly(True)
        self.runner_display.setStyleSheet("font: 10pt \"Courier\";")
        self.runner_display.textChanged.connect(self.saveEnable)

        # Create Score button
        self.score_btn = QPushButton("Score", self)
        self.score_btn.clicked.connect(self.raceScore)

        # Create Simulation button
        self.simulation_btn = QPushButton("Simulation", self)
        self.simulation_btn.clicked.connect(self.setRaceNumber)

        # Create save button
        self.save_btn = QPushButton("Save", self)
        self.save_btn.setEnabled(False)
        self.save_btn.clicked.connect(self.saveToDisk)

        # Create grid layout and add widgets
        self.grid = QGridLayout()
        self.grid.setSpacing(20)

        self.grid.addWidget(self.team_label, 1, 0)
        self.grid.addWidget(self.team_list, 1, 1, 4, 1)
        self.grid.addWidget(self.gender_label, 1, 2)
        self.grid.addWidget(self.gender_cbox, 1, 3)
        self.grid.addWidget(self.status_label, 2, 2)
        self.grid.addWidget(self.status_cbox, 2, 3)
        self.grid.addWidget(self.score_btn, 1, 5)
        self.grid.addWidget(self.simulation_btn, 2, 5)
        self.grid.addWidget(self.save_btn, 3, 5)
        self.grid.addWidget(self.runner_display, 5, 0, 5, 6)

        # Set final window options and display
        self.setLayout(self.grid)
        self.setWindowTitle('Race Simulation')
        self.show()

    def saveEnable(self):

        # Perform necessary checks and adjust Save status accordingly
        if self.runner_display.toPlainText() != "No runners found! Please try again.":
            self.save_btn.setEnabled(True)
        else:
            self.save_btn.setEnabled(False)

    def setRaceNumber(self):

        # Open dialog to input number of races to simulate and pass to Simulation
        i, ok = QInputDialog.getInteger(self, "Number of Race Simulations",
                                              "Enter Number of Races to Simulate (Max 100):           ",
                                              1, 1, 100, 1)
        if ok:
            pass
            self.raceSimulation(i)

    def raceScore(self):

        self.runner_display.clear()

        session = Session()

        # Build and execute the query
        selected_runners = build_query(session, [row.text() for row in self.team_list.selectedItems()],
                                               self.gender_dict[self.gender_cbox.currentText()],
                                               self.status_dict[self.status_cbox.currentText()])

        # Initialize new teams for each team selected by the user
        team_choice = [row.text() for row in self.team_list.selectedItems()]
        if "All Teams" or len(team_choice) == 0:
            team_choice = self.team_array[1:]
        race_teams = []
        
        for team_name in team_choice:
            new_team = Team()
            new_team.name = team_name
            new_team.runners = [runner for runner in selected_runners if runner.team.name == team_name]
            race_teams.append(new_team)

        # Set startlist and display to panel
        race = Race(race_teams)
        self.runner_display.setPlainText(race.startlist())

        session.close()

    def raceSimulation(self, num_races):

        self.runner_display.clear()

        session = Session()

        # Build and execute the query
        selected_runners = build_query(session, [row.text() for row in self.team_list.selectedItems()],
                                               self.gender_dict[self.gender_cbox.currentText()],
                                               self.status_dict[self.status_cbox.currentText()])

        # Initialize new teams for each team selected by the user
        team_choice = [row.text() for row in self.team_list.selectedItems()]
        if "All Teams" or len(team_choice) == 0:
            team_choice = self.team_array[1:]
        race_teams = []
        
        for team_name in team_choice:
            new_team = Team()
            new_team.name = team_name
            new_team.runners = [runner for runner in selected_runners if runner.team.name == team_name]
            race_teams.append(new_team)

        # Run simulations and display results to panel
        race = Race(race_teams)
        self.runner_display.setPlainText(race.run(num_races))

        session.close()

    def saveToDisk(self):

        # Create prompt to input filename
        options = QFileDialog.Options()
        filename, filtr = QFileDialog.getSaveFileName(self,
                                          "Save file",
                                          "",
                                          "Text Files (*.txt)",
                                          "Text Files (*.txt)", options)

        # Save to disk if valid filename
        if filename:
            file = QFile(filename)
            file.open(QIODevice.WriteOnly | QIODevice.Text)
            file.write(self.runner_display.toPlainText())
            file.close

######################################################################################################
#
# Select Runners Widget
#
######################################################################################################

class displaySelect(QWidget):
    """ This will display the menu to search database by team, gender, and status"""

    def __init__(self):
        super(displaySelect, self).__init__()

        # Create the labels
        self.team_label = QLabel('Select Teams:')        
        self.gender_label = QLabel('Select Gender:')
        self.status_label = QLabel('Select Status:')

        # Create display to input gender
        self.gender_cbox = QComboBox()
        self.gender_dict = {'Both' : 0, 'Men' : 'M', 'Women' : 'W'}
        self.gender_cbox.addItems(['Men', 'Women', 'Both'])

        # Create display to input status
        self.status_cbox = QComboBox()
        self.status_dict = {'Active' : 1, 'Not Active' : 0, 'Both' : None}
        self.status_cbox.addItems(['Active', 'Both', 'Not Active'])

        # Create display to input teams
        self.team_list = QListWidget()

        session = Session()
        team_name_list = [team.name for team in get_teams(session)]
        team_name_list.sort()
        session.close()
        
        self.team_array = ["All Teams"] + team_name_list
        self.team_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.team_list.setMaximumSize(800, 400)
        self.team_list.addItems(self.team_array)
        self.team_list.setCurrentRow(0)

        # Create table to display search results
        self.runner_table = QTableWidget(15, 5)
        self.runner_table.verticalHeader().setVisible(False)
        self.runner_table.setHorizontalHeaderLabels(['Name','Gender','Team Name', 'Rating', 'Status'])

        # Create search button
        self.search_btn = QPushButton("Search", self)
        self.search_btn.clicked.connect(self.selectRunners)

        # Create save button
        self.save_btn = QPushButton("Save", self)
        self.save_btn.setEnabled(False)
        self.save_btn.clicked.connect(self.saveToDisk)

        # Create grid layout and add widgets
        self.grid = QGridLayout()
        self.grid.setSpacing(20)

        self.grid.addWidget(self.team_label, 1, 0)
        self.grid.addWidget(self.team_list, 1, 1, 4, 1)
        self.grid.addWidget(self.gender_label, 1, 2)
        self.grid.addWidget(self.gender_cbox, 1, 3)
        self.grid.addWidget(self.status_label, 2, 2)
        self.grid.addWidget(self.status_cbox, 2, 3)
        self.grid.addWidget(self.search_btn, 1, 5)
        self.grid.addWidget(self.save_btn, 2, 5)
        self.grid.addWidget(self.runner_table, 5, 0, 5, 6)

        # Set final window options and display
        self.setLayout(self.grid)
        self.setWindowTitle('Select Runners')
        self.show()

    def selectRunners(self):

        self.runner_table.setSortingEnabled(False)
        self.runner_table.clearContents()
        
        session = Session()

        # Build and execute the query
        selected_runners = build_query(session, [row.text() for row in self.team_list.selectedItems()],
                                               self.gender_dict[self.gender_cbox.currentText()],
                                               self.status_dict[self.status_cbox.currentText()])

        # Print runners to display
        if len(selected_runners) == 0:
            pass # Add dialog box here
        else:
            self.runner_table.setRowCount(len(selected_runners))
            for i, runner in enumerate(selected_runners):
                name = QTableWidgetItem(runner.name)
                gender = QTableWidgetItem(runner.gender)
                team_name = QTableWidgetItem(runner.team.name)
                rating = QTableWidgetItem()
                rating.setData(Qt.EditRole, runner.rating)
                status = QTableWidgetItem(str(int(runner.status)))
                self.runner_table.setItem(i, 0, name)
                self.runner_table.setItem(i, 1, gender)
                self.runner_table.setItem(i, 2, team_name)
                self.runner_table.setItem(i, 3, rating)
                self.runner_table.setItem(i, 4, status)
            self.runner_table.setSortingEnabled(True)
            self.runner_table.resizeColumnsToContents()
            self.save_btn.setEnabled(True)

        session.close()

    def saveToDisk(self):

        # Create prompt to input filename
        options = QFileDialog.Options()
        filename, filtr = QFileDialog.getSaveFileName(self,
                                          "Save file",
                                          "",
                                          "CSV Files (*.csv)",
                                          "CSV Files (*.csv)", options)

        print(filename)
        print(type(filename))

        # Save to disk if valid filename
        if filename:
            print('attempting to print')
            with open(filename, 'w') as f:
                writer = csv.writer(f, delimiter=',', lineterminator='\n')
                for row in range(self.runner_table.rowCount()):
                    rowdata = []
                    for column in range(self.runner_table.columnCount()):
                        item = self.runner_table.item(row, column)
                        rowdata.append(item.text())
                    writer.writerow(rowdata)

######################################################################################################
#
# Main Widget
#
######################################################################################################

class widgetMain(QWidget):
    
    def __init__(self, screen):
        super(widgetMain, self).__init__()

        # Create widgets to populate the program
        self.select_page = displaySelect()
        self.race_page = raceSimulation()

        # Create the stacked widget to store other widgets
        self.stackedWidget = QStackedWidget()
        self.stackedWidget.addWidget(self.select_page)
        self.stackedWidget.addWidget(self.race_page)


        # Create widget selection box
        self.pageComboBox = QComboBox()
        self.pageComboBox.addItem("Select by Team, Gender, and Status")
        self.pageComboBox.addItem("Run Race Simulations")
        self.connect(self.pageComboBox, SIGNAL("activated(int)"),
                     self.stackedWidget, SLOT("setCurrentIndex(int)"))

        # Set layout and populate
        self.vbox = QVBoxLayout()
        self.vbox.addWidget(self.pageComboBox)
        self.vbox.addWidget(self.stackedWidget)
        self.setLayout(self.vbox)

        # Set final geometry options and display
        self.setWindowTitle('Main Menu')
        self.show()

######################################################################################################
#
# Main Window
#
######################################################################################################

class windowMain(QMainWindow):

    def __init__(self, screen):
        super(windowMain, self).__init__()

        # Create actions for menubar and status bar
        exitAction = QAction(QIcon('exit.png'), '&Exit', self)
        exitAction.setShortcut('Ctrl+Q')
        exitAction.setStatusTip('Exit application')
        exitAction.triggered.connect(self.close)

        formatAction = QAction('Format Results', self)
        formatAction.setStatusTip('Format results for processing')
        formatAction.triggered.connect(self.formatResultWizard)

        addResultAction = QAction('Add Results', self)
        addResultAction.setStatusTip('Add processed results to database')
        addResultAction.triggered.connect(self.addResultWizard)
        
        self.statusBar()

        # Create menubar and add actions
        menubar = self.menuBar()
        
        fileMenu = menubar.addMenu('&File')
        fileMenu.addAction(exitAction)
        
        editMenu = menubar.addMenu('Edit')
        editMenu.addAction(formatAction)
        editMenu.addAction(addResultAction)

        # Create and set central widget
        self.main_widget = widgetMain(screen)
        self.setCentralWidget(self.main_widget)

        # Set final geometry options and display
        self.setGeometry(10, 50, screen.width(), screen.height())
        self.showMaximized()
        self.setWindowTitle('NIRCA Database 6.1')
        self.show()

        #########################################

    def formatResultWizard(self):

        # Initializes and runs the Wizard
        self.format_wizard = formatWizard()
        self.format_wizard.show()

    def addResultWizard(self):
        self.add_wizard = addWizard()
        self.add_wizard.show()

######################################################################################################
#
# Misc. Functions
#
######################################################################################################

def get_teams(session):
    """Creates and executes a query to return a list of all teams in database"""

    # Create and execute query to select team names
    team_name_query = session.query(Team)
    team_list = team_name_query.all()

    return team_list

def get_team_names(session):
    """Creates and executes a query to return a list of names for all teams in database"""

    team_name_query = session.query(Team.name)
    team_name_list = team_name_query.all()

    return [team[0] for team in team_name_list]

def build_query(session, team_choice=[], gender_choice=0, status_choice= None):
    """Creates and executes a query to return all runners, based on team, gender, and status"""

    # Initialize session and query
    search_query = session.query(Runner)

    # Format gender selection
    if gender_choice:
        search_query = search_query.filter_by(gender = gender_choice)

    # Format status selection
    if status_choice != None:
        search_query = search_query.filter_by(status = status_choice)

    # Format team selection
    if "All Teams" in team_choice:
        team_choice = []

    if len(team_choice) == 1:
        search_query = search_query.join(Team).filter_by(name = team_choice[0])
    elif len(team_choice) > 1:
        search_query = search_query.join(Team).filter(Team.name.in_(team_choice))

    return search_query.all()    

def find_team_match(word, team_list, threshold=0.8):
    """Attempts to find the best team match for a team name, from a list of teams"""

    results = []
    for team in team_list:
        cost = jf.jaro_distance(unicode(word), unicode(team.name))

        if cost > threshold:
            results.append((team, cost))

    if len(results) > 1:
        results.sort(key=lambda x: x[1], reverse=True)

    # If no match, do something
    if len(results) == 0:
        return "No Match Found!"

    return results[0][0]

def find_match(name, word_list, threshold=0.8, find_multiple=False):
    """Attempts to find the best match for a word, from a list of words"""
    
    results = []
    for word in word_list:
        cost = jf.jaro_distance(unicode(name), unicode(word))

        if cost > threshold:
            results.append((word, cost))

    if len(results) > 1:
        results.sort(key=lambda x: x[1], reverse=True)

    if len(results) == 0:
        return "No Match Found!"

    if not find_multiple:
        return results[0][0]        

def update_runner(runner, result):
    """Updates a runner, after a new result is added to the database"""

    # If new, set rating to the result rating
    if runner.rating == None:
        runner.status = True
        runner.rating = round(result.rating, 3)
        return

    # If inactive, change status to active and set rating to result rating
    if not runner.status:
        runner.status = True
        runner.rating = round(result.rating, 3)
        return

    # If in database, calculate new rating from current rating and result rating
    diff = abs(result.rating - runner.rating)
    if diff >= 40:
        new_rating = max(result.rating, runner.rating)*0.9 + min(result.rating, runner.rating)*0.1
    elif 30 <= diff < 40:
        new_rating = max(result.rating, runner.rating)*0.85 + min(result.rating, runner.rating)*0.15
    elif 20 < diff < 30:
        new_rating = max(result.rating, runner.rating)*0.8 + min(result.rating, runner.rating)*0.2
    else:
        new_rating = max(result.rating, runner.rating)*0.75 + min(result.rating, runner.rating)*0.25

    runner.rating = round(new_rating, 3)
    return

######################################################################################################
#
# Main Function
#
######################################################################################################

def main():

    # Initialize sqlalchemy database    
    engine = create_engine('sqlite:///XC_2015.db', echo=False)
    Base.metadata.create_all(engine)
    Session.configure(bind=engine)

    # Initialize main window
    app = QApplication(sys.argv)
    screen = QDesktopWidget().screenGeometry()
    main_window = windowMain(screen)
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()

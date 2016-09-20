#!/usr/bin/env python

import sys
import NIRCAdb as ndb
import argparse
import copy
import csv

from NIRCAdb import search as ndbsearch
from NIRCAdb import errors as ndberrors
from PyQt4 import QtCore, QtGui

DATABASE = None

################################################################################
##
## Update Database Wizard
##
################################################################################

class UpdateWizard(QtGui.QWizard):
    NUM_PAGES = 5

    (PageIntro, PageTeamMatch, PageRunnerMatch, PageModify,
     PageConclusion) = range(NUM_PAGES)

    def __init__(self, parent=None):
        super(UpdateWizard, self).__init__(parent)

        self.setPage(self.PageIntro, IntroPage(self))
        self.setPage(self.PageTeamMatch, TeamMatchPage())
        self.setPage(self.PageRunnerMatch, RunnerMatchPage())
        self.setPage(self.PageModify, ModifyPage())
        self.setPage(self.PageConclusion, ConclusionPage())

        self.setStartId(self.PageIntro)

        self.setWindowTitle("Update Wizard")

################################################################################
##
## Change Team Dialog
##
################################################################################

class ChangeTeamDialog(QtGui.QDialog):

    def __init__(self, name, database_names):
        super(ChangeTeamDialog, self).__init__()

        self.match = None

        ## Create QWidget objects
        self.selectLabel = QtGui.QLabel('Select New')
        self.nameComboBox = QtGui.QComboBox()
        self.nameComboBox.addItems(sorted(database_names))

        self.newLabel = QtGui.QLabel('Add Team: {0}'.format(name))
        self.newLineEdit = QtGui.QLineEdit()
        self.regionLabel = QtGui.QLabel('Select Region')
        
        self.regionComboBox = QtGui.QComboBox()
        region_items = copy.deepcopy(ndb.REGIONS)
        region_items.sort()
        region_items.insert(0, "")
        self.regionComboBox.addItems(region_items)

        self.hline = QtGui.QFrame()
        self.hline.setFrameShape(QtGui.QFrame.HLine)
        self.hline.setFrameShadow(QtGui.QFrame.Sunken)

        self.buttons = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Ok |
                                              QtGui.QDialogButtonBox.Cancel,
                                              QtCore.Qt.Horizontal, self)

        ## Connect Signals and Slots
        self.buttons.accepted.connect(self.update)
        self.buttons.rejected.connect(self.reject)

        ## Create Layout
        layout = QtGui.QVBoxLayout()
        layout.addWidget(self.selectLabel)
        layout.addWidget(self.nameComboBox)
        layout.addWidget(self.hline)
        layout.addWidget(self.newLabel)
        layout.addWidget(self.newLineEdit)
        layout.addWidget(self.regionLabel)
        layout.addWidget(self.regionComboBox)
        layout.addWidget(self.buttons)

        self.setLayout(layout)

    @staticmethod
    def getMatch(name, database_names):
        dialog = ChangeTeamDialog(name, database_names)
        result = dialog.exec_()
        new = dialog.match
        return (new, result == QtGui.QDialog.Accepted)

    @QtCore.pyqtSlot()
    def update(self):

        ## Check if new team needs to be added
        if self.newLineEdit.isModified():
            
            with ndb.db_session(DATABASE) as session:

                name = str(self.newLineEdit.text())
                region = str(self.regionComboBox.currentText())
                new_team = ndb.Team(name=name, region=region)
                new_team.add_to_db(session)

        else:
            name = str(self.nameComboBox.currentText())
            
        self.match = name
        self.accept()

################################################################################
##
## Change Runner Dialog
##
################################################################################

class ChangeRunnerDialog(QtGui.QDialog):

    def __init__(self, name, database_names):
        super(ChangeRunnerDialog, self).__init__()

        self.match = None

        ## Create QWidget objects
        self.selectLabel = QtGui.QLabel('Select New')
        self.nameComboBox = QtGui.QComboBox()
        self.nameComboBox.addItems(sorted(database_names))

        self.newLabel = QtGui.QLabel('Add Runner: {0}'.format(name))
        self.newLineEdit = QtGui.QLineEdit()

        self.hline = QtGui.QFrame()
        self.hline.setFrameShape(QtGui.QFrame.HLine)
        self.hline.setFrameShadow(QtGui.QFrame.Sunken)

        self.buttons = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Ok |
                                              QtGui.QDialogButtonBox.Cancel,
                                              QtCore.Qt.Horizontal, self)

        ## Connect Signals and Slots
        self.buttons.accepted.connect(self.update)
        self.buttons.rejected.connect(self.reject)

        ## Create Layout
        layout = QtGui.QVBoxLayout()
        layout.addWidget(self.selectLabel)
        layout.addWidget(self.nameComboBox)
        layout.addWidget(self.hline)
        layout.addWidget(self.newLabel)
        layout.addWidget(self.newLineEdit)
        layout.addWidget(self.buttons)

        self.setLayout(layout)

    @staticmethod
    def getMatch(name, database_names):
        dialog = ChangeRunnerDialog(name, database_names)
        result = dialog.exec_()
        new = dialog.match
        return (new, result == QtGui.QDialog.Accepted)

    @QtCore.pyqtSlot()
    def update(self):

        ## Check if new team needs to be added
        if self.newLineEdit.isModified():
            name = str(self.newLineEdit.text())
        else:
            name = str(self.nameComboBox.currentText())
            
        self.match = name
        self.accept()

################################################################################
##
## Multi-Match Display
##
################################################################################

class MultiMatchDisplay(QtGui.QWidget):

    matches_changed = QtCore.pyqtSignal(int)

    def __init__(self, matches, database_names, parent=None):
        super(MultiMatchDisplay, self).__init__(parent)

        self._perfect = []
        self._imperfect = []
        self.database_names = database_names

        ## Separate perfect matches and imperfect matches
        for match in matches:
            if match[2] == 100:
                self._perfect.append(match)

            else:
                self._imperfect.append(match)

        ## If there are imperfect matches construct display
        if len(self._imperfect) > 0:

            ## Initialize QSignalMappers
            self.selectSignalMapper = QtCore.QSignalMapper(self)
            self.addSignalMapper = QtCore.QSignalMapper(self)

            ## Create QWidget objects
            self.nameLabel = QtGui.QLabel('Names: ')
            self.matchLabel = QtGui.QLabel('Matched Name: ')
            self.nameLabels = []
            self.nameLineEdits = []
            self.newButtons = []

            
            ## Create grid layout
            self.grid = QtGui.QGridLayout()
            self.grid.setSpacing(20)
            self.grid.addWidget(self.nameLabel, 1, 0)
            self.grid.addWidget(self.matchLabel, 1, 1)

            ## Populate grid
            for i, match in enumerate(self._imperfect):

                nameLabel = QtGui.QLabel(match[0])
                nameLineEdit = QtGui.QLineEdit(match[1])
                nameLineEdit.setReadOnly(True)

                newButton = QtGui.QPushButton('Select')
                self.selectSignalMapper.setMapping(newButton, i)
                newButton.clicked.connect(self.selectSignalMapper.map)

                self.nameLabels.append(nameLabel)
                self.nameLineEdits.append(nameLineEdit)
                self.newButtons.append(newButton)

                self.grid.addWidget(nameLabel, i+2, 0)
                self.grid.addWidget(nameLineEdit, i+2, 1)
                self.grid.addWidget(newButton, i+2, 2)

            ## Connect Signals and Slots 
            self.selectSignalMapper.mapped.connect(self.modify)

            self.setLayout(self.grid)

        ## Else all teams matched perfectly
        else:

            self.goodLabel = QtGui.QLabel('All teams found!')
            self.grid = QtGui.QGridLayout()
            self.grid.addWidget(self.goodLabel)
            self.setLayout(self.grid)

    @QtCore.pyqtProperty(list)
    def matches(self):
        return self._perfect + self._imperfect

    def setMatch(self, index, new_match):
        raise NotImplementedError('Subclasses must define setMatch()')

    def modify(self):
        raise NotImplementedError('Subclasses must define modify()')

class TeamMultiDisplay(MultiMatchDisplay):

    def __init__(self, matches, database_names, parent=None):
        super(TeamMultiDisplay, self).__init__(matches, database_names,
                                               parent)

    def setMatch(self, index, new_match):
        name = self._imperfect[index][0]
        self.nameLineEdits[index].setText(new_match)
        self._imperfect[index] = (name, new_match, 100)
        self.matches_changed.emit(index)

    def modify(self, index):

        ## Select new match using dialog
        new_match, ok = ChangeTeamDialog.getMatch(self.nameLabels[index].text(),
                                                 self.database_names)

        ## Check if valid and update
        if ok:
            self.setMatch(index, new_match)

class RunnerMultiDisplay(MultiMatchDisplay):

    def __init__(self, matches, database_names, parent=None):
        super(RunnerMultiDisplay, self).__init__(matches, database_names,
                                               parent)

    def setMatch(self, index, new_match):
        name = self._imperfect[index][0]
        team = self._imperfect[index][3]
        time = self._imperfect[index][4]
        self.nameLineEdits[index].setText(new_match)
        self._imperfect[index] = (name, new_match, 100, team, time)
        self.matches_changed.emit(index)

    def modify(self, index):

        ## Select new match using dialog
        new_match, ok = ChangeRunnerDialog.\
                        getMatch(self.nameLabels[index].text(),
                                 self.database_names[index])

        ## Check if valid and update
        if ok:
            self.setMatch(index, new_match)

################################################################################
##
## Race Table Widget
##
################################################################################

class RaceTableWidget(QtGui.QTableWidget):

    def __init__(self, rows):
        super(RaceTableWidget, self).__init__(rows, 4)

        self.verticalHeader().setVisible(False)
        self.setHorizontalHeaderLabels(['Runner ID', 'Time', 'Current Rating',
                                        'Race Rating'])

        self.race = None

    def addRace(self, race, old_ratings):

        self.race = race
        self.old_ratings = old_ratings

        self.setRowCount(len(self.old_ratings))
        for i, result in enumerate(self.race.results):

            runner_id = QtGui.QTableWidgetItem(str(result.runner_id))
            time = QtGui.QTableWidgetItem(str(result.time)) # may have to format

            if self.old_ratings[i] is not None:
                oldrating = QtGui.QTableWidgetItem(str(self.old_ratings[i]))
            else:
                oldrating = QtGui.QTableWidgetItem(str('None'))

            self.setItem(i, 0, runner_id)
            self.setItem(i, 1, time)
            self.setItem(i, 2, oldrating)

        self.resizeColumnsToContents()

    def calculate_ratings(self, r200):

        self.race.calculate_ratings(r200)

        error = 0
        for i, result in enumerate(self.race.results):

            newrating = QtGui.QTableWidgetItem(str(result.rating))
            self.setItem(i, 3, newrating)

            if self.old_ratings[i] is None:
                error += 0
            else:
                diff = float(self.old_ratings[i])-result.rating
                if abs(diff) <= 20.0:
                    error += diff**2.

        return error

    def export_to_csv(self, filename):

        with open(filename, 'w') as f:
            writer = csv.writer(f)

            for i, result in enumerate(self.race.results):

                time_in_s = sum(float(x) * 60 ** i for i,x in \
                                enumerate(reversed(result.time.split(":"))))

                if self.old_ratings[i] is None:
                    old_rating = ''
                else:
                    old_rating = str(self.old_ratings[i])

                writer.writerow([result.runner_id, time_in_s,
                                 result.rating, old_rating])

        
################################################################################
##
## Intro Wizard Page
##
################################################################################

class IntroPage(QtGui.QWizardPage):
    
    def __init__(self, parent=None):
        super(IntroPage, self).__init__(parent)

        self.setTitle(self.tr('Introduction'))

        ## Create QWidget objects
        self.topLabel = QtGui.QLabel('This Wizard will help you add results '
                                     'to the NIRCA database.')
        self.nameLabel = QtGui.QLabel('Name: ')
        self.dateLabel = QtGui.QLabel('Date: ')
        self.genderLabel = QtGui.QLabel('Gender: ')
        self.distanceLabel = QtGui.QLabel('Race Distance: ')
        self.fileButton = QtGui.QPushButton('Get Filename')
        self.nameEdit = QtGui.QLineEdit()

        self.fileEdit = QtGui.QLineEdit()
        self.fileEdit.setReadOnly(True)
        
        self.dateEdit = QtGui.QDateEdit(QtCore.QDate.currentDate())
        self.dateEdit.setDisplayFormat('yyyy-MM-dd')
        self.dateEdit.setCalendarPopup(True)

        self.genderComboBox = QtGui.QComboBox()
        self.genderComboBox.addItem('Choose Gender')
        self.genderComboBox.addItem('Men')
        self.genderComboBox.addItem('Women')

        self.distanceComboBox = QtGui.QComboBox()
        self.distanceComboBox.addItem('Choose Race Distance (meters)')
        self.distanceComboBox.addItem('4000')
        self.distanceComboBox.addItem('5000')
        self.distanceComboBox.addItem('6000')
        self.distanceComboBox.addItem('8000')

        ## Connect Signals and Slots
        self.fileButton.clicked.connect(self.getFile)

        ## Create Layout
        self.grid = QtGui.QGridLayout()
        self.grid.addWidget(self.topLabel, 1, 0)
        self.grid.addWidget(self.nameLabel, 2, 0)
        self.grid.addWidget(self.dateLabel, 3, 0)
        self.grid.addWidget(self.genderLabel, 4, 0)
        self.grid.addWidget(self.distanceLabel, 5, 0)
        self.grid.addWidget(self.nameEdit, 2, 1)
        self.grid.addWidget(self.dateEdit, 3, 1)
        self.grid.addWidget(self.genderComboBox, 4, 1)
        self.grid.addWidget(self.distanceComboBox, 5, 1)
        self.grid.addWidget(self.fileButton, 6, 0)
        self.grid.addWidget(self.fileEdit, 6, 1)        
        self.setLayout(self.grid)

        ## Register fields
        self.registerField('race_name*', self.nameEdit)
        self.registerField('race_date', self.dateEdit, 'date',
                           self.dateEdit.dateChanged)
        self.registerField('race_gender*', self.genderComboBox)
        self.registerField('race_distance*', self.distanceComboBox,
                           'currentText', self.distanceComboBox.\
                           currentIndexChanged)
        self.registerField('filename*', self.fileEdit)

    def getFile(self):

        ## Prompt for filename
        filename = QtGui.QFileDialog.\
                   getOpenFileName(self, caption='Select file',
                                   directory='',
                                   filter='Text Files (*.csv)',
                                   selectedFilter='Text Files (*.csv)')

        ## Check if valid and update
        if filename:
            self.fileEdit.setText(filename)
            

################################################################################
##
## Team Match Page
##
################################################################################

class TeamMatchPage(QtGui.QWizardPage):

    def __init__(self, parent=None):
        super(TeamMatchPage, self).__init__(parent)

        ## Set up scroll bars
        self.scroll = QtGui.QScrollArea()
        self.scroll.setWidgetResizable(False)

        ## Create QWidget objects
        self.confirmCheckBox = QtGui.QCheckBox('Confirm')

        ## Register fields
        self.registerField('team_confirm*', self.confirmCheckBox)

    def initializePage(self):

        ## Read result CSV file
        filename = self.field('filename').toString()
        team_names = set()
        
        with open(filename, 'r') as f:
            data = f.readlines()
            for row in data:
                cols = str.split(row, ',')
                team_names.add(cols[1])
            team_names = list(team_names)

        ## Query database for list of teams
        with ndb.db_session(DATABASE) as session:
            database_teams = ndb.Team.from_db(session)
            self.database_team_names = [team.name for team in database_teams]

            team_matches = []
            for team_name in team_names:

                team_match = ndbsearch.team_search(team_name, limit=1,
                                                   team_list=database_teams)[0]
                
                
                team_matches.append((team_name, team_match[0].name,
                                     team_match[1]))
        

        ## Create a MultiMatchDisplay
        self.teammatchesDisplay = TeamMultiDisplay(team_matches,
                                                   self.database_team_names)

        ## Finalize scroll area
        self.scroll.setWidget(self.teammatchesDisplay)
        vLayout = QtGui.QVBoxLayout(self)
        vLayout.addWidget(self.scroll)
        vLayout.addWidget(self.confirmCheckBox)
        self.setLayout(vLayout)

        self.registerField('team_matches', self.teammatchesDisplay, 'matches')
            
            
################################################################################
##
## Runner Match Page
##
################################################################################

class RunnerMatchPage(QtGui.QWizardPage):

    def __init__(self, parent=None):
        super(RunnerMatchPage, self).__init__(parent)

        ## Set up scroll bars
        self.scroll = QtGui.QScrollArea()
        self.scroll.setWidgetResizable(False)

        ## Create QWidget objects
        self.confirmCheckBox = QtGui.QCheckBox('Confirm')

        ## Register fields
        self.registerField('runner_check*', self.confirmCheckBox)

    def initializePage(self):

        ## Get race information
        gender_dict = {1: 'M', 2 : 'W'}
        race_gender = gender_dict[self.field('race_gender').toPyObject()]

        ## Construct team dictionary
        team_dict = dict()
        team_matches = self.field('team_matches').toPyObject()
        for team_name, database_match, ratio in team_matches:
            team_dict[team_name] = database_match

        ## Read result CSV
        filename = self.field('filename').toString()

        runner_info_list = []
        with open(filename, 'r') as f:
            data = f.readlines()
            for row in data:
                cols = str.split(row, ',')
                runner_name = cols[0]
                runner_team_name = team_dict[cols[1]]
                runner_time = cols[2].rstrip()
                runner_info_list.append((runner_name, runner_team_name,
                                         runner_time))

        ## Query database for list of runners
        with ndb.db_session(DATABASE) as session:
            team_list = list(team_dict.values())

            ## Get runners from all teams in the race
            database_runners = ndb.Runner.from_db(session,
                                                  team_list=team_list,
                                                  gender=race_gender)

            runner_matches = []
            self.database_runner_names = []

            ## Find a database match for each runner in the results file
            for runner_info in runner_info_list:

                runner_list = [runner for runner in database_runners if
                               runner.team.name == runner_info[1]]

                search_result = ndbsearch.runner_search(runner_info[0], limit=1,
                                                       runner_list=runner_list)[0]

                runner_match = (runner_info[0], search_result[0].name,
                                search_result[1], runner_info[1],
                                runner_info[2])

                runner_matches.append(runner_match)
                
                self.database_runner_names.append([runner.name for \
                                                   runner in runner_list])

        ## Create a MultiMatchDisplay
        self.runnermatchesDisplay = RunnerMultiDisplay(runner_matches,
                                                       self.database_runner_names)

        ## Finalize scroll area
        self.scroll.setWidget(self.runnermatchesDisplay)
        vLayout = QtGui.QVBoxLayout(self)
        vLayout.addWidget(self.scroll)
        vLayout.addWidget(self.confirmCheckBox)
        self.setLayout(vLayout)

        self.registerField('runner_matches', self.runnermatchesDisplay,
                           'matches')


################################################################################
##
## Modify Page
##
################################################################################

class ModifyPage(QtGui.QWizardPage):

    def __init__(self):
        super(ModifyPage, self).__init__()

        ## Create QWidget objects
        self.ratingLabel = QtGui.QLabel('Assign 200 SR Time:')
        self.ratingSpinBox = QtGui.QDoubleSpinBox()
        self.ratingSpinBox.setDecimals(3)
        self.ratingSpinBox.setRange(500.000, 1800.000)
        self.ratingSpinBox.setSuffix(' s')

        self.errorLabel = QtGui.QLabel('Error:')
        self.errorEdit = QtGui.QLineEdit()

        self.raceTable = RaceTableWidget(15)

        self.generateButton = QtGui.QPushButton('Generate')
        self.exportButton = QtGui.QPushButton('Export')
        self.addButton = QtGui.QPushButton('Add')
        self.confirmCheckBox = QtGui.QCheckBox('Confirm')

        ## Set up layout
        self.grid = QtGui.QGridLayout()
        self.grid.setSpacing(20)

        self.grid.addWidget(self.ratingLabel, 0, 0)
        self.grid.addWidget(self.ratingSpinBox, 0, 1)
        self.grid.addWidget(self.generateButton, 0, 2)
        self.grid.addWidget(self.errorLabel, 0, 4)
        self.grid.addWidget(self.errorEdit, 0, 5)
        self.grid.addWidget(self.raceTable, 1, 0, 10, 6)
        self.grid.addWidget(self.exportButton, 12, 0)
        self.grid.addWidget(self.addButton, 12, 4)
        self.grid.addWidget(self.confirmCheckBox, 12, 5)
        self.setLayout(self.grid)

        ## Connect signals and slots

        ## Register fields
        self.registerField('modify_check*', self.confirmCheckBox)

    def initializePage(self):

        ## Get race information
        gender_dict = {1: 'M', 2 : 'W'}
        self.race_gender = gender_dict[self.field('race_gender').toPyObject()]
        self.race_distance = int(self.field('race_distance').toPyObject())
        self.runner_matches = self.field('runner_matches').toPyObject()
        date =  self.field('race_date').toPyObject()
        self.race_date = date.toPyDate()
        self.race_name = str(self.field('race_name').toPyObject())

        print type(self.race_distance)
        print type(self.race_date)
        print type(self.race_name)

        if self.race_gender == 'M':
            self.ratingSpinBox.setValue(1500.000)
        else:
            self.ratingSpinBox.setValue(1125.000)

        ## Add new runners and create Race object
        result_list = []
        old_ratings = []
        with ndb.db_session(DATABASE) as session:
            
            for i, match in enumerate(self.runner_matches):

                try:
                    runner = ndb.Runner.from_db(session,
                                                names = match[1])[0]
                except ndberrors.QueryError:
                    runner = ndb.Runner(name = match[1], status = True,
                                    gender = self.race_gender)

                    team = ndb.Team.from_db(session,
                                            names = match[3])[0]
                    team.runners.append(runner)
                    session.flush()

                print runner.id, runner.name

                result = ndb.Result(name=self.race_name,
                                    date=self.race_date,
                                    distance=self.race_distance,
                                    rating=None, time = match[4],
                                    runner_id = runner.id)
                result_list.append(result)
                old_ratings.append(runner.rating)

        race = ndb.Race(self.race_name,
                        self.race_date,
                        self.race_distance, result_list)

        self.raceTable.addRace(race, old_ratings)

        self.update()

        self.ratingSpinBox.valueChanged.connect(self.update)
        self.exportButton.clicked.connect(self.export)
        self.addButton.clicked.connect(self.add)

    def generate(self):
        pass

    @QtCore.pyqtSlot()
    def update(self):

        r200 = self.ratingSpinBox.value()
        
        error = self.raceTable.calculate_ratings(r200)

        self.errorEdit.setText('{0:.3f}'.format(error))

    @QtCore.pyqtSlot()
    def export(self):

        filename = '{0}_{1}_Raw.csv'.format(self.race_name, self.race_gender)
        print filename
        self.raceTable.export_to_csv(filename)

    @QtCore.pyqtSlot()
    def add(self):

        with ndb.db_session(DATABASE) as session:
            self.raceTable.race.process(session)

################################################################################
##
## Conclusion Page
##
################################################################################

class ConclusionPage(QtGui.QWizardPage):

    def __init__(self):
        super(ConclusionPage, self).__init__()

        self.conclusionLabel = QtGui.QLabel('Results have been added.')

        self.grid = QtGui.QGridLayout()
        self.grid.addWidget(self.conclusionLabel, 0, 0)
        self.setLayout(self.grid)
        

################################################################################
##
## Main Function
##
################################################################################

def main(database):

    global DATABASE
    DATABASE = 'sqlite:///{0}'.format(database)

    app = QtGui.QApplication(sys.argv)
    wiz = UpdateWizard()
    wiz.show()
    sys.exit(app.exec_())

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--database', help='database to modify.',
                        default='test.db')

    args = parser.parse_args()
    database = args.database

    main(database)

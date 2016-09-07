#!/usr/bin/env python

import sys
import NIRCAdb as ndb
import argparse
import copy

from NIRCAdb import search as ndbsearch
from PyQt4 import QtCore, QtGui

DATABASE = None

################################################################################
##
## Update Database Wizard
##
################################################################################

class UpdateWizard(QtGui.QWizard):
    NUM_PAGES = 6

    (PageIntro, PageTeamMatch, PageRunnerMatch, PageModify,
     PageConfirmation, PageConclusion) = range(NUM_PAGES)

    def __init__(self, parent=None):
        super(UpdateWizard, self).__init__(parent)

        self.setPage(self.PageIntro, IntroPage(self))
        self.setPage(self.PageTeamMatch, TeamMatchPage())
        self.setPage(self.PageRunnerMatch, RunnerMatchPage())
        self.setPage(self.PageModify, ModifyPage())
        self.setPage(self.PageConfirmation, ConfirmationPage())
        self.setPage(self.PageConclusion, ConclusionPage())

        self.setStartId(self.PageIntro)

        self.setWindowTitle("Update Wizard")

################################################################################
##
## Change Match Dialog
##
################################################################################

class ChangeMatchDialog(QtGui.QDialog):

    def __init__(self, name, database_names):
        super(ChangeMatchDialog, self).__init__()

        ## Create QWidget objects
        self.selectLabel = QtGui.QLabel('Select New')
        self.nameLabel = QtGui.QLabel('Name: {0}'.format(name))
     
        self.nameComboBox = QtGui.QComboBox()
        self.nameComboBox.addItems(sorted(database_names))

        self.buttons = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Ok |
                                              QtGui.QDialogButtonBox.Cancel,
                                              QtCore.Qt.Horizontal, self)

        ## Connect Signals and Slots
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

        ## Create Layout
        layout = QtGui.QVBoxLayout()
        layout.addWidget(self.nameLabel)
        layout.addWidget(self.selectLabel)
        layout.addWidget(self.nameComboBox)
        layout.addWidget(self.buttons)

        self.setLayout(layout)

    @staticmethod
    def getMatch(name, database_names):
        dialog = ChangeMatchDialog(name, database_names)
        result = dialog.exec_()
        new = str(dialog.new_match())
        return (new, result == QtGui.QDialog.Accepted)

    def new_match(self):

        new_name = self.nameComboBox.currentText()
        return new_name

################################################################################
##
## Add Team Dialog
##
################################################################################

class AddTeamDialog(QtGui.QDialog):

    def __init__(self, name):
        super(AddTeamDialog, self).__init__()

        ## Create QWidget objects
        self.newLabel = QtGui.QLabel('Add Team: {0}'.format(name))
        self.newLineEdit = QtGui.QLineEdit()
        self.regionLabel = QtGui.QLabel('Select Region')
        self.regionComboBox = QtGui.QComboBox()

        region_items = copy.deepcopy(ndb.REGIONS)
        region_items.sort()
        region_items.insert(0, "")
        self.regionComboBox.addItems(region_items)

        self.buttons = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Ok |
                                              QtGui.QDialogButtonBox.Cancel,
                                              QtCore.Qt.Horizontal, self)

        ## Connect Signals and Slots
        self.buttons.accepted.connect(self.add)
        self.buttons.rejected.connect(self.reject)

        ## Create Layout
        layout = QtGui.QVBoxLayout()
        layout.addWidget(self.newLabel)
        layout.addWidget(self.newLineEdit)
        layout.addWidget(self.regionLabel)
        layout.addWidget(self.regionComboBox)
        layout.addWidget(self.buttons)

        self.setLayout(layout)

    @staticmethod
    def addTeam(name):
        dialog = AddTeamDialog(name)
        result = dialog.exec_()
        new = str(dialog.new_team())
        return (new, result == QtGui.QDialog.Accepted)

    @QtCore.pyqtSlot()
    def add(self):

        with ndb.db_session(DATABASE) as session:

            name = str(self.newLineEdit.text())
            region = str(self.regionComboBox.currentText())
            new_team = ndb.Team(name=name, region=region)
            new_team.add_to_db(session)

        self.accept()

    def new_team(self):

        new = self.newLineEdit.text()
        return new

################################################################################
##
## Multi-Match Display
##
################################################################################

class MultiMatchDisplay(QtGui.QWidget):

    matches_changed = QtCore.pyqtSignal(int)

    def __init__(self, matches, database_names, parent=None):
        super(MultiMatchDisplay, self).__init__()

        self.database_names = database_names
        self._matches = matches

        ## Initialize QSignalMappers
        self.selectSignalMapper = QtCore.QSignalMapper(self)
        self.addSignalMapper = QtCore.QSignalMapper(self)

        ## Create QWidget objects
        self.nameLabel = QtGui.QLabel('Names: ')
        self.matchLabel = QtGui.QLabel('Matched Name: ')
        self.nameLabels = []
        self.nameLineEdits = []
        self.newButtons = []
        self.addButtons = []

        ## Create grid layout
        self.grid = QtGui.QGridLayout()
        self.grid = QtGui.QGridLayout()
        self.grid.setSpacing(20)
        self.grid.addWidget(self.nameLabel, 1, 0)
        self.grid.addWidget(self.matchLabel, 1, 1)

        ## Populate grid
        for i, match in enumerate(matches):

            nameLabel = QtGui.QLabel(match[0])
            nameLineEdit = QtGui.QLineEdit(match[1])
            nameLineEdit.setReadOnly(True)

            newButton = QtGui.QPushButton('Select')
            self.selectSignalMapper.setMapping(newButton, i)
            newButton.clicked.connect(self.selectSignalMapper.map)

            addButton = QtGui.QPushButton('Add')
            self.addSignalMapper.setMapping(addButton, i)
            addButton.clicked.connect(self.addSignalMapper.map)

            self.nameLabels.append(nameLabel)
            self.nameLineEdits.append(nameLineEdit)
            self.newButtons.append(newButton)
            self.addButtons.append(addButton)

            self.grid.addWidget(nameLabel, i+2, 0)
            self.grid.addWidget(nameLineEdit, i+2, 1)
            self.grid.addWidget(newButton, i+2, 2)
            self.grid.addWidget(addButton, i+2, 3)

        ## Connect Signals and Slots 
        self.selectSignalMapper.mapped.connect(self.modify)
        self.addSignalMapper.mapped.connect(self.add)

        self.setLayout(self.grid)

    @QtCore.pyqtProperty(list)
    def matches(self):
        return self._matches

    def setMatch(self, index, new_match):
        name = self.matches[index][0]
        self.nameLineEdits[index].setText(new_match)
        self._matches[index] = (name, new_match)
        self.matches_changed.emit(index)

    def modify(self, index):

        ## Select new match using dialog
        new_match, ok = ChangeMatchDialog.getMatch(self.nameLabels[index].text(),
                                                 self.database_names)

        ## Check if valid and update
        if ok:
            self.setMatch(index, new_match)

    def add(self, index):

        ## Add new match using dialog
        new_match, ok = AddTeamDialog.addTeam(self.nameLabels[index].text())

        ## Check if valid and update
        if ok:
            self.setMatch(index, new_match)

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
        self.registerField('date*', self.dateEdit, 'date',
                           QtGui.QDateEdit.dateChanged)
        self.registerField('gender*', self.genderComboBox)
        self.registerField('distance*', self.distanceComboBox)
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
                
                
                team_matches.append((team_name, team_match[0].name))
        

        ## Create a MultiMatchDisplay
        self.teammatchesDisplay = MultiMatchDisplay(team_matches,
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

        team_matches = self.field('team_matches').toPyObject()

#        ## Construct team dictionary
#        for team_name, database_match in team_matches:
#            team_dict[team_name] = database_match

#            with ndb.db_session(DATABASE) as session:
#                try:
#                    ndb.Team.from_db(names=database_match)
#                except QueryError:
#                    print database_match
                    
                    
        
#        Construct 

################################################################################
##
## Modify Page
##
################################################################################

class ModifyPage(QtGui.QWizardPage):
    pass

################################################################################
##
## Confirmation Page
##
################################################################################

class ConfirmationPage(QtGui.QWizardPage):
    pass

################################################################################
##
## Conclusion Page
##
################################################################################

class ConclusionPage(QtGui.QWizardPage):
    pass

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

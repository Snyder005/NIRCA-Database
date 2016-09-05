#!/usr/bin/env python

import sys
import NIRCAdb as ndb
from PyQt4 import QtCore, QtGui


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
## Intro Page
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
        self.setLayout(grid)

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

        ## Check if non-empty and update
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
        self.container = QtGui.QWidget()
        self.scroll = QtGui.QScrollArea()
        self.scroll.setWidgetResizable(False)

        ## Create QWidget objects
        self.nameLabel = QtGui.QLabel('Names: ')
        self.matchLabel = QtGui.QLabel('Matched Name: ')
        self.confirmCheckBox = QtGui.QCheckBox('Confirm')

        ## Create Layout
        self.grid = QtGui.QGridLayout()
        self.grid.setSpacing(20)
        self.grid.addWidget(self.nameLabel, 1, 0)
        self.grid.addWidget(self.matchLabel, 1, 1)

        ## Register fields
        self.registerField('team_confirm*', self.confirmCheckBox)

    def initializePage(self):

        ## Read result CSV file
        filename = self.field('filename')
        team_names = set()
        
        with open(filename, 'r') as f:
            data = f.readlines()
            for row in data:
                cols = str.split(row, ',')
                team_names.add(cols[1])
            team_names = list(team_names)

        ## Query database for list of teams
        with ndb.db_session(DATABASE) as session:
            database_teams = Team.from_db(session)

            team_matches = []
            for team_name in team_names:

                team_match = ndb.search.team_search(team_name, limit=1,
                                                    team_list=database_teams)[0]
                
                
                team_matches.append((team_name, team_match.name))

        ## Set-up match displays
        signalMapper = QtGui.QSignalMapper(self)
        self.matchDisplays = []

        for i, team_match in enumerate(team_matches):

            nameDisplay = QtGui.QLabel(team_match[0])
            matchDisplay = QtGui.LineEdit(team_match[1])
            matchDisplay.setReadOnly(True)
            
            newteamButton = QtGui.QPushButton('Select New Team')
            signalMapper.setMapping(newteamButton, i)
            newteamButton.clicked.connect(signalMapper.map)

            self.matchDisplays.append(matchDisplay)
            
            self.grid.addWidget(nameDisplay, i+2, 0)
            self.grid.addWidget(matchDisplay, i+2, 1)
            self.grid.addWidget(newteamButton, i+2, 2)

        signalMapper.mapped.connect(self.modify)
        self.grid.addWidget(self.confirmCheckBox, len(team_matches)+3, 0)

        ## Finalize scroll area
        self.container.setLayout(self.grid)
        self.scroll.setWidget(self.container)
        vLayout = QtGui.QVBoxLayout(self)
        vLayout.addWidget(self.scroll)
        self.setLayout(vLayout)

    def modify(self, index):
        pass
            


################################################################################
##
## Runner Match Page
##
################################################################################

class RunnerMatchPage(QtGui.QWizardPage):
    pass

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

def main():

    app = QtGui.QApplication(sys.argv)
    wiz = UpdateWizard()
    wiz.show()
    sys.exit(app.exec_())

if __name__ == '__main__':

    main()

#!/usr/bin/env python

"""Wizard for adding race results to the database.

This python script provides a stand-alone program that guides the user 
through the process of adding results from a CSV file to the SQL database.
It performs fuzzy string matching to identify teams and individuals already
present in the database, as well as allows for dynamic insertion of new 
teams and individuals.  Once proper runner identification has been performed,
the user will be able to adjust the base rating for the race in the GUI, or
export to a CSV file for external analysis.  

"""

import sys
import argparse

from NIRCAdb import gui as ndbgui
from PyQt4.QtGui import QApplication

################################################################################
##
## Main Function
##
################################################################################

def main(database):

    database_ref = 'sqlite:///{0}'.format(database)

    app = QApplication(sys.argv)
    wiz = ndbgui.UpdateWizard(database_ref)
    wiz.show()
    sys.exit(app.exec_())

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--database', help='database to modify.',
                        default='test.db')

    args = parser.parse_args()
    database = args.database

    main(database)

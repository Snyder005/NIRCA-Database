import sys
import argparse

from NIRCAdb import gui as ndbgui
from PyQt4.QtGui import QApplication


################################################################################
##
## Predictor Wizard
##
################################################################################

def main(database):

    database_ref = 'sqlite:///{0}'.format(database)

    app = QApplication(sys.argv)
    wiz = ndbgui.PredictorWizard(database_ref)
    wiz.show()
    sys.exit(app.exec_())

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--database', help='database to modify.',
                        default='test.db')

    args = parser.parse_args()
    database = args.database

    main(database)

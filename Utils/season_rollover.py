import argparse
import NIRCAdb as ndb
from sqlalchemy import exc
import shutil
import os

################################################################################
##
## Example 1: Print List of Teams from a Specific Region
##
################################################################################

def main(database):

    ## First back-up database    
    shutil.copy2(database,
                 "{0}_backup.db".format(os.path.splitext(database)[0]))

    ## Open database
    with ndb.db_session('sqlite:///{0}'.format(database)) as f:

        try:

            ## Delete all results
            num_deleted = f.query(ndb.Result).delete()
            print "Results Deleted: {0}".format(num_deleted)

            ## Set all runners to inactive
            f.query(ndb.Runner).update({ndb.Runner.status: 0})
            print "All Runner statuses reset."

        except exc.SQLAlchemyError as e:
            print e
            return False

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('database', help='database to modify.')

    args = parser.parse_args()
    database = args.database

    main(database)
                

            

        

        

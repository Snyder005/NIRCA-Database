#!/usr/bin/env python

import NIRCAdb as ndb
from sqlalchemy import exc
import argparse

def main(database, resultfile):

    with ndb.db_session('sqlite:///{0}'.format(database)) as f:

        try:
            new_race = ndb.Race.from_csv(resultfile)
            new_race.process(f)
        except exc.SQLAlchemyError as e:
            print e
            return False

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('file', help='result file to add.')
    parser.add_argument('-d', '--database', help='database to modify.',
                        default = 'XC_2016.db')

    args = parser.parse_args()
    file = args.file
    database = args.database

    main(database, file)
    

    
    

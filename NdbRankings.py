from NIRCAdb import sim as ndbsim
import NIRCAdb as ndb
import sys

def main(gender):

    if gender not in ['M', 'W']:
        return

    with ndb.db_session('sqlite:///test.db') as session:

        all_teams = ndb.Team.from_db(session)

        sim = ndbsim.Sim(all_teams, gender)

        sim.predict()

if __name__ == '__main__':

    main(sys.argv[1])

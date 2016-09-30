from NIRCAdb import sim as ndbsim
import NIRCAdb as ndb

def main():

    with ndb.db_session('sqlite:///test.db') as session:

        all_teams = ndb.Team.from_db(session)

        sim = ndbsim.Sim(all_teams, 'W')

        sim.predict()

if __name__ == '__main__':

    main()

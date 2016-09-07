"""NIRCAdb Package Version 7.0rc2 source code.

This contains the source code for what will be NIRCAdb Version 7.0.  It is
currently under construction.  Once completed this will serve as base python
package. Additionally a GUI will be created using the code developed in this
package. Version 6.1 is a stand alone GUI and is functional, though it can be 
unstable and is out-of-date. 

Features:
    Version 6.1 has the following features:

    * Single Runner Querying: Query the database, using a GUI, by runner names. 

    * Multiple Runner Querying: Query the database, using a GUI, filtering by
          team names, runner status, and runner gender. GUI interface allows 
          sorting by runner name, team names, runner gender, runner Speed 
          Rating, and runner status.

    * Team Ranking: Rank multiple teams using the runners' Speed Ratings.

    * Race Simulation: Basic support for simulating races between teams and 
          displaying average results

    * Result Formatting: Format a list of results from a single race to be
          processed by hand.

    * Upload Processed Results: Upload processed results and update the
          database

New Features:  
    In addition to the above features, Version 7.0 will include the following,
    some of which will supercede features in Version 6.1.

    * Region Filter: NIRCA region will be added as a filter for multiple runner
          queries, and simulated races.

    * Roll-over Database: Add functionality to update database for the next 
          season, i.e., remove inactive runners and remove all results

    * Improved Result Formatting: Improvements to the runner/result matching to
          improve result formatting.

    * MCMC Result Processing: Processing of results automatically using MCMC
          techniques.

    * Integrated Results Uploading: Streamline and integrate result formatting,
          processing, and final upload.

Todo:

    * Add raises for exceptions for failed database queries

    * QOL changes for printing runners, results and teams

    * Build GUI for Query. (5.0)

    * Program and implement MCMC result processing. (3.0)
 
    * Fix result formatting, processing and uploading issues. (4.0)

    * Add Result Uploading features to GUI (6.0)

.. NIRCAdb 7.0rc2
   http://github.com/Snyder005/NIRCAdb

"""

from database import Runner
from database import Team
from database import Result
from database import Race
from database import REGIONS
from database import db_session

__version__ = "7.0rc2"


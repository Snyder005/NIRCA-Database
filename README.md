# NIRCAdb

This repository contains both the older, stand-alone version of the NIRCA database GUI and its corresponding sqlite database, XC_2015.db, as well as the development build for the next NIRCA database version.

The aim of the next version, 7.0, will be to be a python package containing all the necessary code for users to create their own personal databases, and run their own race simulations.  The release will also include a standalone GUI, to allow basic simulation and query functionality.

## Use

The primary use of Version 6.1 was to match results from a race to runners in a database, so that I could generate Speed Ratings for the race and then easily upload them and update the database.  This would allow me to quickly generate future race predictions and limited simulated races.

As a benefit of this, I added database specific query options to the GUI program, which proved beneficial.  Due to ease of implementation, these features are far more stable than the result formatting.

The GUI can be used for various Query functions, to rank teams, and to run limited race simulations.  The included database is the final database for the NIRCA XC 2015 season. The test database is simply a copy of this.

## Dependencies

The following non-standard packages are used. While older versions may work, depending on the specific features used, I make no guarantees.

1. NumPy Version 1.10 or higher. NumPy functionality is limited to basic array manipulations.

2. SciPy Version 0.17.0 or higher. SciPy is used for drawing from statistical distributions, most specifically a Maxwell and a Normal distribution.

3. SQLAlchemy Version 1.0.9 or higher. This is the heart and soul of the code, providing the python implementation for database interaction

4. PyQt4. This will be used to build the GUI.

* The following are required to run the NIRCAdb_6.1.py

5. PySide Version 1.1.2. This is used to build the GUI for Version 6.1.  Will be replaced by PyQt4 in Version 7.0

6. Jellyfish Version 0.5.6 or higher. Used for fuzzy string matching of runners to results, when formatting results for the database.

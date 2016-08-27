# NIRCAdb

This repository contains both the older, stand-alone version of the NIRCA database GUI and its corresponding sqlite database, XC_2015.db, as well as the development build for the next NIRCA database version.

The aim of the next version, 7.0, will be to be a python package containing all the necessary code for users to create their own personal databases, and run their own race simulations.  The release will also include a standalone GUI, to allow basic simulation and query functionality.

## Use

NIRCAdb_6.1.py is a GUI that interfaces with the SQLite database 'XC_2015.db'. The 'Select by Team, Gender, Status' page offers a variety of built in Query features, and displays results in a spreadsheet which supports sorting.  Results of the query can be exported as a CSV file (may be broken at this time).  The 'Run Simulations' page has 2 main features.

1. 'Score' : Score the selected teams according to their Speed Ratings in the database. Team results and individual results are displayed to screen and can be saved.  This is used to develop rankings.

2. 'Simulation' : Simulate races between the selected teams by generating Speed Ratings from a probability distribution and display the average of the results.  Same format output as the 'Score' feature.  This is just a novelty at the moment, as I never found the time to expand on the simulation results (team score distributions, etc.).  It can also run slowly if you use all the teams.  Additionally, I am just using a probability distribution that I made up.  This feature will be improved the most with the next version.

The final two features can be found in the Edit menu; 'Format Results' and 'Add Results'.  I use these when processing new race results and updating the database.  They are no use to regular users, and can crash the program or mess up the database if used improperly.  

1. 'Format Results' : Used to match race results to runners in the database. Input is a CSV file of a race. The program performs a fuzzy string match for each runner's name and attempts to locate them in the database.  The results of this are displayed for the user to confirm.  In addition, if no match is found, the user will have to either manually match them or add them. Once confirmed, a properly formatted CSV file with each runner's database ID is added to their result.

2. 'Add Results' : Upload processed results to the database. This reads a CSV file of a processed race, identifies each runner from the database ID appended by the 'Format Results' function, and updates the database with their result.

The program requires a few dependencies, and if one just wants to browse the database, a good SQL viewer works.

## Speed Ratings

Besides just storing results for runners in the database, I also store a "Speed Rating".  This is the method which I use to rank runners based off of Cross-Country results.  The secret process of Speed Rating generation is done by me between the 'Format Results' step and the 'Add Results' step.  The original Speed Ratings were developed in NY by Bill Meylan, an avid follower of cross country.  I developed my own modified version for extension to collegiate race distances. Explanation is kind of lengthy ([a brief overview can be found here](http://www.tullyrunners.com/Data/Articles/refrunner.htm)) but suffice to say it is about 50% science, 50% art.  When looking at the Speed Ratings one only needs to know that a difference of 1 corresponds to a difference of 5 (3.75) seconds in a race for men (women), and the higher the rating, the better.

## Dependencies

The following non-standard packages are used. While older versions may work, depending on the specific features used, I make no guarantees.

1. NumPy Version 1.10 or higher. NumPy functionality is limited to basic array manipulations.

2. SciPy Version 0.17.0 or higher. SciPy is used for drawing from statistical distributions, most specifically a Maxwell and a Normal distribution.

3. SQLAlchemy Version 1.0.9 or higher. This is the heart and soul of the code, providing the python implementation for database interaction

4. PyQt4. This will be used to build the GUI.

The following are required to run the NIRCAdb_6.1.py

5. PySide Version 1.1.2. This is used to build the GUI for Version 6.1.  Will be replaced by PyQt4 in Version 7.0

6. Jellyfish Version 0.5.6 or higher. Used for fuzzy string matching of runners to results, when formatting results for the database.

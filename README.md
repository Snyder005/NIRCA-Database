# NIRCAdb

This repository contains both the older, stand-alone version of the NIRCA database GUI and its corresponding sqlite database, XC_2015.db, as well as the development build for the next NIRCA database version.

The aim of the next version, 7.0, will be to be a python package containing all the necessary code for users to create their own personal databases, and run their own race simulations.  The release will also include a standalone GUI, to allow basic simulation and query functionality.

## Dependencies

The following non-standard packages are used. While older versions may work, depending on the specific features used, I make no guarantees.

1. NumPy Version 1.10 or higher. NumPy functionality is limited to basic array manipulations.

2. SciPy Version 0.17.0 or higher. SciPy is used for drawing from statistical distributions, most specifically a Maxwell and a Normal distribution.

3. SQLAlchemy Version 1.0.9 or higher. This is the heart and soul of the code, providing the python implementation for database interaction.

4. PyQt4. This will be used to build the GUI.

5. fuzzywuzzy Version 0.11.1 or higher. The fuzzywuzzy package is used to do string matching for database searches.

## Speed Ratings

Besides just storing results for runners in the database, I also store a "Speed Rating".  This is the method which I use to rank runners based off of Cross-Country results.  The secret process of Speed Rating generation is done by me between the 'Format Results' step and the 'Add Results' step.  The original Speed Ratings were developed in NY by Bill Meylan, an avid follower of cross country.  I developed my own modified version for extension to collegiate race distances. Explanation is kind of lengthy ([a brief overview can be found here](http://www.tullyrunners.com/Data/Articles/refrunner.htm)) but suffice to say it is about 50% science, 50% art.  When looking at the Speed Ratings one only needs to know that a difference of 1 corresponds to a difference of 5 (3.75) seconds in a race for men (women), and the higher the rating, the better.

## Examples

Examples are provided in the Examples subdirectory.  In order to run these properly from any location, you will need to add the directory containing the NIRCAdb package subdirectory to your python path.  Optionally you could modify the code themselves to do a relative import, or add the correct path to your system path using the sys Python package.

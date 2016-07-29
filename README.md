# NIRCAdb

This repository contains both the older, stand-alone version of the NIRCA database GUI and its corresponding sqlite database, XC_2015.db, as well as the development build for the next NIRCA database version.

The aim of the next version, 7.0, will be to be a python package containing all the necessary code for users to create their own personal databases, and run their own race simulations.  The release will also include a standalone GUI, to allow basic simulation and query functionality.

## Dependencies

The following non-standard packages are used. While older versions may work, depending on the specific features used, I make no guarantees.

1. NumPy Version 1.10 or higher. NumPy functionality is limited to basic array manipulations.

2. SciPy Version 0.17.0 or higher. SciPy is used for drawing from statistical distributions, most specifically a Maxwell and a Normal distribution.

3. SQLAlchemy Version 1.0.9 or higher. This is the heart and soul of the code, providing the python implementation for database interaction

4. PyQt4. This will be used to build the GUI.

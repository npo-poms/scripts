poms-scripts
============

Scripts to talk to POMS Rest API.

These scripts are in python. But we may add scripts in groovy or other scripting languages as well.

Python
------
For python we maintain a 'poms.py' which is imported in the other python scripts. It provides a simple shelve-database with settings you use, and maps the rest-calls which are used in the scripts.

Groovy/Java
-----------
Since POMS is written in Java, it is actually feasible to use its domain objects in your scripts. A rest client in java is available and is in use at VPRO.

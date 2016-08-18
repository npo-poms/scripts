Python scripts
============

This directory collects various python scripts to talk with the POMS backend api.

Most of them use a collection of utilities collected in 'poms.py', but we moved some of those also to a nicer object oriented structure in https://github.com/npo-poms/pyapi.

poms.py
-------
Most functionality is in 'poms.py' which is imported in the other scripts. It also takes care of command line parsing and a database of credentials. The simplest example is 'post.sh', which simply posts an existing file.

MediaBackend.py
---------------
cleanupGroup.py  is an example of script using the MediaBackend client object in pyapi.


addGenre
========

A script to add genre to all members of a certain POMS-group. Available genre id  can be obtained from 
http://poms.omroep.nl/schema/classification

Usage:
```bash
michiel@baleno:~/github/npo-poms/scripts/python$ ./addGenre.py 
./addGenre.py [-r] [-h] [-s] [-t <target>] <MID> <genreId>
-s       Show stored credentials (in creds.db). If none stored, username/password will be asked interactively.
-t <url> Change target. 'test', 'dev' and 'prod' are possible abbreviations for https://api[-test|-dev].poms.omroep.nl/media/. Defaults to previously used version (stored in creds.db)
-r       Reset and ask username/password again
-e <email> Set email address to mail errors to. Defaults to previously used value (stored in creds.db).
```
Example:
```bash
michiel@baleno:~/github/npo-poms/scripts/python$ ./addGenre.py -t test WO_S_VPRO_425270  3.0.1.1
Setting target to https://api-test.poms.omroep.nl/
Username for https://api-test.poms.omroep.nl/: vpro-mediatools
Password: 
Username/password stored in file creds.db. Use -r to set it.
loading members of WO_S_VPRO_425270
13/13
Adding genre 3.0.1.1 to WO_VPRO_430114
posting WO_VPRO_430114 to https://api-test.poms.omroep.nl/media/media?lookupcrid=False
Adding genre 3.0.1.1 to WO_VPRO_430120
posting WO_VPRO_430120 to https://api-test.poms.omroep.nl/media/media?lookupcrid=False
Adding genre 3.0.1.1 to WO_VPRO_430117
posting WO_VPRO_430117 to https://api-test.poms.omroep.nl/media/media?lookupcrid=False
Adding genre 3.0.1.1 to POMS_VPRO_429671
posting POMS_VPRO_429671 to https://api-test.poms.omroep.nl/media/media?lookupcrid=False
Adding genre 3.0.1.1 to POMS_VPRO_430299
posting POMS_VPRO_430299 to https://api-test.poms.omroep.nl/media/media?lookupcrid=False
Adding genre 3.0.1.1 to WO_VPRO_430118
posting WO_VPRO_430118 to https://api-test.poms.omroep.nl/media/media?lookupcrid=False
Adding genre 3.0.1.1 to WO_VPRO_430116
posting WO_VPRO_430116 to https://api-test.poms.omroep.nl/media/media?lookupcrid=False
Adding genre 3.0.1.1 to POMS_VPRO_429678
posting POMS_VPRO_429678 to https://api-test.poms.omroep.nl/media/media?lookupcrid=False
Adding genre 3.0.1.1 to WO_VPRO_430121
posting WO_VPRO_430121 to https://api-test.poms.omroep.nl/media/media?lookupcrid=False
Adding genre 3.0.1.1 to WO_VPRO_430112
posting WO_VPRO_430112 to https://api-test.poms.omroep.nl/media/media?lookupcrid=False
Adding genre 3.0.1.1 to WO_VPRO_430119
posting WO_VPRO_430119 to https://api-test.poms.omroep.nl/media/media?lookupcrid=False
Adding genre 3.0.1.1 to WO_VPRO_430115
posting WO_VPRO_430115 to https://api-test.poms.omroep.nl/media/media?lookupcrid=False
Adding genre 3.0.1.1 to WO_VPRO_430113
posting WO_VPRO_430113 to https://api-test.poms.omroep.nl/media/media?lookupcrid=False
```

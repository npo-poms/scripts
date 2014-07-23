poms-scripts
============

Scripts to talk to POMS Rest API.

These scripts are in python. But we may add scripts in groovy or other scripting languages as well.

Python
------
For python we maintain a 'poms.py' which is imported in the other python scripts. It provides a simple shelve-database with settings you use, and maps the rest-calls which are used in the scripts.
```Shell
michiel@baleno:~/github/npo-poms/scripts/python$ ./post.py -r -t dev  ../examples/program.xml 
Username for https://api-dev.poms.omroep.nl/media/: vpro-mediatools
Password: 
Username/password stored in file creds.db. Use -r to set it.
posting  to https://api-dev.poms.omroep.nl/media/media?errors=michiel.meeuwissen@gmail.com
crid://bds.tv/9876,crid://tmp.fragment.mmbase.vpro.nl/1234
michiel@baleno:~/github/npo-poms/scripts/python$ 
```

Groovy/Java
-----------
Since POMS is written in Java, it is actually feasible to use its domain objects in your scripts. A rest client in java is available and is in use at VPRO. At request we can make this client available as well.
```java
MediaRestClient client = new MediaRestClient();
client.setUrl(mediaRsUrl);
client.setUserName(userName);
client.setPassword(password);
client.setErrors(getMail());
..
GroupUpdate group = client.getGroup(id);
..

group.setPublishStart(onlineDate);

client.set(group);

```

Bash
----
Simply calling 'curl' in shell script is of course possible too sometimes.

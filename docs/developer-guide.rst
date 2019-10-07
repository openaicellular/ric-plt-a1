.. ==================================================================================
..       Copyright (c) 2019 Nokia
..       Copyright (c) 2018-2019 AT&T Intellectual Property.
..
..   Licensed under the Apache License, Version 2.0 (the "License");
..   you may not use this file except in compliance with the License.
..   You may obtain a copy of the License at
..
..          http://www.apache.org/licenses/LICENSE-2.0
..
..   Unless required by applicable law or agreed to in writing, software
..   distributed under the License is distributed on an "AS IS" BASIS,
..   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
..   See the License for the specific language governing permissions and
..   limitations under the License.
.. ==================================================================================

A1 Dev Guide
============

Tech Stack
==========

-  OpenAPI3
-  Connexion
-  Flask with Gevent serving
-  Python3.7

Version bumping
===============

This project follows semver. When changes are made, the versions are in:

1) ``docs/release-notes.rst``

2) ``setup.py``

3) ``container-tag.yaml``

4) ``integration_tests/a1mediator/Chart.yaml``

6) ``a1/openapi.yaml`` (this is an API version, not a software version; no need to bump on patch changes)

7) in the it/dep repo that contains a1 helm chart, ``values.yaml``, ``Chart.yml``

Version bumping rmr-python
==========================
rmr-python is a critial dependency of A1. Bumping the rmr version dependency requires changes in:

1) ``setup.py``

2) ``Dockerfile``

3) ``integration_tests/Dockerfile``

Run the integration tests after attempting this.

Unit Testing
============
Note,  before this will work, for the first time on the machine running the tests, run ``./install_deps.sh``. This is only needed once on the machine.
Also, this requires the python packages ``tox`` and ``pytest``.

::

   tox
   open htmlcov/index.html

Alternatively, you can run the unit tests in Docker (this is somewhat less nice because you don't get the pretty HTML)

::

   docker build  --no-cache -t a1test:latest -f Dockerfile-Unit-Test

Integration testing
===================
This tests A1’s external API with two test receivers. This depends on helm+k8s, meaning you cannot run this if this is not installed.

Unlike the unit tests, however, this does not require rmr to be installed on the base system, as everything
runs in Docker, and the Dockerfiles provide/install rmr.

First, build the latest A1 you are testing (from the root):
::

    docker build  --no-cache -t a1:latest .

Note that this step also runs the unit tests, since running the unit tests are part of the Dockerfile for A1.

If you've never run the integration tests before, build the test receiver, which is referenced in the helm chart:
::

    cd integration_tests
    docker build  --no-cache -t testreceiver:latest .

Finally, run all the tests from the root (this requires the python packages ``tox``, ``pytest``, and ``tavern``).
::

   tox -c tox-integration.ini

This script:
1. Deploys 3 helm charts into a local kubernetes installation
2. Port forwards a pod ClusterIP to localhost
3. Uses “tavern” to run some tests against the server
4. Barrages the server with apache bench
5. Tears everything down

Unless you're a core A1 developer, you should probably stop here. The below instructions
are for running A1 locally, without docker, and is much more involved (however useful when developing a1).

Running locally
===============

1. Before this will work, for the first time on that machine, run ``./install_deps.sh``

2. It also requires rmr-python installed. (The dockerfile does this)

3. Create a ``local.rt`` file and copy it into ``/opt/route/local.rt``.
   Note, the example one in ``integration_tests`` will need to be modified for
   your scenario and machine.

4. Copy a ric manifest into ``/opt/ricmanifest.json`` and an rmr mapping
   table into ``/opt/rmr_string_int_mapping.txt``. You can use the test
   ones packaged if you want:

   ::

     cp tests/fixtures/ricmanifest.json /opt/ricmanifest.json
     cp tests/fixtures/rmr_string_int_mapping.txt /opt/rmr_string_int_mapping.txt

5. Then:

   ::

   sudo pip install -e .
   set -x LD_LIBRARY_PATH /usr/local/lib/; set -x RMR_SEED_RT /opt/route/local.rt ; set -x RMR_RCV_RETRY_INTERVAL 500; set -x RMR_RETRY_TIMES 10;
   /usr/bin/run.py


There are also two test receivers in ``integration_tests`` you can run locally.
The first is meant to be used with the ``control_admission`` policy
(that comes in test fixture ric manifest):

::

   set -x LD_LIBRARY_PATH /usr/local/lib/; set -x RMR_SEED_RT /opt/route/local.rt ; python receiver.py

The second can be used against the ``test_policy`` policy to test the
async nature of A1, and to test race conditions. You can start it with
several env variables as follows:

::

   set -x LD_LIBRARY_PATH /usr/local/lib/; set -x RMR_SEED_RT /opt/route/local.rt ; set -x TEST_RCV_PORT 4563; set -x TEST_RCV_RETURN_MINT 10001; set -x TEST_RCV_SEC_DELAY 5; set -x TEST_RCV_RETURN_PAYLOAD '{"ACK_FROM": "DELAYED_TEST", "status": "SUCCESS"}' ; python receiver.py

To test the async nature of A1, trigger a call to ``test_policy``, which
will target the delayed receicer, then immediately call
``control_admission``. The ``control_admission`` policy return should be
returned immediately, whereas the ``test_policy`` should return after
about ``TEST_RCV_SEC_DELAY 5``. The ``test_policy`` should not block A1
while it is sleeping, and both responses should be correct.

::

   curl -v -X PUT -H "Content-Type: application/json" -d '{}' localhost:10000/ric/policies/test_policy
   curl -v -X PUT -H "Content-Type: application/json" -d '{ "enforce":true, "window_length":10, "blocking_rate":20, "trigger_threshold":10 }' localhost:10000/ric/policies/admission_control_policy
   curl -v localhost:10000/ric/policies/admission_control_policy
   curl -v localhost:10000/a1-p/healthcheck

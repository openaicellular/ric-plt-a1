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

4) ``integration_tests/a1mediator/values.yaml + ``Chart.yaml``

6) ``a1/openapi.yml``

7) in the it/dep repo that contains a1 helm chart, ``values.yaml``, ``Chart.yml``

Running locally
===============

1. This requires that RMR is installed on the base system. (the
   Dockerfile does this when running in Docker)

2. It also requires rmr-python >= 0.10.1 installed. (The dockerfile also
   does this)

3. Create a ``local.rt`` file and copy it into ``/opt/route/local.rt``.
   Note, the example one in ``local_tests`` will need to be modified for
   your scenario and machine.

4. Copy a ric manifest into ``/opt/ricmanifest.json`` and an rmr mapping
   table into ``/opt/rmr_string_int_mapping.txt``. You can use the test
   ones packaged if you want:

   ::

     cp tests/fixtures/ricmanifest.json /opt/ricmanifest.json cp
     tests/fixtures/rmr_string_int_mapping.txt
     /opt/rmr_string_int_mapping.txt

5. Then:

   sudo pip install –ignore-installed .; set -x LD_LIBRARY_PATH
   /usr/local/lib/; set -x RMR_SEED_RT /opt/route/local.rt ; set -x
   RMR_RCV_RETRY_INTERVAL 500; set -x RMR_RETRY_TIMES 10;
   /usr/bin/run.py

Testing locally
===============

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
   curl -v -X PUT -H "Content-Type: application/json" -d '{"dc_admission_start_time": "10:00:00", "dc_admission_end_time": "11:00:00"}' localhost:10000/ric/policies/control_admission_time

Finally, there is a test “bombarder” that will flood A1 with messages
with good message types but bad transaction IDs, to test A1’s resilience
against queue-overflow attacks

::

   set -x LD_LIBRARY_PATH /usr/local/lib/; set -x RMR_SEED_RT /opt/route/local.rt ;  python bombard.py

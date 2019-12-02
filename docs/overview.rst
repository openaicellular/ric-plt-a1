.. This work is licensed under a Creative Commons Attribution 4.0 International License.
.. SPDX-License-Identifier: CC-BY-4.0

A1 Mediator
===========

Code
----
https://gerrit.o-ran-sc.org/r/admin/repos/ric-plt/a1

API
---

You can see the API (OpenAPI3 spec) at ``a1/openapi.yml``. You can also
see the “pretty” version if you run the container at
``http://localhost:10000/ui/``.

Policy Overview
----------------
There are two "object types" associated with policy: policy types and policy instances.

Policy types define the name, description, and most importantly the schema of all instances of that type. Think of policy types as defining a JSON schema for the messages sent from A1 to xapps.

Xapps do not receive policy types from A1; types are used only by A1 to validate instance creation requests. However, xapps must register to receive instances of type ids in their xapp descriptor.

Xapp developers can also create new policy types, though the exact process of where these are stored is still TBD. For practical purposes, when the RIC is running, A1s API needs to be invoked to load the policy types before instances can be created.

Policy instances are concrete instantiations of a policy type. They give concrete values of a policy. There may be many instances of a single type. Whenever a policy instance is created in A1, messages are sent over RMR to all xapps registered for that policy type; see below.

Xapps can "sign up" for multiple policy types using their xapp descriptor.

Xapps are expected to handle multiple simultaneous instances of each type that they are registered for.

Xapps supporting A1


Integrating Xapps with A1
-------------------------

A1 to Xapps
~~~~~~~~~~~
When A1 sends a message to xapps, the schema for messages from A1 to the xapp is defined by ``downstream_message_schema`` in ``docs/a1_xapp_contract_openapi.yaml``

All policy instance requests get sent from A1 using message type 20010

Xapps to A1
~~~~~~~~~~~
There are three scenarios in which Xapps are to send a message to A1:

1. When an xapp receives a CREATE or UPDATE message for a policy instance. Xapps must respond to these requests by sending a message of type 20011 to A1. The schema for that message is defined by ``downstream_notification_schema`` in ``docs/a1_xapp_contract_openapi.yaml``
2. Since policy instances can "deprecate" other instances, there are times when xapps need to asyncronously tell A1 that a policy is no longer active. Same message type and schema. The only difference between case 1 and 2 is that case 1 is a "reply" and case 2 is "unsolicited".
3. Xapps can request A1 to re-send all instances of a type using a query, message 20012. When A1 receives this (TBD HERE, STILL BE WORKED OUT)

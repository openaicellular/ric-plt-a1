# ==================================================================================
#       Copyright (c) 2019-2020 Nokia
#       Copyright (c) 2018-2020 AT&T Intellectual Property.
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#          http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
# ==================================================================================
import msgpack
from ricsdl.exceptions import RejectedByBackend, NotConnected, BackendError


class MockSDLWrapper:
    """
    Mock wrapper for SDL that uses a dict so we do not rely on Redis for unit tests.
    Would be really nice if SDL itself came with a "standalone: dictionary" mode for this purpose...
    """

    def __init__(self):
        self.POLICY_DATA = {}

    def set(self, key, value):
        """set a key"""

        # these are for unit testing that the handler works on various SDL errors
        if key == "a1.policy_type.111":
            raise RejectedByBackend()
        if key == "a1.policy_type.112":
            raise NotConnected()
        if key == "a1.policy_type.113":
            raise BackendError()

        self.POLICY_DATA[key] = msgpack.packb(value, use_bin_type=True)

    def get(self, key):
        """get a key"""
        if key in self.POLICY_DATA:
            return msgpack.unpackb(self.POLICY_DATA[key], raw=False)
        return None

    def find_and_get(self, prefix):
        """get all k v pairs that start with prefix"""
        return {k: msgpack.unpackb(v, raw=False) for k, v in self.POLICY_DATA.items() if k.startswith(prefix)}

    def delete(self, key):
        """ delete a key"""
        del self.POLICY_DATA[key]

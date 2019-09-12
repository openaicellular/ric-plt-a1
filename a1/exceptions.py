# ==================================================================================
#       Copyright (c) 2019 Nokia
#       Copyright (c) 2018-2019 AT&T Intellectual Property.
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
"""
Custom Exceptions
"""


class PolicyInstanceNotFound(BaseException):
    """a policy instance cannot be found"""


class PolicyTypeNotFound(BaseException):
    """a policy type instance cannot be found"""


class MissingRmrString(BaseException):
    pass


class MissingManifest(BaseException):
    pass


class MissingRmrMapping(BaseException):
    pass

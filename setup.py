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
from setuptools import setup, find_packages

setup(
    name="a1",
    version="1.0.0",
    packages=find_packages(exclude=["tests.*", "tests"]),
    author="Tommy Carpenter",
    description="RIC A1 Mediator for policy/intent changes",
    url="https://gerrit.o-ran-sc.org/r/admin/repos/ric-plt/a1",
    entry_points={"console_scripts": ["run.py=a1.run:main"]},
    # we require jsonschema, should be in that list, but connexion already requires a specific version of it
    install_requires=["requests", "Flask", "connexion[swagger-ui]", "gevent", "rmr>=0.13.2"],
    package_data={"a1": ["openapi.yaml"]},
)

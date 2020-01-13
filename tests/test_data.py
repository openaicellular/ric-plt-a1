"""
tests data functions
"""
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
from a1 import data
from ricsdl.syncstorage import SyncStorage


def setup_module():
    """module level setup"""
    data.SDL.sdl = SyncStorage(fake_db_backend="dict")


def test_sdl_raw():
    """
    test raw sdl functions
    """
    data.SDL.set("as.df1", "data")
    data.SDL.set("as.df2", "data2")
    assert data.SDL.get("as.df1") == "data"
    assert data.SDL.get("as.df2") == "data2"
    assert data.SDL.find_and_get("as.df1") == {"as.df1": "data"}
    assert data.SDL.find_and_get("as.df2") == {"as.df2": "data2"}
    assert data.SDL.find_and_get("as.df") == {"as.df1": "data", "as.df2": "data2"}
    assert data.SDL.find_and_get("as.d") == {"as.df1": "data", "as.df2": "data2"}
    assert data.SDL.find_and_get("as.") == {"as.df1": "data", "as.df2": "data2"}
    assert data.SDL.find_and_get("asd") == {}

    # delete 1
    data.SDL.delete("as.df1")
    assert data.SDL.get("as.df1") is None
    assert data.SDL.get("as.df2") == "data2"

    # delete 2
    data.SDL.delete("as.df2")
    assert data.SDL.get("as.df2") is None

    assert data.SDL.find_and_get("as.df") == {}
    assert data.SDL.find_and_get("") == {}

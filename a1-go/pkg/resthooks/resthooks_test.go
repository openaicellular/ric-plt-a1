/*
==================================================================================
  Copyright (c) 2021 Samsung

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.

   This source code is part of the near-RT RIC (RAN Intelligent Controller)
   platform project (RICP).
==================================================================================
*/
package resthooks

import (
	"os"
	"testing"

       "gerrit.o-ran-sc.org/r/ric-plt/a1/pkg/a1"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/mock"
)

var rh *Resthook
var sdlInst *SdlMock

func TestMain(m *testing.M) {
	sdlInst = new(SdlMock)

       sdlInst.On("GetAll", "A1m_ns").Return([]string{"a1.policy_instance.1006001.qos",
               "a1.policy_type.1006001",
               "a1.policy_type.20000",
               "a1.policy_inst_metadata.1006001.qos",
       }, nil)

       a1.Init()
	rh = createResthook(sdlInst)
	code := m.Run()
	os.Exit(code)
}

func TestGetAllPolicyType(t *testing.T) {
	resp := rh.GetAllPolicyType()
	assert.Equal(t, 2, len(resp))
}

type SdlMock struct {
	mock.Mock
}

func (s *SdlMock) GetAll(ns string) ([]string, error) {
       args := s.MethodCalled("GetAll", ns)
       return args.Get(0).([]string), nil
}

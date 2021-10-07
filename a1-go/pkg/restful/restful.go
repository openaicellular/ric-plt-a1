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
package restful

import (
	"fmt"
	"log"
	"os"

	"github.com/go-openapi/loads"
	"github.com/go-openapi/runtime/middleware"
       "gerrit.o-ran-sc.org/r/ric-plt/a1/pkg/restapi"
       "gerrit.o-ran-sc.org/r/ric-plt/a1/pkg/restapi/operations"
       "gerrit.o-ran-sc.org/r/ric-plt/a1/pkg/restapi/operations/a1_mediator"
       "gerrit.o-ran-sc.org/r/ric-plt/a1/pkg/resthooks"
)

func NewRestful() *Restful {
	r := &Restful{
		rh: resthooks.NewResthook(),
	}
	r.api = r.setupHandler()
	return r
}

func (r *Restful) setupHandler() *operations.A1API {
	swaggerSpec, err := loads.Embedded(restapi.SwaggerJSON, restapi.FlatSwaggerJSON)
	if err != nil {
		os.Exit(1)
	}

	api := operations.NewA1API(swaggerSpec)
	api.A1MediatorA1ControllerGetAllPolicyTypesHandler = a1_mediator.A1ControllerGetAllPolicyTypesHandlerFunc(func(param a1_mediator.A1ControllerGetAllPolicyTypesParams) middleware.Responder {
		fmt.Printf("\n---- handler for get all all policy type --- \n")
		return a1_mediator.NewA1ControllerGetAllPolicyTypesOK().WithPayload(r.rh.GetAllPolicyType())
	})
	return api

}

func (r *Restful) Run() {

	server := restapi.NewServer(r.api)
	defer server.Shutdown()
	server.Port = 8080
	server.Host = "0.0.0.0"
	if err := server.Serve(); err != nil {
		log.Fatal(err.Error())
	}
}

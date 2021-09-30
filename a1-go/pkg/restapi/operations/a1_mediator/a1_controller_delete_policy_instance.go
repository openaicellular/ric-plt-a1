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
// Code generated by go-swagger; DO NOT EDIT.

package a1_mediator

// This file was generated by the swagger tool.
// Editing this file might prove futile when you re-run the generate command

import (
	"net/http"

	"github.com/go-openapi/runtime/middleware"
)

// A1ControllerDeletePolicyInstanceHandlerFunc turns a function with the right signature into a a1 controller delete policy instance handler
type A1ControllerDeletePolicyInstanceHandlerFunc func(A1ControllerDeletePolicyInstanceParams) middleware.Responder

// Handle executing the request and returning a response
func (fn A1ControllerDeletePolicyInstanceHandlerFunc) Handle(params A1ControllerDeletePolicyInstanceParams) middleware.Responder {
	return fn(params)
}

// A1ControllerDeletePolicyInstanceHandler interface for that can handle valid a1 controller delete policy instance params
type A1ControllerDeletePolicyInstanceHandler interface {
	Handle(A1ControllerDeletePolicyInstanceParams) middleware.Responder
}

// NewA1ControllerDeletePolicyInstance creates a new http.Handler for the a1 controller delete policy instance operation
func NewA1ControllerDeletePolicyInstance(ctx *middleware.Context, handler A1ControllerDeletePolicyInstanceHandler) *A1ControllerDeletePolicyInstance {
	return &A1ControllerDeletePolicyInstance{Context: ctx, Handler: handler}
}

/*A1ControllerDeletePolicyInstance swagger:route DELETE /a1-p/policytypes/{policy_type_id}/policies/{policy_instance_id} A1 Mediator a1ControllerDeletePolicyInstance

Delete this policy instance


*/
type A1ControllerDeletePolicyInstance struct {
	Context *middleware.Context
	Handler A1ControllerDeletePolicyInstanceHandler
}

func (o *A1ControllerDeletePolicyInstance) ServeHTTP(rw http.ResponseWriter, r *http.Request) {
	route, rCtx, _ := o.Context.RouteInfo(r)
	if rCtx != nil {
		r = rCtx
	}
	var Params = NewA1ControllerDeletePolicyInstanceParams()

	if err := o.Context.BindValidRequest(r, route, &Params); err != nil { // bind params
		o.Context.Respond(rw, r, route.Produces, route, err)
		return
	}

	res := o.Handler.Handle(Params) // actually handle the request

	o.Context.Respond(rw, r, route.Produces, route, res)

}

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
// Editing this file might prove futile when you re-run the swagger generate command

import (
	"net/http"

	"github.com/go-openapi/runtime"

	"subh.com/a1-go/pkg/models"
)

// A1ControllerGetAllInstancesForTypeOKCode is the HTTP code returned for type A1ControllerGetAllInstancesForTypeOK
const A1ControllerGetAllInstancesForTypeOKCode int = 200

/*A1ControllerGetAllInstancesForTypeOK list of all policy instance ids for this policy type id

swagger:response a1ControllerGetAllInstancesForTypeOK
*/
type A1ControllerGetAllInstancesForTypeOK struct {

	/*
	  In: Body
	*/
	Payload []models.PolicyInstanceID `json:"body,omitempty"`
}

// NewA1ControllerGetAllInstancesForTypeOK creates A1ControllerGetAllInstancesForTypeOK with default headers values
func NewA1ControllerGetAllInstancesForTypeOK() *A1ControllerGetAllInstancesForTypeOK {

	return &A1ControllerGetAllInstancesForTypeOK{}
}

// WithPayload adds the payload to the a1 controller get all instances for type o k response
func (o *A1ControllerGetAllInstancesForTypeOK) WithPayload(payload []models.PolicyInstanceID) *A1ControllerGetAllInstancesForTypeOK {
	o.Payload = payload
	return o
}

// SetPayload sets the payload to the a1 controller get all instances for type o k response
func (o *A1ControllerGetAllInstancesForTypeOK) SetPayload(payload []models.PolicyInstanceID) {
	o.Payload = payload
}

// WriteResponse to the client
func (o *A1ControllerGetAllInstancesForTypeOK) WriteResponse(rw http.ResponseWriter, producer runtime.Producer) {

	rw.WriteHeader(200)
	payload := o.Payload
	if payload == nil {
		// return empty array
		payload = make([]models.PolicyInstanceID, 0, 50)
	}

	if err := producer.Produce(rw, payload); err != nil {
		panic(err) // let the recovery middleware deal with this
	}
}

// A1ControllerGetAllInstancesForTypeServiceUnavailableCode is the HTTP code returned for type A1ControllerGetAllInstancesForTypeServiceUnavailable
const A1ControllerGetAllInstancesForTypeServiceUnavailableCode int = 503

/*A1ControllerGetAllInstancesForTypeServiceUnavailable Potentially transient backend database error. Client should attempt to retry later.

swagger:response a1ControllerGetAllInstancesForTypeServiceUnavailable
*/
type A1ControllerGetAllInstancesForTypeServiceUnavailable struct {
}

// NewA1ControllerGetAllInstancesForTypeServiceUnavailable creates A1ControllerGetAllInstancesForTypeServiceUnavailable with default headers values
func NewA1ControllerGetAllInstancesForTypeServiceUnavailable() *A1ControllerGetAllInstancesForTypeServiceUnavailable {

	return &A1ControllerGetAllInstancesForTypeServiceUnavailable{}
}

// WriteResponse to the client
func (o *A1ControllerGetAllInstancesForTypeServiceUnavailable) WriteResponse(rw http.ResponseWriter, producer runtime.Producer) {

	rw.Header().Del(runtime.HeaderContentType) //Remove Content-Type on empty responses

	rw.WriteHeader(503)
}

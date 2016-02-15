// Helper functionality to manage telemetry policies
//
// This isn't part of the core API, but is just utility functionality
//
// Simon, August 2015

package xrm2m_util

import (
	"encoding/json"
	"xrm2m"
)

type TelemetryPolicy struct {
	Name     string                    `json:""`
	Metadata interface{}               `json:",omitempty"`
	Tables   map[string]TelemetryTable `json:""`
}

type TelemetryTable struct {
	Period int      `json:""`
	Paths  []string `json:""`
}

// Upddate a telemetry policy. Assume we use the policy name as filename
func UpdateTelemetryPolicy(m2m *xrm2m.M2MClient, policy *TelemetryPolicy) {
	if m2m.Error != nil {
		return
	}
	path := "/telemetry/policies/" + policy.Name + ".policy"
	data, err := json.MarshalIndent(policy, "", "  ")
	if err != nil {
		m2m.Error = err
		m2m.LastOp = "UpdateTelemetryPolicy"
		return
	}
	m2m.WriteFile(path, data)
}

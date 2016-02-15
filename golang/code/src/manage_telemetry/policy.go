// Simple telemetry management client example
//
// Simon, August 2015

package main

import (
	"errors"
	"time"
	"xrm2m"
)

// Metadata type. This is totally under the control of the script, and can
// be whatever you like
type Metadata struct {
	Script string `json:""`
	Date   string `json:""`
}

// Select one of the sample policies, fill in the live metadata, and update
func set_policy(m2m *xrm2m.M2MClient, policy_name string) error {
	policy, ok := policies[policy_name]
	if !ok {
		return errors.New("bad policy name")
	}

	// Add some metadata including the time we're changing policy
	now, _ := time.Now().MarshalText()
	policy.Metadata = &Metadata{
		Script: "Telemetry management bot 0.1",
		Date:   string(now),
	}

	// Set it using the M2M API
	m2m.UpdateTelemetryPolicy(policy)
	return m2m.Error
}

// Set of sample policies
var policies = map[string]*xrm2m.TelemetryPolicy{

	// Policy 1 - normal
	"normal": &xrm2m.TelemetryPolicy{
		Name: "example_policy",
		Tables: map[string]xrm2m.TelemetryTable{
			"Medium stats": xrm2m.TelemetryTable{
				Period: 30,
				Paths: []string{
					"RootOper.InfraStatistics.Interface(['*']).GenericCounters",
				},
			},
			"Slow stats": xrm2m.TelemetryTable{
				Period: 60,
				Paths: []string{
					"RootOper.QOS.Interface([*]).Input.Statistics",
					"RootOper.QOS.Interface([*]).Output.Statistics",
				},
			},
		},
	},

	// Policy 2 - investigating something specific
	"debug": &xrm2m.TelemetryPolicy{
		Name: "example_policy",
		Tables: map[string]xrm2m.TelemetryTable{
			"Fast stats": xrm2m.TelemetryTable{
				Period: 15,
				Paths: []string{
					"RootOper.InfraStatistics.Interface(['tunnel-te101']).Latest.GenericCounters",
					"RootOper.InfraStatistics.Interface(['tunnel-te102']).Latest.GenericCounters",
					"RootOper.InfraStatistics.Interface(['HundredGigE*']).Latest.GenericCounters",
				},
			},
			"Medium stats": xrm2m.TelemetryTable{
				Period: 30,
				Paths: []string{
					"RootOper.InfraStatistics.Interface(['*']).GenericCounters",
				},
			},
			"Slow stats": xrm2m.TelemetryTable{
				Period: 60,
				Paths: []string{
					"RootOper.QOS.Interface([*]).Input.Statistics",
					"RootOper.QOS.Interface([*]).Output.Statistics",
				},
			},
		},
	},
}

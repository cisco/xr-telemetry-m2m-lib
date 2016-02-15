// Simple telemetry management client example
//
// Simon, August 2015

package main

import (
	"encoding/json"
	"fmt"
	"xrm2m"
	"xrm2m_util"
)

type Collector struct {
	Address string `json:"IPAddr"`
	Port    int    `json:"TCPPort"`
}

// Populate the commit buffer with our desired state for collctors
func update_collectors(m2m *xrm2m.M2MClient, collectors *[]Collector) {
	const path_root = "RootCfg.Telemetry.JSON.PolicyGroup(['main']).IPv4Address"

	// Indicate we're going to replace the whole subtree for this Policy
	m2m.Replace(path_root)

	// Set each collector's IP address and port
	for _, collector := range *collectors {
		key, _ := json.Marshal(collector)
		m2m.Set(fmt.Sprintf("%s(%s)", path_root, key), true)
	}

	// For educational purposes, show what changes are about to be committed
	xrm2m_util.PrintChanges(m2m)

	// Commit any changes if there are any
	xrm2m_util.CommitAndPrintOutcome(m2m, "telemetry bot v0.1")
}

// Few bits of helper functionality for simple scripts.
//
// This isn't part of the core API, but is just utility functionality
//
// Simon, August 2015

package xrm2m_util

import (
	"fmt"
	"log"
	"os"
	"xrm2m"
)

// Create a credentials struct from environment variables
func CredsFromEnv() *xrm2m.Creds {
	creds := &xrm2m.Creds{
		User:        os.Getenv("SSH_USER"),
		Password:    os.Getenv("SSH_PASSWORD"),
		Keypathname: os.Getenv("SSH_KEYFILE"),
	}
	if creds.User == "" {
		log.Fatal("SSH_USER environment variable must be set")
	}
	if creds.Password == "" && creds.Keypathname == "" {
		log.Fatal("At least one of SSH_PASSWORD and SSH_KEYFILE environment variables must be set")
	}
	return creds
}

// Print any changes that would be effected with a commit to stdout
func PrintChanges(m2m *xrm2m.M2MClient) {
	changes := m2m.GetChanges()
	if len(changes) > 0 {
		fmt.Println("Changes to be committed:\n")
		for _, change := range changes {
			for key, value := range change {
				fmt.Printf("%10s: %v\n", key, value)
			}
			fmt.Println("")
		}
	}
}

// Commit and print the outcome to stdout, including any error that happened
// during population of the commit buffer prior to this call
func CommitAndPrintOutcome(m2m *xrm2m.M2MClient, label string) {
	commit_id := m2m.Commit(label, "")
	if m2m.Error == nil {
		if commit_id == "" {
			fmt.Println("No commit required")
		} else {
			fmt.Println("New commit ", commit_id)
		}
	} else {
		fmt.Printf("Error during %s: %s\n", m2m.LastOp, m2m.Error.Error())
	}
}

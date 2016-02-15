// Simple telemetry management client example
//
// Simon, August 2015

package main

import (
	"fmt"
	"github.com/abiosoft/ishell"
	"log"
	"net"
	"os"
	"strconv"
	"xrm2m"
	"xrm2m_util"
)

func main() {
	if len(os.Args) != 2 {
		log.Fatalf("Usage: %s <host>", os.Args[0])
	}
	m2m, err := xrm2m.NewClient(os.Args[1]+":22", xrm2m_util.CredsFromEnv())
	if err != nil {
		log.Fatal("Can't open M2M session: " + err.Error())
	}
	defer m2m.Close()
	fmt.Println("Connection established")
	enter_shell(m2m)
}

func enter_shell(m2m *xrm2m.M2MClient) {
	const done = "<done>"
	shell := ishell.NewShell()
	shell.Println("Welcome to the telemetry management demo")

	shell.Register("collectors", func(args ...string) (string, error) {
		var cols []Collector
		for _, arg := range args {
			host, port, _ := net.SplitHostPort(arg)
			portnum, _ := strconv.Atoi(port)
			cols = append(cols, Collector{Address: host, Port: portnum})
		}
		update_collectors(m2m, &cols)
		return "Updated collectors", nil
	})

	shell.Register("policy", func(args ...string) (string, error) {
		if len(args) != 1 {
			return "Please specify a policy name", nil
		}
		err := set_policy(m2m, args[0])
		return "Updated policy", err
	})
	shell.Start()
}

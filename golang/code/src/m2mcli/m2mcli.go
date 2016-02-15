// Very basic CLI client for XR M2M package
//
// Simon, August 2015

package main

import (
	"github.com/abiosoft/ishell"
	"github.com/kr/pretty"
	"log"
	"os"
	"strings"
	"xrm2m"
	"xrm2m_util"
)

func main() {
	if len(os.Args) != 2 {
		log.Fatalf("Usage: %s <host>", os.Args[0])
	}
	m2m, err := xrm2m.NewClient(os.Args[1]+":22", xrm2m_util.CredsFromEnv())
	if err != nil {
		log.Fatal("Can't create M2M client session: " + err.Error())
	}
	defer m2m.Close()

	enter_shell(m2m)
}

func enter_shell(m2m *xrm2m.M2MClient) {
	const done = "<done>"
	shell := ishell.NewShell()
	shell.Println("Welcome to the XR M2M CLI")

	// CLI transition functions

	shell.Register("cli_exec", func(args ...string) (string, error) {
		return m2m.CliExec(strings.Join(args, " ")), m2m.Error
	})
	shell.Register("cli_get", func(args ...string) (string, error) {
		return pretty_print(m2m.CliGet(strings.Join(args, " ")), m2m.Error)
	})
	shell.Register("cli_set", func(args ...string) (string, error) {
		m2m.CliSet(strings.Join(args, " "))
		return done, m2m.Error
	})
	shell.Register("write_file", func(args ...string) (string, error) {
		shell.Println("Input multiple lines and end with semicolon ';'.")
		data := shell.ReadMultiLines(";")
		data = strings.TrimSuffix(data, ";") // @@@ bug in ishell
		m2m.WriteFile(args[0], []byte(data))
		return done, m2m.Error
	})

	// Basic schema ops

	shell.Register("get", func(args ...string) (string, error) {
		return pretty_print(m2m.Get(strings.Join(args, " ")), m2m.Error)
	})

	shell.Register("get_children", func(args ...string) (string, error) {
		return pretty_print(m2m.GetChildren(strings.Join(args, " ")), m2m.Error)
	})

	shell.Register("set", func(args ...string) (string, error) {
		m2m.Set(args[0], args[1])
		return done, m2m.Error
	})

	shell.Register("delete", func(args ...string) (string, error) {
		m2m.Delete(strings.Join(args, " "))
		return done, m2m.Error
	})

	shell.Register("replace", func(args ...string) (string, error) {
		m2m.Replace(strings.Join(args, " "))
		return done, m2m.Error
	})

	// Commit operations. Both "comment" and "label" are optional

	shell.Register("commit", func(args ...string) (string, error) {
		comment, label := optional(args)
		return m2m.Commit(comment, label), m2m.Error
	})

	shell.Register("commit_replace", func(args ...string) (string, error) {
		comment, label := optional(args)
		return m2m.CommitReplace(comment, label), m2m.Error
	})

	shell.Register("discard_changes", func(args ...string) (string, error) {
		m2m.DiscardChanges()
		return done, m2m.Error
	})

	shell.Register("get_changes", func(args ...string) (string, error) {
		return pretty_print(m2m.GetChanges(), m2m.Error)
	})

	// Schema

	shell.Register("get_schema", func(args ...string) (string, error) {
		path := args[0]
		var fields string
		if len(args) == 2 {
			fields = args[1]
		}
		return pretty_print(m2m.GetSchema(path, fields), m2m.Error)
	})

	shell.Register("get_version", func(args ...string) (string, error) {
		return pretty_print(m2m.GetVersion(), m2m.Error)
	})

	shell.Start()
}

func pretty_print(val interface{}, err error) (string, error) {
	if err == nil {
		pretty.Println(val)
	}
	return "", err
}

func optional(args []string) (string, string) {
	var comment, label string
	if len(args) >= 1 {
		comment = args[0]
	}
	if len(args) >= 2 {
		label = args[1]
	}
	return comment, label
}

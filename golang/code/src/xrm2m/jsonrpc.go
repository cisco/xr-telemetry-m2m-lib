// Simple client library for the IOS-XR M2M API over JSON-RPC-over-SSH transport
//
// Simon, August 2015

package xrm2m

import (
	"jsonrpc2"
	"net/rpc"
)

// Represent an M2M client connection, plus error. If the Error is non-nil then
// further operations will be skipped, and LastOp will contain the JSON-RPC
// method that triggered the failure
type M2MClient struct {
	rpc.Client
	Error  error
	LastOp string
}

// Create a JSON-RPC over SSH client session for the XR M2M API
func NewClient(host string, creds *Creds) (*M2MClient, error) {
	xrs, err := NewXrSession(host, creds, "run json_rpc_server")
	if err != nil {
		return nil, err
	}
	return &M2MClient{*jsonrpc2.NewClient(xrs), nil, ""}, nil
}

//
// Wrappers for each individual API
//

// CLI transition tools
func (m2m *M2MClient) CliExec(command string) string {
	return m2m.call_for_string("cli_exec", "command", command)
}

func (m2m *M2MClient) CliGet(command string) [][]interface{} {
	return m2m.call_for_array_of_arrays("cli_get", "command", command)
}

func (m2m *M2MClient) CliSet(command string) {
	m2m.call_for_void("cli_set", "command", command)
}

func (m2m *M2MClient) WriteFile(filename string, data []byte) {
	m2m.call_for_void("write_file", "filename", filename, "data", string(data))
}

// Basic schema ops
func (m2m *M2MClient) Get(path string) [][]interface{} {
	return m2m.call_for_array_of_arrays("get", "path", path)
}

func (m2m *M2MClient) GetChildren(path string) []string {
	return m2m.call_for_string_array("get_children", "path", path)
}

func (m2m *M2MClient) Set(path string, value interface{}) {
	m2m.call_for_void("set", "path", path, "value", value)
}

func (m2m *M2MClient) Delete(path string) {
	m2m.call_for_void("delete", "path", path)
}

func (m2m *M2MClient) Replace(path string) {
	m2m.call_for_void("replace", "path", path)
}

// Commit operations. Both "comment" and "label" are optional. If a new
// commit history point actually gets created, then that gets returned as
// a non-empty string. A non-error return code and empty commit_id string
// indicates a successful operation that did not result in a new commit
// point being created.
func (m2m *M2MClient) Commit(comment, label string) string {
	return m2m.call_for_optional_string("commit", "comment", comment, "label", label)
}

func (m2m *M2MClient) CommitReplace(comment, label string) string {
	return m2m.call_for_optional_string("commit_replace", "comment", comment, "label", label)
}

func (m2m *M2MClient) DiscardChanges() {
	m2m.call_for_void("discard_changes")
}

func (m2m *M2MClient) GetChanges() []map[string]interface{} {
	return m2m.call_for_array_of_objects("get_changes")
}

// Schema inspection

func (m2m *M2MClient) GetSchema(path, fields string) map[string]interface{} {
	if fields != "" {
		return m2m.call_for_object("get_schema", "path", path, "fields", fields)
	} else {
		return m2m.call_for_object("get_schema", "path", path)
	}
}

func (m2m *M2MClient) GetVersion() map[string]interface{} {
	return m2m.call_for_object("get_version")
}

// ---------------------------------------------------------------------------

// Helper functions to wrap individal APIs

func (m2m *M2MClient) call_for_array_of_arrays(method string, args ...interface{}) [][]interface{} {
	if m2m.Error != nil {
		return nil
	}
	var reply [][]interface{}
	m2m.Error = m2m.Call(method, make_request(args), &reply)
	m2m.LastOp = method
	return reply
}

func (m2m *M2MClient) call_for_object(method string, args ...interface{}) map[string]interface{} {
	if m2m.Error != nil {
		return nil
	}
	var reply map[string]interface{}
	m2m.Error = m2m.Call(method, make_request(args), &reply)
	m2m.LastOp = method
	return reply
}

func (m2m *M2MClient) call_for_array_of_objects(method string, args ...interface{}) []map[string]interface{} {
	if m2m.Error != nil {
		return nil
	}
	var reply []map[string]interface{}
	m2m.Error = m2m.Call(method, make_request(args), &reply)
	m2m.LastOp = method
	return reply
}

func (m2m *M2MClient) call_for_string(method string, args ...interface{}) string {
	if m2m.Error != nil {
		return ""
	}
	var reply string
	m2m.Error = m2m.Call(method, make_request(args), &reply)
	m2m.LastOp = method
	return reply
}

func (m2m *M2MClient) call_for_optional_string(method string, args ...interface{}) string {
	if m2m.Error != nil {
		return ""
	}
	var reply *string
	m2m.Error = m2m.Call(method, make_request(args), &reply)
	m2m.LastOp = method
	if reply == nil {
		return ""
	} else {
		return *reply
	}
}

func (m2m *M2MClient) call_for_string_array(method string, args ...interface{}) []string {
	if m2m.Error != nil {
		return nil
	}
	var reply []string
	m2m.Error = m2m.Call(method, make_request(args), &reply)
	m2m.LastOp = method
	return reply
}

func (m2m *M2MClient) call_for_void(method string, args ...interface{}) {
	if m2m.Error != nil {
		return
	}
	var reply interface{}
	m2m.Error = m2m.Call(method, make_request(args), &reply)
	m2m.LastOp = method
}

func make_request(args []interface{}) *map[string]interface{} {
	request := make(map[string]interface{})
	for i := 0; i < len(args); i += 2 {
		request[args[i].(string)] = args[i+1]
	}
	return &request
}

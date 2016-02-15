// Simple wrapper around invoking a service on an IOS-XR router over SSH
//
// Simon, August 2015

package xrm2m

import (
	"errors"
	"io"
	"io/ioutil"
	"time"

	// normal ssh doesn't support aes128-cbc
	"github.com/ScriptRock/crypto/ssh"
)

// Simplified SSH credentials
// Must provide a username, and at least one of password and key pathname
type Creds struct {
	User        string
	Password    string
	Keypathname string
}

// Represent running a long-lived command on an XR router over SSH
// as a ReadWriteCloser
type XrSession struct {
	session *ssh.Session
	stdin   *io.WriteCloser
	stdout  *io.Reader
	ready   bool
}

// Create an SSH session that can connect to an XR router and run one
// potentially long-lived command, interacting over stdin/stdout
func NewXrSession(host string, creds *Creds, cmd string) (*XrSession, error) {
	auth, err := get_auth(creds)
	if err != nil {
		return nil, err
	}
	sshConfig := &ssh.ClientConfig{
		User:   creds.User,
		Auth:   auth,
		Config: ssh.Config{Ciphers: []string{"aes128-ctr", "aes128-cbc"}},
	}

	client, err := ssh.Dial("tcp", host, sshConfig)
	if err != nil {
		return nil, errors.New("Can't connect: " + err.Error())
	}

	session, err := client.NewSession()
	if err != nil {
		return nil, errors.New("Can't create session: " + err.Error())
	}

	stdin, err := session.StdinPipe()
	if err != nil {
		return nil, errors.New("Can't create stdin pipe: " + err.Error())
	}

	stdout, err := session.StdoutPipe()
	if err != nil {
		return nil, errors.New("Can't create stdout pipe: " + err.Error())
	}

	err = session.Start(cmd)
	if err != nil {
		return nil, errors.New("Can't start command: " + err.Error())
	}

	xrsession := &XrSession{
		session: session,
		stdin:   &stdin,
		stdout:  &stdout,
		ready:   false,
	}

	// Swallow the preamble of a couple of blank lines and a date
	go func() {
		buf := make([]byte, 128) // just needs to be big enough
		_, err := stdout.Read(buf)
		if err != nil {
			panic("Can't read preamble: " + err.Error())
		}
		xrsession.ready = true
	}()

	return xrsession, nil
}

// Convert simplified credentials into something useful for the ssh package
func get_auth(creds *Creds) ([]ssh.AuthMethod, error) {
	auth := []ssh.AuthMethod{}

	// Passwords. This isn't enough for a typical SSH server (which will usually
	// be configured for KeyboardInteractive, not Password) but fine for XR.
	if creds.Password != "" {
		auth = append(auth, ssh.Password(creds.Password))
	}

	// Keys
	if creds.Keypathname != "" {
		buf, err := ioutil.ReadFile(creds.Keypathname)
		if err != nil {
			return nil, errors.New("Can't read private key file: " + err.Error())
		}

		key, err := ssh.ParsePrivateKey(buf)
		if err != nil {
			return nil, errors.New("Can't parse private key: " + err.Error())
		}

		auth = append(auth, ssh.PublicKeys(key))
	}

	return auth, nil
}

// Handle the ReadWriteCloser semantics. We cheesily block if asked to do
// something before the session itself is fully up, but this is at worst
// only a very transient thing right when the session is being established.
func (xrs *XrSession) Read(p []byte) (n int, err error) {
	for !xrs.ready {
		time.Sleep(100 * time.Millisecond)
	}
	return (*xrs.stdout).Read(p)
}

func (xrs *XrSession) Write(p []byte) (n int, err error) {
	for !xrs.ready {
		time.Sleep(100 * time.Millisecond)
	}
	return (*xrs.stdin).Write(p)
}

func (xrs *XrSession) Close() error {
	return (*xrs.session).Close()
}

package cmdutil

import (
	"io"
	"os"
	"sync"

	"github.com/tencentcloud/cls-cli/internal/client"
	"github.com/tencentcloud/cls-cli/internal/core"
	"github.com/tencentcloud/cls-cli/internal/output"
)

type IOStreams struct {
	In     io.Reader
	Out    io.Writer
	ErrOut io.Writer
}

type Factory struct {
	Config    func() (*core.CliConfig, error)
	CLSClient func() (*client.APIClient, error)
	IOStreams  *IOStreams
	Format    output.Format
	DryRun    bool
}

func NewDefault() *Factory {
	streams := &IOStreams{
		In:     os.Stdin,
		Out:    os.Stdout,
		ErrOut: os.Stderr,
	}

	var (
		cfgOnce    sync.Once
		cfgVal     *core.CliConfig
		cfgErr     error
		clientOnce sync.Once
		clientVal  *client.APIClient
		clientErr  error
	)

	configFn := func() (*core.CliConfig, error) {
		cfgOnce.Do(func() {
			cfgVal, cfgErr = core.LoadConfig()
		})
		return cfgVal, cfgErr
	}

	clientFn := func() (*client.APIClient, error) {
		clientOnce.Do(func() {
			cfg, err := configFn()
			if err != nil {
				clientErr = err
				return
			}
			clientVal = client.NewAPIClient(cfg.SecretID, cfg.SecretKey, cfg.Region, cfg.Endpoint)
		})
		return clientVal, clientErr
	}

	return &Factory{
		Config:    configFn,
		CLSClient: clientFn,
		IOStreams:  streams,
	}
}

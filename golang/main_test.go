package main

import (
	"io"
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/stretchr/testify/assert"
	"k8s.io/apimachinery/pkg/version"
	disco "k8s.io/client-go/discovery/fake"
	"k8s.io/client-go/kubernetes/fake"
)

func TestGetKubernetesVersion(t *testing.T) {
	okClientset := fake.NewSimpleClientset()
	okClientset.Discovery().(*disco.FakeDiscovery).FakedServerVersion = &version.Info{GitVersion: "1.25.0-fake"}

	okVer, err := getKubernetesVersion(okClientset)
	assert.NoError(t, err)
	assert.Equal(t, "1.25.0-fake", okVer)

	badClientset := fake.NewSimpleClientset()
	badClientset.Discovery().(*disco.FakeDiscovery).FakedServerVersion = &version.Info{}

	badVer, err := getKubernetesVersion(badClientset)
	assert.NoError(t, err)
	assert.Equal(t, "", badVer)
}

func TestHealthHandler(t *testing.T) {
	req := httptest.NewRequest(http.MethodGet, "/healthz", nil)
	rec := httptest.NewRecorder()

	healthHandler(rec, req)
	res := rec.Result()

	assert.Equal(t, http.StatusOK, res.StatusCode)

	defer func(Body io.ReadCloser) {
		assert.NoError(t, Body.Close())
	}(res.Body)
	resp, err := io.ReadAll(res.Body)

	assert.NoError(t, err)
	assert.Equal(t, "ok", string(resp))
}

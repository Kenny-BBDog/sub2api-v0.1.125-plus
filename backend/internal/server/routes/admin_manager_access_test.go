package routes

import (
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/Wei-Shaw/sub2api/internal/handler"
	"github.com/Wei-Shaw/sub2api/internal/server/middleware"
	"github.com/Wei-Shaw/sub2api/internal/service"
	"github.com/gin-gonic/gin"
	"github.com/stretchr/testify/require"
)

func TestRegisterAdminRoutesManagerAccessScope(t *testing.T) {
	gin.SetMode(gin.TestMode)

	router := gin.New()
	router.Use(gin.Recovery())

	v1 := router.Group("/api/v1")
	RegisterAdminRoutes(v1, &handler.Handlers{Admin: &handler.AdminHandlers{}}, func(c *gin.Context) {
		c.Set(string(middleware.ContextKeyUser), middleware.AuthSubject{UserID: 2})
		c.Set(string(middleware.ContextKeyUserRole), service.RoleManager)
		c.Next()
	})

	for _, tc := range []struct {
		name string
		path string
	}{
		{name: "dashboard", path: "/api/v1/admin/dashboard/stats"},
		{name: "ops", path: "/api/v1/admin/ops/dashboard/overview"},
		{name: "redeem", path: "/api/v1/admin/redeem-codes"},
	} {
		t.Run(tc.name, func(t *testing.T) {
			w := httptest.NewRecorder()
			req := httptest.NewRequest(http.MethodGet, tc.path, nil)

			router.ServeHTTP(w, req)

			require.NotEqual(t, http.StatusForbidden, w.Code)
		})
	}

	t.Run("settings stays admin only", func(t *testing.T) {
		w := httptest.NewRecorder()
		req := httptest.NewRequest(http.MethodGet, "/api/v1/admin/settings", nil)

		router.ServeHTTP(w, req)

		require.Equal(t, http.StatusForbidden, w.Code)
	})
}

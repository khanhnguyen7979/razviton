(() => {
  const API_BASE = "";
  const API = `${API_BASE}/api/auth`;

  const $$ = (sel) => document.querySelector(sel);
  const toast = (msg) => {
    let el = document.getElementById("auth-toast");
    if (!el) {
      el = document.createElement("div");
      el.id = "auth-toast";
      el.style.cssText = "position:fixed;right:12px;top:12px;padding:10px 12px;border-radius:8px;background:#111;color:#fff;z-index:9999;";
      document.body.appendChild(el);
    }
    el.textContent = msg;
    el.style.display = "block";
    setTimeout(() => (el.style.display = "none"), 3000);
  };

  const request = async (path, options = {}) => {
    const resp = await fetch(`${API}${path}`, {
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      ...options
    });
    const data = await resp.json().catch(() => ({}));
    if (!resp.ok) throw new Error(data.detail || "REQUEST_FAILED");
    return data;
  };

  const getMe = async () => {
    const res = await request("/me", { method: "GET" });
    return res;
  };

  const bindAuthWidgets = async () => {
    const loginLink = document.getElementById("auth-login-link");
    const registerLink = document.getElementById("auth-register-link");
    const accountLink = document.getElementById("auth-account-link");
    const logoutBtn = document.getElementById("auth-logout");
    const userBadge = document.getElementById("auth-user");

    let user = null;
    try {
      user = await getMe();
    } catch (_) {
      user = null;
    }

    if (user) {
      if (loginLink) loginLink.style.display = "none";
      if (registerLink) registerLink.style.display = "none";
      if (accountLink) {
        accountLink.style.display = "inline-block";
        accountLink.href = "/account.html";
      }
      if (userBadge) {
        userBadge.textContent = `Hello, ${user.username}`;
      }
      if (logoutBtn) {
        logoutBtn.style.display = "inline-block";
        logoutBtn.addEventListener("click", async (e) => {
          e.preventDefault();
          await request("/logout", { method: "POST", body: JSON.stringify({ all_devices: false }) });
          toast("Signed out");
          window.location.href = "/index.html";
        });
      }
    } else {
      if (loginLink) loginLink.style.display = "inline-block";
      if (registerLink) registerLink.style.display = "inline-block";
      if (accountLink) accountLink.style.display = "none";
      if (userBadge) userBadge.textContent = "";
      if (logoutBtn) logoutBtn.style.display = "none";
    }

    return user;
  };

  const bindAuthForms = () => {
    const loginForm = document.getElementById("login-form");
    if (loginForm) {
      loginForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const fd = new FormData(loginForm);
        const payload = {
          identifier: String(fd.get("identifier") || "").trim(),
          password: String(fd.get("password") || "")
        };
        try {
          const data = await request("/login", {
            method: "POST",
            body: JSON.stringify(payload)
          });
          toast(`Signed in: ${data.username}`);
          window.location.href = "/account.html";
        } catch (err) {
          toast(err.message || "Login failed");
        }
      });
    }

    const registerForm = document.getElementById("register-form");
    if (registerForm) {
      const fields = document.getElementById("registration-fields");
      const status = document.getElementById("registration-status");
      request("/config").then((config) => {
        const enabled = config.registration_enabled === true;
        if (fields) fields.disabled = !enabled;
        if (status) status.textContent = enabled ? "Registration is available. Read the account-data disclosure before submitting." : "New registrations are temporarily paused. Existing members can still sign in.";
      }).catch(() => {
        if (fields) fields.disabled = true;
        if (status) status.textContent = "Registration availability could not be verified. Please try again later.";
      });
    }
    if (registerForm) {
      registerForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const fd = new FormData(registerForm);
        const payload = {
          username: String(fd.get("username") || "").trim(),
          email: String(fd.get("email") || "").trim(),
          password: String(fd.get("password") || ""),
          full_name: String(fd.get("full_name") || "").trim()
        };
        try {
          await request("/register", { method: "POST", body: JSON.stringify(payload) });
          toast("Account created");
          window.location.href = "/account.html";
        } catch (err) {
          toast(err.message || "Register failed");
        }
      });
    }

    const accountMe = document.getElementById("account-me");
    if (accountMe) {
      bindAuthWidgets().then((user) => {
        accountMe.textContent = user ? `${user.username} (${user.email})` : "Not signed in";
      });
    }

    const adminStats = document.getElementById("admin-stats");
    if (adminStats) {
      request("/admin/stats", { method: "GET" })
        .then((stats) => {
          adminStats.innerHTML = `<li>Total users: ${stats.total_users}</li><li>Active users: ${stats.active_users}</li><li>Active sessions: ${stats.active_sessions}</li>`;
        })
        .catch(() => {
          adminStats.innerHTML = "<li>Administrator access required.</li>";
        });
    }
  };

  document.addEventListener("DOMContentLoaded", async () => {
    bindAuthForms();
    await bindAuthWidgets();
  });
})();


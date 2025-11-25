document.addEventListener("DOMContentLoaded", () => {
  // Clear flash messages after 4 seconds
  const msgs = document.querySelectorAll(".flash");
  if (msgs.length) {
    setTimeout(() => {
      msgs.forEach(m => m.style.display = "none");
    }, 4000);
  }

  // Confirm passwords TODO: Could just do in Python
  const reg = document.getElementById("registerForm");
  if (reg) {
    reg.addEventListener("submit", (e) => {
      const pw = reg.querySelector("input[name='password']").value;
      const pw2 = reg.querySelector("input[name='password_confirm']").value;
      if (pw !== pw2) {
        e.preventDefault();
        alert("Passwords do not match.");
      }
    });
  }
});

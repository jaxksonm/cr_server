document.addEventListener("DOMContentLoaded", () => {
  // auto-dismiss flash messages
  const msgs = document.querySelectorAll(".flash");
  if (msgs.length) {
    setTimeout(() => {
      msgs.forEach(m => m.style.display = "none");
    }, 4000);
  }

  // simple client-side confirm for register password match
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

document.addEventListener("DOMContentLoaded", () => {
  // Clear flash messages after 4 seconds
  const msgs = document.querySelectorAll(".flash");
  if (msgs.length) {
    setTimeout(() => {
      msgs.forEach(m => m.style.display = "none");
    }, 5000);
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

document.addEventListener('DOMContentLoaded', function(){
    document.querySelectorAll('.nested-bubble').forEach(function(el, i){
      // only add pins if they aren't present already
      if (!el.querySelector('.pin')) {
        const pinL = document.createElement('span');
        pinL.className = 'pin';

        const pinR = document.createElement('span');
        pinR.className = 'pin right';

        el.appendChild(pinL);
        el.appendChild(pinR);
      }

      const r = (Math.random() * 4) - 2;
      el.style.transform = 'rotate(' + r + 'deg)';
    });
  });
document.addEventListener("DOMContentLoaded", () => {
  // Reveal sections gently as they enter the viewport.
  const revealItems = document.querySelectorAll(".reveal");
  if ("IntersectionObserver" in window) {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add("visible");
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.08 });
    revealItems.forEach(item => observer.observe(item));
  } else {
    revealItems.forEach(item => item.classList.add("visible"));
  }

  // Small count-up effect for dashboard totals.
  document.querySelectorAll("[data-count]").forEach(el => {
    const target = Number(el.dataset.count || 0);
    if (!Number.isFinite(target) || target === 0) return;
    const duration = 650, start = performance.now();
    const tick = now => {
      const progress = Math.min((now - start) / duration, 1);
      el.textContent = Math.round(target * (1 - Math.pow(1 - progress, 3))).toLocaleString();
      if (progress < 1) requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
  });

  // Dismissible status messages.
  document.querySelectorAll(".flash-close").forEach(button => {
    button.addEventListener("click", () => {
      const flash = button.closest(".flash");
      flash.style.opacity = "0";
      flash.style.transform = "translateY(-5px)";
      setTimeout(() => flash.remove(), 180);
    });
  });

  // Feedback form completion progress and comment character count.
  const form = document.getElementById("feedbackForm");
  if (form) {
    const questions = [...form.querySelectorAll(".rating-question")];
    const progressText = document.getElementById("progressText");
    const progressBar = document.getElementById("progressBar");
    const updateProgress = () => {
      const answered = questions.filter(q => q.querySelector('input[type="radio"]:checked')).length;
      progressText.textContent = `${answered} of ${questions.length} answered`;
      progressBar.style.width = `${questions.length ? answered / questions.length * 100 : 0}%`;
    };
    form.querySelectorAll('input[type="radio"]').forEach(input => input.addEventListener("change", () => {
      updateProgress();
      const group = input.closest(".rating-question");
      group.classList.add("answered");
    }));
    updateProgress();

    const comment = document.getElementById("comment");
    const count = document.getElementById("charCount");
    if (comment && count) {
      const updateCount = () => count.textContent = `${comment.value.length} / 500`;
      comment.addEventListener("input", updateCount);
      updateCount();
    }
    form.addEventListener("submit", event => {
      const course = document.getElementById("course_id");
      const answered = questions.filter(q => q.querySelector('input[type="radio"]:checked')).length;
      if (!course.value || answered !== questions.length) {
        event.preventDefault();
        form.reportValidity();
        const firstMissing = questions.find(q => !q.querySelector('input[type="radio"]:checked'));
        if (firstMissing) firstMissing.scrollIntoView({ behavior: "smooth", block: "center" });
      }
    });
  }
});

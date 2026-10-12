document.addEventListener("DOMContentLoaded", function () {
    const display = document.getElementById("timer-display");

    if (!display) return;

    const deadlineValue = display.dataset.deadline;
    const refreshButton = document.getElementById("timer-refresh");
    const checkForm = document.getElementById("timer-check-form");

    if (!deadlineValue) return;

    const deadline = Number(deadlineValue);

    if (!Number.isFinite(deadline)) return;

    let sudahDiperiksa = false;

    function renderTimer() {
        const sisa = Math.max(0, Math.ceil((deadline - Date.now()) / 1000));
        const menit = Math.floor(sisa / 60);
        const detik = sisa % 60;

        display.textContent =
            String(menit).padStart(2, "0") + ":" +
            String(detik).padStart(2, "0");

        if (sisa <= 0 && !sudahDiperiksa) {
            sudahDiperiksa = true;

            if (checkForm) {
                checkForm.requestSubmit();
            } else {
                window.location.reload();
            }
        }
    }

    renderTimer();

    const intervalId = window.setInterval(function () {
        renderTimer();

        if (sudahDiperiksa) {
            window.clearInterval(intervalId);
        }
    }, 250);

    if (refreshButton) {
        refreshButton.addEventListener("click", function () {
            window.location.reload();
        });
    }
});
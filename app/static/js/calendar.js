document.addEventListener("DOMContentLoaded", function () {
    // 1. Fade out flash alerts automatically after 4 seconds
    const alerts = document.querySelectorAll(".alert");
    alerts.forEach(function (alert) {
        setTimeout(function () {
            alert.style.transition = "opacity 0.5s ease, transform 0.5s ease";
            alert.style.opacity = "0";
            alert.style.transform = "translateY(-20px) scale(0.95)";
            setTimeout(function () {
                alert.remove();
            }, 500);
        }, 4000);
    });

    // Alert close button interaction
    const closeButtons = document.querySelectorAll(".alert-close");
    closeButtons.forEach(function (button) {
        button.addEventListener("click", function () {
            const parentAlert = this.closest(".alert");
            if (parentAlert) {
                parentAlert.remove();
            }
        });
    });

    // 2. Calendar Interactive Filters
    const dateFilter = document.getElementById("date-filter");
    const roomFilter = document.getElementById("room-filter");
    const capacityFilter = document.getElementById("capacity-filter");
    const equipmentFilter = document.getElementById("equipment-filter");
    
    function applyFilters() {
        const form = document.querySelector(".calendar-filters");
        if (form) {
            form.submit();
            return;
        }
        
        const queryParams = [];
        if (dateFilter && dateFilter.value) {
            queryParams.push(`date=${encodeURIComponent(dateFilter.value)}`);
        }
        if (roomFilter && roomFilter.value) {
            queryParams.push(`room_id=${encodeURIComponent(roomFilter.value)}`);
        }
        if (capacityFilter && capacityFilter.value) {
            queryParams.push(`capacity=${encodeURIComponent(capacityFilter.value)}`);
        }
        if (equipmentFilter && equipmentFilter.value) {
            queryParams.push(`equipment=${encodeURIComponent(equipmentFilter.value)}`);
        }
        
        const url = window.location.pathname + (queryParams.length > 0 ? "?" + queryParams.join("&") : "");
        window.location.href = url;
    }

    // Trigger filter reload on change or keypress Enter
    if (dateFilter) dateFilter.addEventListener("change", applyFilters);
    if (roomFilter) roomFilter.addEventListener("change", applyFilters);
    if (capacityFilter) {
        capacityFilter.addEventListener("keypress", function(e) {
            if (e.key === 'Enter') applyFilters();
        });
    }
    if (equipmentFilter) {
        equipmentFilter.addEventListener("keypress", function(e) {
            if (e.key === 'Enter') applyFilters();
        });
    }

    // 3. Grid Cell Click-To-Book
    const clickableCells = document.querySelectorAll(".calendar-cell.clickable-slot");
    clickableCells.forEach(function (cell) {
        cell.addEventListener("click", function (e) {
            // Only redirect if they clicked on the empty cell directly, not on a booking card inside it
            if (e.target.closest(".calendar-booking-card")) {
                return;
            }
            
            const roomId = this.getAttribute("data-room-id");
            const dateTimeStr = this.getAttribute("data-datetime");
            if (roomId && dateTimeStr) {
                window.location.href = `/bookings/new?room_id=${roomId}&start_at=${dateTimeStr}`;
            }
        });
    });

    // 4. File upload size limit client verification
    const fileInput = document.querySelector('input[type="file"]');
    if (fileInput) {
        fileInput.addEventListener("change", function () {
            if (this.files && this.files[0]) {
                const fileSize = this.files[0].size; // in bytes
                const maxSize = 16 * 1024 * 1024; // 16MB
                
                if (fileSize > maxSize) {
                    alert("Ошибка: размер файла превышает ограничение 16 МБ.");
                    this.value = ""; // Clear file
                }
            }
        });
    }
});

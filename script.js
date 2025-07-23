// Confirm Booking button functionality
document.getElementById('bookingForm').addEventListener('submit', function (e) {
    e.preventDefault();
    const formData = getFormData();
    
    if (!validateForm(formData)) {
        return;
    }

    // Send data to backend to confirm booking
    fetch('http://127.0.0.1:5000/submit', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            Swal.fire({
                icon: 'success',
                title: 'Booking Confirmed!',
                text: 'Your booking has been confirmed successfully.',
            });

            // Save user name and booking ID in local storage
            localStorage.setItem('userName', formData.userName);
            localStorage.setItem('ID', data.ID);

            // Enable "Check History" button
            document.getElementById('checkHistoryBtn').disabled = false;
        } else {
            Swal.fire({
                icon: 'error',
                title: 'Error!',
                text: data.error || 'An error occurred while confirming the booking.',
            });
        }
    })
    .catch(error => {
        Swal.fire({
            icon: 'error',
            title: 'Error!',
            text: 'An error occurred. Please check the console for details.',
        });
        console.error("Confirm error:", error);
    });
});

// Helper function to get form data
function getFormData() {
    return {
        userName: document.getElementById('userName').value,
        arrivalDate: document.getElementById('arrivalDate').value,
        departureDate: document.getElementById('departureDate').value,
        adults: document.getElementById('adults').value,
        children1to5: document.getElementById('children1to5').value,
        children6to11: document.getElementById('children6to11').value,
        cultureCategory: document.getElementById('cultureCategory').value,
        preferences: document.getElementById('tourPreferences').value
    };
}

// Helper function to validate form
function validateForm(formData) {
    // Check for required fields
    if (!formData.userName || !formData.arrivalDate || !formData.departureDate || !formData.adults || !formData.cultureCategory) {
        Swal.fire({
            icon: 'error',
            title: 'Missing Fields!',
            text: 'Please fill all required fields.',
        });
        return false;
    }

    // Get today's date
    const today = new Date();
    today.setHours(0, 0, 0, 0); // Set time to midnight for accurate date comparison

    // Convert arrival date string to Date object
    const arrivalDate = new Date(formData.arrivalDate);
    arrivalDate.setHours(0, 0, 0, 0);

    // Check if arrival date is in the past
    if (arrivalDate < today) {
        Swal.fire({
            icon: 'error',
            title: 'Invalid Arrival Date!',
            text: 'Arrival date cannot be in the past. Please select today or a future date.',
        });
        return false;
    }

    // Convert departure date string to Date object
    const departureDate = new Date(formData.departureDate);
    departureDate.setHours(0, 0, 0, 0);

    // Check if departure date is in the past
    if (departureDate < today) {
        Swal.fire({
            icon: 'error',
            title: 'Invalid Departure Date!',
            text: 'Departure date cannot be in the past. Please select today or a future date.',
        });
        return false;
    }

    // Check if departure date is before or equal to arrival date
    if (departureDate <= arrivalDate) {
        Swal.fire({
            icon: 'error',
            title: 'Invalid Dates!',
            text: 'Departure date must be after arrival date.',
        });
        return false;
    }

    return true;
}

// Set minimum date for arrival and departure date inputs
document.addEventListener('DOMContentLoaded', function() {
    const arrivalDateInput = document.getElementById('arrivalDate');
    const departureDateInput = document.getElementById('departureDate');
    const today = new Date().toISOString().split('T')[0];
    
    arrivalDateInput.min = today;
    departureDateInput.min = today;

    // Update departure date minimum when arrival date changes
    arrivalDateInput.addEventListener('change', function() {
        departureDateInput.min = this.value;
        if (departureDateInput.value && departureDateInput.value < this.value) {
            departureDateInput.value = this.value;
        }
    });
});

// Show booking history
document.getElementById('checkHistoryBtn').addEventListener('click', function () {
    const userName = localStorage.getItem('userName');
    const ID = localStorage.getItem('ID');

    if (!userName || !ID) {
        Swal.fire({
            icon: 'error',
            title: 'No Booking History!',
            text: 'No booking history found for the current user.',
        });
        return;
    }

    // Fetch booking history for the user
    fetch(`http://127.0.0.1:5000/bookings?userName=${userName}&ID=${ID}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                displayBookings(data.bookings);
                
                const modal = new bootstrap.Modal(document.getElementById('bookingHistoryModal'));
                modal.show();
            } else {
                Swal.fire({
                    icon: 'error',
                    title: 'Error!',
                    text: data.error || 'An error occurred while fetching booking history.',
                });
            }
        })
        .catch(error => {
            Swal.fire({
                icon: 'error',
                title: 'Error!',
                text: 'An error occurred. Please check the console for details.',
            });
            console.error("An error occurred:", error);
        });
});

// Function to display bookings in the modal
function displayBookings(bookings) {
    const bookingsTableBody = document.getElementById('bookingsTableBody');
    bookingsTableBody.innerHTML = ''; // Clear previous content

    bookings.forEach(booking => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${booking.arrivalDate}</td>
            <td>${booking.departureDate}</td>
            <td>${booking.adults}</td>
            <td>${booking.children1to5}</td>
            <td>${booking.children6to11}</td>
            <td>${booking.cultureCategory}</td>
            <td>${booking.tourPreferences}</td>
            <td>
                <button class="btn btn-warning btn-sm" onclick="updateBooking(${booking.id})">Update</button>
                <button class="btn btn-danger btn-sm" onclick="deleteBooking(${booking.id})">Delete</button>
            </td>
        `;
        bookingsTableBody.appendChild(row);
    });
}

// Function to update a booking
function updateBooking(bookingId) {
    Swal.fire({
        title: 'Update Booking',
        html:
            `<div class="container">
                <!-- Tour Details -->
                <h2 class="section-title"><i class="fas fa-map-marked-alt"></i> Tour Details</h2>
                <div class="row mb-4">
                    <div class="col-md-6">
                        <label for="newArrivalDate" class="form-label">Arrival Date:</label>
                        <input type="date" id="newArrivalDate" class="form-control" required>
                    </div>
                    <div class="col-md-6">
                        <label for="newDepartureDate" class="form-label">Departure Date:</label>
                        <input type="date" id="newDepartureDate" class="form-control" required>
                    </div>
                </div>

                <!-- Guest Information -->
                <h2 class="section-title"><i class="fas fa-users"></i> Guest Information</h2>
                <div class="row mb-4">
                    <div class="col-md-6">
                        <label for="newAdults" class="form-label">Number of Adults:</label>
                        <input type="number" id="newAdults" class="form-control" min="1" required>
                    </div>
                    <div class="col-md-3">
                        <label for="newChildren1to5" class="form-label">Children (1-5):</label>
                        <input type="number" id="newChildren1to5" class="form-control" min="0">
                    </div>
                    <div class="col-md-3">
                        <label for="newChildren6to11" class="form-label">Children (6-11):</label>
                        <input type="number" id="newChildren6to11" class="form-control" min="0">
                    </div>
                </div>

                <!-- Culture Category and Tour Preferences -->
                <h2 class="section-title"><i class="fas fa-theater-masks"></i> Culture Category & Tour Preferences</h2>
                <div class="row mb-4">
                    <div class="col-md-6">
                        <label for="newCultureCategory" class="form-label">Select a Category:</label>
                        <select id="newCultureCategory" class="form-select" required>
                            <option value="">Select</option>
                            <option value="Arts & Crafts">Arts & Crafts</option>
                            <option value="Wellness and Traditional Healing">Wellness and Traditional Healing</option>
                            <option value="Performing Arts and Entertainment">Performing Arts and Entertainment</option>
                        </select>
                    </div>
                    <div class="col-md-6">
                        <label for="newTourPreferences" class="form-label">Select a Preference:</label>
                        <select id="newTourPreferences" class="form-select" required>
                            <option value="">Select</option>
                            <option value="Tour Guide">Tour Guide</option>
                            <option value="Transportation">Transportation</option>
                        </select>
                    </div>
                </div>
            </div>`,
        focusConfirm: false,
        showCancelButton: true,
        confirmButtonText: 'Update',
        cancelButtonText: 'Cancel',
        customClass: {
            container: 'custom-swal-container',
            popup: 'custom-swal-popup',
            htmlContainer: 'custom-swal-html-container'
        },
        preConfirm: () => {
            const newArrivalDate = document.getElementById('newArrivalDate').value;
            const newDepartureDate = document.getElementById('newDepartureDate').value;
            const newAdults = document.getElementById('newAdults').value;
            const newChildren1to5 = document.getElementById('newChildren1to5').value;
            const newChildren6to11 = document.getElementById('newChildren6to11').value;
            const newCultureCategory = document.getElementById('newCultureCategory').value;
            const newTourPreferences = document.getElementById('newTourPreferences').value;

            if (!newArrivalDate || !newDepartureDate || !newAdults || !newChildren1to5 || !newChildren6to11 || !newCultureCategory || !newTourPreferences) {
                Swal.showValidationMessage('All fields are required');
                return false;
            }

            return {
                newArrivalDate,
                newDepartureDate,
                newAdults,
                newChildren1to5,
                newChildren6to11,
                newCultureCategory,
                newTourPreferences
            };
        }
    }).then((result) => {
        if (result.isConfirmed) {
            const {
                newArrivalDate,
                newDepartureDate,
                newAdults,
                newChildren1to5,
                newChildren6to11,
                newCultureCategory,
                newTourPreferences
            } = result.value;

            fetch(`http://127.0.0.1:5000/update/${bookingId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    arrivalDate: newArrivalDate,
                    departureDate: newDepartureDate,
                    adults: newAdults,
                    children1to5: newChildren1to5,
                    children6to11: newChildren6to11,
                    cultureCategory: newCultureCategory,
                    TourPreferences: newTourPreferences
                }),
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    Swal.fire({
                        icon: 'success',
                        title: 'Booking Updated!',
                        text: 'Your booking has been updated successfully.',
                    });
                    document.getElementById('checkHistoryBtn').click(); // Refresh booking history
                } else {
                    Swal.fire({
                        icon: 'error',
                        title: 'Error!',
                        text: data.error || 'An error occurred while updating the booking.',
                    });
                }
            })
            .catch(error => {
                Swal.fire({
                    icon: 'error',
                    title: 'Error!',
                    text: 'An error occurred. Please check the console for details.',
                });
                console.error("An error occurred:", error);
            });
        }
    });
}

// Function to delete a booking
function deleteBooking(bookingId) {
    Swal.fire({
        title: 'Are you sure?',
        text: 'You will not be able to recover this booking!',
        icon: 'warning',
        showCancelButton: true,
        confirmButtonText: 'Yes, delete it!',
        cancelButtonText: 'No, keep it',
    }).then((result) => {
        if (result.isConfirmed) {
            fetch(`http://127.0.0.1:5000/delete/${bookingId}`, {
                method: 'DELETE',
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    Swal.fire({
                        icon: 'success',
                        title: 'Booking Deleted!',
                        text: 'Your booking has been deleted successfully.',
                    });
                    document.getElementById('checkHistoryBtn').click(); // Refresh booking history
                } else {
                    Swal.fire({
                        icon: 'error',
                        title: 'Error!',
                        text: data.error || 'An error occurred while deleting the booking.',
                    });
                }
            })
            .catch(error => {
                Swal.fire({
                    icon: 'error',
                    title: 'Error!',
                    text: 'An error occurred. Please check the console for details.',
                });
                console.error("An error occurred:", error);
            });
        }
    });
}

// Generate PDF Report button functionality
document.getElementById('generateReportBtn').addEventListener('click', function() {
    const userName = localStorage.getItem('userName');
    const ID = localStorage.getItem('ID');

    if (!userName || !ID) {
        Swal.fire({
            icon: 'error',
            title: 'No Booking History!',
            text: 'No booking history found to generate report.',
        });
        return;
    }

    // Fetch booking history for the user
    fetch(`http://127.0.0.1:5000/bookings?userName=${userName}&ID=${ID}`)
        .then(response => response.json())
        .then(data => {
            if (data.success && data.bookings.length > 0) {
                generatePDFReport(data.bookings, userName);
            } else {
                Swal.fire({
                    icon: 'error',
                    title: 'No Bookings!',
                    text: 'No bookings found to generate report.',
                });
            }
        })
        .catch(error => {
            Swal.fire({
                icon: 'error',
                title: 'Error!',
                text: 'An error occurred while fetching booking history for report.',
            });
            console.error("Report generation error:", error);
        });
});

// Function to generate PDF report
function generatePDFReport(bookings, userName) {
    const { jsPDF } = window.jspdf;
    const doc = new jsPDF();

    // Title and Header Info
    doc.setFontSize(20);
    doc.text('Tour Booking Summary Report', 105, 20, { align: 'center' });

    doc.setFontSize(14);
    doc.text(`User: ${userName}`, 14, 30);

    const today = new Date();
    doc.text(`Report Date: ${today.toLocaleDateString()}`, 14, 40);

    let yPosition = 50;

    bookings.forEach((booking, index) => {
        const adults = parseInt(booking.adults) || 0;
        const c1 = parseInt(booking.children1to5) || 0;
        const c2 = parseInt(booking.children6to11) || 0;
        const totalGuests = adults + c1 + c2;
        const duration = calculateDuration(booking.arrivalDate, booking.departureDate);

        // Booking Header
        doc.setFontSize(12);
        doc.text(`Booking ${index + 1}`, 14, yPosition);
        yPosition += 6;

        // Tour Dates Table
        doc.autoTable({
            startY: yPosition,
            head: [['Tour Dates', '']],
            body: [
                ['Arrival Date', booking.arrivalDate || "N/A"],
                ['Departure Date', booking.departureDate || "N/A"],
                ['Total Duration', duration]
            ],
            theme: 'striped',
            headStyles: { fillColor: [52, 152, 219] }
        });

        yPosition = doc.lastAutoTable.finalY + 5;

        // Guest Info Table
        doc.autoTable({
            startY: yPosition,
            head: [['Guest Information', '']],
            body: [
                ['Number of Adults', adults],
                ['Children (1–5)', c1],
                ['Children (6–11)', c2],
                ['Total Guests', totalGuests]
            ],
            theme: 'striped',
            headStyles: { fillColor: [46, 204, 113] }
        });

        yPosition = doc.lastAutoTable.finalY + 5;

        // Tour Details Table
        doc.autoTable({
            startY: yPosition,
            head: [['Tour Details', '']],
            body: [
                ['Culture Category', booking.cultureCategory || "N/A"],
                ['Tour Preference', booking.tourPreferences || "N/A"]
            ],
            theme: 'striped',
            headStyles: { fillColor: [155, 89, 182] }
        });

        yPosition = doc.lastAutoTable.finalY + 10;

        // Add page break if needed
        if (yPosition > 250) {
            doc.addPage();
            yPosition = 20;
        }
    });

    // Save PDF
    const filename = `Booking_Report_${userName}_${today.toISOString().split('T')[0]}.pdf`;
    doc.save(filename);

    // SweetAlert (optional)
    if (window.Swal) {
        Swal.fire({
            icon: 'success',
            title: 'Report Generated!',
            text: 'Your booking report has been downloaded as PDF.',
        });
    }
}

// Helper function to calculate duration
function calculateDuration(arrival, departure) {
    const start = new Date(arrival);
    const end = new Date(departure);
    if (isNaN(start) || isNaN(end)) return "N/A";
    const diffTime = Math.abs(end - start);
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    return `${diffDays} Days`;
}

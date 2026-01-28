// ===== CONSTANTS =====
const DAYS_OF_WEEK = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
const MONTH_VIEW = 'month';
const DAY_VIEW = 'day';

// ===== STATE VARIABLES =====
let currentYear,
	currentMonth,
	currentDay,
	currentView = MONTH_VIEW,
	showingCalendar = false;

// ===== UTILITY FUNCTIONS =====

/**
 * Format date as YYYY-MM-DD
 * @param {number} year - The year
 * @param {number} month - The month (0-11)
 * @param {number} day - The day (1-31)
 * @return {string} Formatted date string
 */
function formatDate(year, month, day) {
	return `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
}

/**
 * Sort events by time (in chronological order), then by title (A-Z)
 * @param {object[]} events - Array of event objects with 'time' and 'title' properties
 * @returns Sorted array of events
 */
function sortEvents(events) {
	return events.sort((a, b) => {
		if (a.time === b.time) {
			return a.title.localeCompare(b.title);
		}
		if (!a.time) return 1;
		if (!b.time) return -1;
		return a.time.localeCompare(b.time);
	});
}

/**
 * Map events by date for quick access
 * @param {object[]} events - Array of event objects with 'date' property
 * @returns Map of dates to arrays of events
 */
function createEventMap(events) {
	const eventMap = {};
	events.forEach((ev) => {
		if (!eventMap[ev.date]) eventMap[ev.date] = [];
		eventMap[ev.date].push(ev);
	});
	return eventMap;
}

/**
 * Set the current day for the next day view.
 * If the current month is not this month, set currentDay to the first of the month.
 * If the current month is this month, set currentDay to today.
 */
function setDayForNextDayView() {
	if (
		currentMonth !== new Date().getMonth() ||
		currentYear !== new Date().getFullYear()
	) {
		currentDay = 1;
	} else {
		currentDay = new Date().getDate();
	}
}

// ===== CALENDAR GENERATION FUNCTIONS =====

/**
 * Generate HTML for the calendar table header (the days of the week from Sunday to Saturday)
 * @returns {string} HTML string for the calendar table header
 */
function generateTableHeader() {
	let html = '<thead><tr>';
	DAYS_OF_WEEK.forEach((day) => (html += `<th>${day}</th>`));
	html += '</tr></thead>';
	return html;
}

/**
 * Create empty table cells to fill the calendar grid, ensuring that the first of the month starts on the correct day of the week
 * and that the grid is complete.
 * @param {number} count - Number of empty cells to generate
 * @returns Generated HTML string for empty cells
 */
function generateEmptyCells(count) {
	let html = '';
	for (let i = 0; i < count; i++) html += '<td></td>';
	return html;
}

/**
 * Check if the given date is today
 * @param {number} year - The year
 * @param {number} month - The month (0-11)
 * @param {number} day - The day (1-31)
 * @returns True if the date is today, false otherwise
 */
function isToday(year, month, day) {
	const today = new Date();
	return (
		today.getFullYear() === year &&
		today.getMonth() === month &&
		today.getDate() === day
	);
}

/**
 * Generate a single day cell in the calendar, including the day number and any events for that day.
 * The cell will be styled differently if it is today or if it has events.
 * @param {number} year - The year
 * @param {number} month - The month (0-11)
 * @param {number} day - The day (1-31)
 * @param {object.<object, object>} eventMap - Map of dates to arrays of events
 * @returns Generated HTML string for the day cell
 */
function generateDayCell(year, month, day, eventMap) {
	const dateStr = formatDate(year, month, day);
	const dayEvents = sortEvents(eventMap[dateStr] || []);

	let style = '';
	if (isToday(year, month, day))
		style += 'background: #e0f7fa; font-weight:bold;';
	if (dayEvents.length) style += 'border: 2px solid #2185d0;';

	let html = `<td${style ? ` style="${style}"` : ''} data-date="${dateStr}">`;
	html += `<div class="calendar-day-number">${day}</div>`;
	dayEvents.forEach((ev) => {
		html += `<div class="month-calendar-event" data-event-id="${ev.id}" title="${ev.title}">
            <button class="ui icon button calendar-event-edit-btn" title="Edit Event"><i class="pencil alternate icon"></i></button>
            <button class="ui red icon button calendar-event-delete-btn" title="Delete Event"><i class="trash icon"></i></button>
            ${ev.title}
            </div>`;
	});
	html += '</td>';
	return html;
}

/**
 * Generate the HTML for the month view calendar of a given month and year, including the header,
 * empty cells before the first day, and cells for each day of the month.
 * It also includes the events for each day, if any.
 * @param {number} year - The year
 * @param {number} month - The month (0-11)
 * @param {number} eventMap - Map of dates to arrays of events
 * @returns Generated HTML string for the month view calendar
 */
function generateMonthView(year, month, eventMap) {
	const firstDay = new Date(year, month, 1);
	const lastDay = new Date(year, month + 1, 0);

	let html = '<table class="ui celled table calendar-table">';
	html += generateTableHeader();
	html += '<tbody><tr>';

	// Fill empty cells before the first day of the month
	html += generateEmptyCells(firstDay.getDay());

	// Generate cells for each day of the month
	for (let day = 1; day <= lastDay.getDate(); day++) {
		html += generateDayCell(year, month, day, eventMap);
		if ((firstDay.getDay() + day) % 7 === 0) html += '</tr><tr>';
	}

	// Fill empty cells after the last day of the month
	const lastCell = (firstDay.getDay() + lastDay.getDate()) % 7;
	if (lastCell !== 0) html += generateEmptyCells(7 - lastCell);

	html += '</tr></tbody></table>';
	html =
		`<h3 class="ui header" style="text-align:center">${firstDay.toLocaleString('default', { month: 'long' })} ${year}</h3>` +
		html;
	return html;
}

/**
 * Generate the HTML for the day view calendar of a given date, including the date as a header.
 * It also includes the events for each day, if any.
 * @param {number} year - The year
 * @param {number} month - The month (0-11)
 * @param {number} day - The day (1-31)
 * @param {object.<object, object>} eventMap - Map of dates to arrays of events
 * @returns
 */
function generateDayView(year, month, day, eventMap) {
	const dateStr = formatDate(year, month, day);
	const dayEvents = sortEvents(eventMap[dateStr] || []);
	const viewDate = new Date(year, month, day);

	let html = `<h3 class="ui header" style="text-align:center">${viewDate.toLocaleString('default', { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' })}</h3>`;
	html += '<div class="ui segments">';

	if (dayEvents.length === 0) {
		html +=
			'<div class="ui segment"><p>No events scheduled for this day.</p></div>';
	} else {
		dayEvents.forEach((event) => {
			html += `<div class="ui segment day-calendar-event" data-event-id="${event.id}">
            <button class="ui icon button calendar-event-edit-btn" title="Edit Event"><i class="pencil alternate icon"></i></button>
            <button class="ui red icon button calendar-event-delete-btn" title="Delete Event"><i class="trash icon"></i></button>
            <div class="ui small header">${event.is_all_day ? 'All Day' : event.time}</div>
            <p>${event.title}</p>
            </div>`;
		});
	}

	html += '</div>';
	return html;
}

// ===== EVENT DELETION FUNCTIONS =====

/**
 * Handle the deletion of an event via AJAX
 * @param {string} eventId - The ID of the event to delete
 */
function deleteEventFromDatabase(eventId) {
	fetch(`/delete/${eventId}`, { method: 'GET' })
		.then((response) => {
			if (response.ok) {
				removeEventFromCalendarViews(eventId);
				removeEventFromListView(eventId);
				renderView();
			} else {
				showErrorNotification();
			}
		})
		.catch((error) => showErrorNotification());
}

/**
 * Removes an event from Calendar views by removing it from the events array (defined in home.html script tag)
 * @param {string} eventId - The ID of the event to remove
 */
function removeEventFromCalendarViews(eventId) {
	const index = events.findIndex((event) => event.id === eventId);
	if (index !== -1) {
		events.splice(index, 1);
	}
}

/**
 * Removes an event from the List view by removing the corresponding HTML element.
 * @param {string} eventId - The ID of the event to remove
 */
function removeEventFromListView(eventId) {
	const listView = document.getElementById('list-view');
	if (listView) {
		const eventElement = listView.querySelector(
			`.list-event[data-event-id="${eventId}"]`,
		);
		if (eventElement) {
			eventElement.remove();
		}
	}
}

function getEventDataById(eventId) {
	const eventsData = typeof events !== 'undefined' ? events : [];
	return eventsData.find((event) => event.id === eventId);
}

function openEditDialog(eventData) {
	const dialog = document.getElementById('edit-dialog');
	const eventIdInput = document.getElementById('edit-event-id');
	const titleInput = document.getElementById('edit-title');
	const dateInput = document.getElementById('edit-date');
	const timeInput = document.getElementById('edit-time');
	if (!dialog || !eventIdInput || !titleInput || !dateInput || !timeInput) {
		return;
	}
	eventIdInput.value = eventData.id || '';
	titleInput.value = eventData.title || '';
	dateInput.value = eventData.date || '';
	timeInput.value = eventData.is_all_day ? '' : eventData.time || '';
	if (typeof dialog.showModal === 'function') {
		dialog.showModal();
	} else {
		dialog.setAttribute('open', 'open');
	}
}

function setupEditDialog() {
	const dialog = document.getElementById('edit-dialog');
	const cancelButton = document.getElementById('edit-cancel-btn');
	if (!dialog || !cancelButton) {
		return;
	}
	cancelButton.addEventListener('click', function () {
		dialog.close();
	});
	dialog.addEventListener('click', function (event) {
		if (event.target === dialog) {
			dialog.close();
		}
	});
}

// ===== EVENT SELECTION FUNCTIONS =====

/**
 * Select an event element and show the delete button
 * @param {HTMLElement} eventElement - The event element to select
 */
function selectEvent(eventElement) {
	clearEventSelection();
	eventElement.classList.add('selected-event');
	// Showing the delete button is handled in CSS
}

/**
 * Clear the current event selection and remove the delete button
 */
function clearEventSelection() {
	const selectedEvent = document.querySelector('.selected-event');
	if (selectedEvent) {
		selectedEvent.classList.remove('selected-event');
	}
	// Hiding the delete button is handled in CSS
}

// ===== RENDERING FUNCTIONS =====

/**
 * Render the current view of the calendar based on the selected view (month or day).
 * It generates the HTML for the calendar and updates the container element.
 */
function renderView() {
	const container = document.getElementById('calendar-container');
	const eventsData = typeof events !== 'undefined' ? events : [];
	const eventMap = createEventMap(eventsData);

	if (currentView === MONTH_VIEW) {
		container.innerHTML = generateMonthView(
			currentYear,
			currentMonth,
			eventMap,
		);
		addDayDoubleClickListeners();
	} else {
		container.innerHTML = generateDayView(
			currentYear,
			currentMonth,
			currentDay,
			eventMap,
		);
	}

	updateMonthDayToggleButton();
	addEventClickListeners();
	addDeleteEventListeners();
	addEditEventListeners();
}

/**
 * Update the text of the month/day toggle button based on the current view.
 * If the current view is month, it shows "Switch to Day View", otherwise it shows "Switch to Month View".
 */
function updateMonthDayToggleButton() {
	const btn = document.getElementById('toggle-month-day-btn');
	if (btn) {
		btn.textContent =
			currentView === MONTH_VIEW
				? 'Switch to Day View'
				: 'Switch to Month View';
	}
}

/**
 * Show or hide the month/day toggle button based on whether the calendar is being displayed.
 * If the calendar is being shown, the button is displayed; otherwise (i.e., if in list view), it is hidden.
 */
function showHideMonthDayToggleButton() {
	const monthDayBtn = document.getElementById('toggle-month-day-btn');
	if (showingCalendar) {
		monthDayBtn.style.display = '';
	} else {
		monthDayBtn.style.display = 'none';
	}
}

/**
 * Show an error notification if an error occurs when processing the user's request.
 * This function is called when an error occurs during event deletion.
 */
function showErrorNotification() {
	const errorNotification = document.getElementById('error-notification');
	if (errorNotification) {
		errorNotification.classList.add('show');
	}
}

/**
 * Hide the error notification when the user clicks on the "x" button.
 */
function hideErrorNotification() {
	const errorNotification = document.getElementById('error-notification');
	if (errorNotification) {
		errorNotification.classList.remove('show');
	}
}

// ===== NAVIGATION FUNCTIONS =====

/**
 * Navigate to the next month in the calendar.
 * It updates the current day, month, and year, and re-renders the calendar view.
 */
function navigateToNextMonth() {
	currentMonth++;
	if (currentMonth > 11) {
		currentMonth = 0;
		currentYear++;
	}
	setDayForNextDayView();
	renderView();
}

/**
 * Navigate to the previous month in the calendar.
 * It updates the current day, month, and year, and re-renders the calendar view.
 */
function navigateToPreviousMonth() {
	currentMonth--;
	if (currentMonth < 0) {
		currentMonth = 11;
		currentYear--;
	}
	setDayForNextDayView();
	renderView();
}

/**
 * Navigate to the previous day in the calendar.
 * It updates the current day, month, and year, and re-renders the calendar view.
 */
function navigateToPreviousDay() {
	const prevDay = new Date(currentYear, currentMonth, currentDay - 1);
	currentYear = prevDay.getFullYear();
	currentMonth = prevDay.getMonth();
	currentDay = prevDay.getDate();
	renderView();
}

/**
 * Navigate to the next day in the calendar.
 * It updates the current day, month, and year, and re-renders the calendar view.
 */
function navigateToNextDay() {
	const nextDay = new Date(currentYear, currentMonth, currentDay + 1);
	currentYear = nextDay.getFullYear();
	currentMonth = nextDay.getMonth();
	currentDay = nextDay.getDate();
	renderView();
}

// ===== EVENT HANDLERS =====

/**
 * Add double-click listeners to each day cell in the calendar.
 * When a day cell is double-clicked, it switches to the day view for that date
 */
function addDayDoubleClickListeners() {
	const dayCells = document.querySelectorAll('.calendar-table td[data-date]');
	dayCells.forEach((cell) => {
		cell.addEventListener('dblclick', function () {
			const dateStr = this.getAttribute('data-date');
			const [year, month, day] = dateStr.split('-').map(Number);
			currentYear = year;
			currentMonth = month - 1;
			currentDay = day;
			currentView = DAY_VIEW;
			renderView();
		});
	});
}

/**
 * Add a toggle button to switch between list view and calendar view.
 * The button toggles the visibility of the list view and calendar view sections.
 * It also updates the button text and visibility of the month/day toggle button.
 */
function addListCalendarToggle() {
	const btn = document.getElementById('toggle-view-btn');
	const monthDayBtn = document.getElementById('toggle-month-day-btn');
	const listView = document.getElementById('list-view');
	const calendarView = document.getElementById('calendar-view');

	btn.addEventListener('click', function () {
		showingCalendar = !showingCalendar;
		if (showingCalendar) {
			listView.style.display = 'none';
			calendarView.style.display = '';
			btn.textContent = 'Switch to List View';
		} else {
			listView.style.display = '';
			calendarView.style.display = 'none';
			btn.textContent = 'Switch to Calendar View';
		}
		showHideMonthDayToggleButton();
	});
}

/**
 * Add a toggle button to switch between month view and day view.
 * The button toggles the current view and updates the calendar display accordingly.
 */
function addMonthDayToggle() {
	const btn = document.getElementById('toggle-month-day-btn');
	btn.addEventListener('click', function () {
		if (currentView === MONTH_VIEW) {
			currentView = DAY_VIEW;
		} else {
			currentView = MONTH_VIEW;
			setDayForNextDayView();
		}
		renderView();
	});
}

/**
 * Add event listeners for the previous navigation button.
 * This button allows the user to navigate to the previous month or day based on the current view.
 */
function addPreviousNavigationListener() {
	document.getElementById('prev-btn').addEventListener('click', function () {
		if (currentView === MONTH_VIEW) {
			navigateToPreviousMonth();
		} else if (currentView === DAY_VIEW) {
			navigateToPreviousDay();
		}
	});
}

/**
 * Add event listeners for the next navigation button.
 * This button allows the user to navigate to the next month or day based on the current view.
 */
function addNextNavigationListener() {
	document.getElementById('next-btn').addEventListener('click', function () {
		if (currentView === MONTH_VIEW) {
			navigateToNextMonth();
		} else if (currentView === DAY_VIEW) {
			navigateToNextDay();
		}
	});
}

/**
 * Add click listeners to event elements in both month and day calendar views.
 */
function addEventClickListeners() {
	const eventElements = document.querySelectorAll(
		'.month-calendar-event, .day-calendar-event',
	);
	eventElements.forEach((element) => {
		element.addEventListener('click', function (event) {
			event.stopPropagation();
			selectEvent(event.currentTarget);
		});
	});

	// Add click listener to document to clear selection when clicking elsewhere
	document.addEventListener('click', function (event) {
		if (
			!event.target.closest('.selectable-event') &&
			!event.target.closest('#event-delete-btn')
		) {
			clearEventSelection();
		}
	});
}

/**
 * Add event listeners to delete buttons for calendar events.
 * When a delete button is clicked, the eventID of the associated event is retrieved and
 * passed to the deleteEventFromDatabase function.
 */
function addDeleteEventListeners() {
	const deleteButtons = document.querySelectorAll('.calendar-event-delete-btn');
	deleteButtons.forEach((button) => {
		button.addEventListener('click', function (event) {
			event.stopPropagation();
			const eventElement = event.target.closest(
				'.month-calendar-event, .day-calendar-event',
			);
			if (eventElement) {
				const eventId = eventElement.getAttribute('data-event-id');
				deleteEventFromDatabase(eventId);
			}
		});
	});
}

function addEditEventListeners() {
	const editButtons = document.querySelectorAll('.calendar-event-edit-btn');
	editButtons.forEach((button) => {
		button.addEventListener('click', function (event) {
			event.stopPropagation();
			const eventElement = event.target.closest(
				'.month-calendar-event, .day-calendar-event',
			);
			if (eventElement) {
				const eventId = eventElement.getAttribute('data-event-id');
				const eventData = getEventDataById(eventId);
				if (eventData) {
					openEditDialog(eventData);
				}
			}
		});
	});
}

function addListEditListeners() {
	const editButtons = document.querySelectorAll('.edit-list-btn');
	editButtons.forEach((button) => {
		button.addEventListener('click', function (event) {
			event.preventDefault();
			const eventElement = button.closest('.list-event');
			if (!eventElement) {
				return;
			}
			const eventData = {
				id: eventElement.getAttribute('data-event-id'),
				title: eventElement.getAttribute('data-title'),
				date: eventElement.getAttribute('data-date'),
				time: eventElement.getAttribute('data-time'),
			};
			openEditDialog(eventData);
		});
	});
}

// ===== INITIALIZATION =====

/**
 * Initialize the calendar with the current date and render the initial view of the calendar (today's month)
 */
function initializeCalendar() {
	const now = new Date();
	currentYear = now.getFullYear();
	currentMonth = now.getMonth();
	currentDay = now.getDate();
	renderView();
}

document.addEventListener('DOMContentLoaded', function () {
	addListCalendarToggle();
	addMonthDayToggle();
	showHideMonthDayToggleButton();
	initializeCalendar();
	addPreviousNavigationListener();
	addNextNavigationListener();
	setupEditDialog();
	addListEditListeners();
});

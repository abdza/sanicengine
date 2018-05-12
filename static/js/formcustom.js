function initfields() {
	// date picker
	$('.date-picker').datepicker({
		language: 'en',
		autoClose: true,
		dateFormat: 'yyyy-mm-dd',
	});
	$('.datetimepicker').datepicker({
		timepicker: true,
		language: 'en',
		autoClose: true,
		dateFormat: 'yyyy-mm-dd',
		timeFormat: 'hh:ii'
	});
	$('.datetimepicker-range').datepicker({
		language: 'en',
		range: true,
		multipleDates: true,
		multipleDatesSeparator: " - "
	});
	$('.month-picker').datepicker({
		language: 'en',
		minView: 'months',
		view: 'months',
		autoClose: true,
		dateFormat: 'yyyy-mm',
	});
	// only time picker
	$( ".time-picker" ).timeDropper({
		mousewheel: true,
		meridians: true,
		init_animation: 'dropdown',
		setCurrentTime: false
	});
	$('.time-picker-default').timeDropper();
}
initfields();

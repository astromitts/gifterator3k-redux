function toggleElementClass(element) {
	if (element.hasClass('default-hidden')) {
		element.removeClass('default-hidden');
	} else {
		element.addClass('default-hidden');
	}
}

function toggleElementText(element) {
	var expandedText = element.attr('data-expanded-text');
	var collapsedText = element.attr('data-collapsed-text');
	if ( expandedText != undefined ) {
		if ( element.html() != expandedText ) {
			element.html(expandedText);
		} else {
			element.html(collapsedText);
		}
	}
}

function bindToggleButtons() {
	$('.js-expand-collapse-toggle').click(function doToggle(){
		toggleElementText($(this));
		var showTarget = $($(this).attr('data-show-target'));
		if ( showTarget.length > 1 ) {
			showTarget.each(function toggleElement() {
				toggleElementClass($(this));
			});
		} else {
			toggleElementClass(showTarget);
		}
		var hideTarget = $(this).attr('data-hide-target');
		if ( hideTarget != undefined ) {
			hideTarget.addClass('default-hidden');
		}
	});
}

$(document).ready(function setUpPage(){
	bindToggleButtons();
});
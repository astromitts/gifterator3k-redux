function doSynchedPost(targetUrl, postData) {
	var resultData;
	showLoader();
	$.ajax({
		method: 'POST',
		url: targetUrl,
		dataType: 'json',
		data: postData,
		async: false,
		success: function successFunction(data) {
			resultData = data;
		}
	});
	setTimeout(function () {
		hideLoader();
    }, 500);
	return resultData;
}

function doSynchedGet(targetUrl) {
	var resultData;
	showLoader();
	$.ajax({
		method: 'GET',
		url: targetUrl,
		dataType: 'json',
		async: false,
		success: function successFunction(data) {
			resultData = data;
		}
	});
	
	setTimeout(function () {
		hideLoader();
    }, 500);
	return resultData;
}


function bindUpdateDetails(apiTargetUrl) {
	var postResult;
	$('input#id_update-details').click(function updateDetails(event) {
		event.preventDefault();
		postData = $(this).closest('form').serialize();
		postResult = doSynchedPost(apiTargetUrl, postData);
		if (postResult.status == 'success') {
			successMessage(postResult.message);
			refreshDashoardTools(postResult.giftExchange);
		} else {
			errorMessage(postResult.message);
		}
	});
}

function bindRemoveUser(apiTargetUrl) {
	var postResult;
	$('input.js-remove-user').click(function removeUser(event){
		event.preventDefault();
		postData = $(this).closest('form').serialize();
		postResult = doSynchedPost(apiTargetUrl, postData);
		if (postResult.status == 'success') {
			$(this).closest('tr').remove();
			refreshDashoardTools(postResult.giftExchange);
		} else {
			errorMessage(postResult.message);
		}
	});	
}

function bindAddFromSearch(apiTargetUrl) {
	var postResult;
	$('input.js-add-user').click(function addUser(event){
		event.preventDefault();
		postData = $(this).closest('form').serialize();
		postResult = doSynchedPost(apiTargetUrl, postData);
		if (postResult.status == 'success') {
			$('div#participant-list').html(postResult.html);
			bindRemoveUser(apiTargetUrl);
			$(this).closest('tr').remove();
			refreshDashoardTools(postResult.giftExchange);
			if (PREVIEW_EMAILS_IN_APP == 'True') {
				window.open(postResult.postProcessUrl, '_blank');
			}
		} else {
			errorMessage(postResult.message);
		}
	});
}


function bindEmailSearch(apiTargetUrl) {
	var postResult;
	$('input#id_email-search').click(function doUserSearch(event) {
		event.preventDefault();
		postData = $(this).closest('form').serialize();
		postResult = doSynchedPost(apiTargetUrl, postData);
		if (postResult.status == 'success') {
			$('div#search-results').html(postResult.html);
			bindAddFromSearch(apiTargetUrl);
			refreshDashoardTools(postResult.giftExchange);
		} else {
			errorMessage(postResult.message);
		}
	});
}


function bindAssignmentsFunctions(apiTargetUrl) {
	var postResult;
	$('input.js-assignment-control').click(function doAssignmentAction(event){
		event.preventDefault();
		postData = $(this).closest('form').serialize();
		postResult = doSynchedPost(apiTargetUrl, postData);
		if (postResult.status == 'success') {
			if ( postResult.html ) {
				$('div#assignment-list').html(postResult.html);
				bindSendSingleSend(apiTargetUrl);
			}
			refreshDashoardTools(postResult.giftExchange);
		} else {
			errorMessage(postResult.message);
		}
	});
}

function bindSendSingleSend(apiTargetUrl) {
	var postResult;
	$('input.js-single-notify').click(function notifyUser(event){
		event.preventDefault();
		postData = $(this).closest('form').serialize();
		postResult = doSynchedPost(apiTargetUrl, postData);
		if (postResult.status == 'success') {
			$('div#assignment-list').html(postResult.html);
			bindSendSingleSend(apiTargetUrl);
			refreshDashoardTools(postResult.giftExchange);
		} else {
			errorMessage(postResult.message);
		}
	});	
}

function disableDetailForm() {
	var detailsForm = $('div#details-form').find('form');
	detailsForm.find('input').each( function disableField(){
		$(this).prop('disabled', true);
	});
	detailsForm.find('textarea').each( function enableField(){
		$(this).prop('disabled', true);
	});
}

function enableDetailForm() {
	var detailsForm = $('div#details-form').find('form');
	detailsForm.find('input').each( function enableField(){
		$(this).removeAttr('disabled');
	});
	detailsForm.find('textarea').each( function enableField(){
		$(this).removeAttr('disabled');
	});
}

function bindSendBulkMessage(apiTargetUrl) {
	$('button#js-send-bulk-message').click(function sendBulkMessage(){
		var postData = $('form#send_bulk_message').serialize();
		postResult = doSynchedPost(apiTargetUrl, postData);
		if (postResult.status == 'success') {
			successMessage(postResult.successMessage);
			$('#modal_send-participant-message').modal('hide');
		}
	});
}

function bindModalOpen() {
	$('a.js-modal-trigger').click(function showModal(event){
		event.preventDefault();
		var modalId = 'modal_' + $(this).attr('id');
		$('#' + modalId).modal('show');
	});
}

function hide(element) {
	element.addClass('default-hidden');
}
function show(element) {
	element.removeClass('default-hidden');
}

function refreshDashoardTools(giftExchange) {
	if( giftExchange.participantsNotified ) {
		show($('div#notify-participants-alert'));
		show($('div.resend-assignment'));
		show($('div#assignment-list'));
		hide($('div#notify-participants'));
		hide($('div#id_search-users'));
		hide($('input#id_set-assignments'));
		hide($('div#participant-list'));
		hide($('input#id_unset-assignments'));
		hide($('input#id_lock-assignments'));
	} else if ( giftExchange.hasAssignments ) {
		show($('div#assignment-list'));
		show($('input#id_unset-assignments'));
		hide($('div#id_search-users'));
		hide($('div#participant-list'));
		$('input#id_set-assignments').val('Re-set Assignments');
		if ( giftExchange.locked ) {
			// disableDetailForm();
			hide($('input#id_set-assignments'));
			hide($('input#id_lock-assignments'));
			show($('div#notify-participants'));
		} else {
			// enableDetailForm();
			show($('input#id_unset-assignments'));
			show($('input#id_lock-assignments'));
			hide($('div#notify-participants'));
		}
	} else {
		// enableDetailForm();
		if ( giftExchange.participantCount >= 3 ) {
			show($('input#id_set-assignments'));
			hide($('div#notify-participant-count'));
		} else {
			hide($('input#id_set-assignments'));
			show($('div#notify-participant-count'));
		}
		show($('div#id_search-users'));
		show($('div#participant-list'));
		hide($('div#notify-participants'));
		hide($('div#notify-participants-alert'));
		hide($('div#assignment-list'));
		hide($('input#id_unset-assignments'));
		hide($('input#id_lock-assignments'));
		$('input#id_set-assignments').val('Set Assignments');
	}
}

function setUpDashboard(apiTargetUrl) {
	getResult = doSynchedGet(apiTargetUrl);
	refreshDashoardTools(getResult.giftExchange);
}


$(document).ready(function(){
	var apiTargetUrl = $('input#post-url').val();
	bindUpdateDetails(apiTargetUrl);
	bindEmailSearch(apiTargetUrl);
	bindRemoveUser(apiTargetUrl);
	bindAssignmentsFunctions(apiTargetUrl);
	bindSendSingleSend(apiTargetUrl);
	setUpDashboard(apiTargetUrl);
	bindModalOpen();
	bindSendBulkMessage(apiTargetUrl);
});
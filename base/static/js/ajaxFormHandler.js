function bindAjaxFormSubmit(form_id) {
	$('form#' + form_id).submit(function(event){
		event.preventDefault()
		var submitUrl = $(this).attr('action');
		var reloadUrl = $('input#id_submit_done_url').val();
		doASynchedPost(
	        submitUrl,
	        $(this).serialize(),
	        function handleFormSubmitOutcome(submitData) {
	        	if (submitData.status == 'success') {
	        		if (reloadUrl) {
	        			window.location.href = reloadUrl;
	        		}
	        	} else {
	        		errorMessage(submitData.message);
	        	}
	        },
	    );
	});
}

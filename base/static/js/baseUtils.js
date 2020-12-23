function doSynchedPost(targetUrl, postData) {
	var resultData;
	$.ajax({
		method: 'POST',
		url: targetUrl,
		dataType: 'json',
		data: postData,
		async: false,
		beforeSend: function(){
			$('div#loader').removeClass('default-hidden');
		},
		success: function successFunction(data) {
			resultData = data;
			setTimeout(function () {
				$('div#loader').addClass('default-hidden');
		    }, 500);
		},
		error: function errorFunction(data) {
			setTimeout(function () {
				$('div#loader').addClass('default-hidden');
		    }, 500);
		}
	});
	return resultData;
}

function doASynchedPost(targetUrl, postData, callBack) {
	$.ajax({
		method: 'POST',
		url: targetUrl,
		dataType: 'json',
		data: postData,
		beforeSend: function(){
			showLoader();
		},
		success: function successFunction(data) {
			callBack(data);
			hideLoader();
		},
		error: function errorFunction(data) {
			
			hideLoader();
		}
	});
}

function doASynchedGet(targetUrl, callBack) {
	$.ajax({
		method: 'GET',
		url: targetUrl,
		dataType: 'json',
		beforeSend: function(){
			showLoader();
		},
		success: function successFunction(data) {
			callBack(data);
			hideLoader();
		},
		error: function errorFunction(data) {
			
			hideLoader();
		}
	});
}

function doSynchedGet(targetUrl) {
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
	return resultData;
}

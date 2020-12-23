
function fetchSiteMeta(targetUrl) {
    var getData = doASynchedPost(
        '/tools/metadatafetcher/',
        {'targetUrl': targetUrl},
        fillForm,
    );
    return getData;
}

function fillForm(siteData) {
	$('input#id_nickname').val(siteData.title);
	$('textarea#id_description').val(siteData.description);
	$('input#id_web_link').val(siteData.url);
}

function bindGetLinkData() {
	$('input#id_web_link').change(function(){
		if ($(this).val().length > 0 ){
			showLoader();
			var siteData = fetchSiteMeta($(this).val());
		} else {
			$('input#id_nickname').val('');
			$('textarea#id_description').val('');
			$('input#id_web_link').val('');
		}
	});
}

$(document).ready(function(){
	bindGetLinkData();
});

function showMessage(message, type) {
/*
	<div id="js-alert" class="alert alert-dismissible fade show" role="alert">
	 	<strong><span id="message-body"></span></strong>
	 	<button type="button" class="close" data-dismiss="alert" aria-label="Close">
	 	<span aria-hidden="true">&times;</span>
	</div>

*/
	var messageDiv = document.createElement('div');
	messageDiv.setAttribute('id', 'js-alert')
	messageDiv.setAttribute('class', 'alert alert-dismissible fade show alert-' + type);
	messageDiv.innerHTML = '<strong>' + message + '</strong>';
	messageDiv.innerHTML = messageDiv.innerHTML + '<button class="close float-right" data-dismiss="alert" aria-label="Close">X</button>';

	var messagesCol = document.getElementById('js-messages-col');
	messagesCol.append(messageDiv);
	window.scrollTo(0, 0);
}

function errorMessage(message) {
	showMessage(message, 'danger');
}

function warningMessage(message) {
	showMessage(message, 'warning');

}

function successMessage(message) {
	showMessage(message, 'success');

}

function primaryMessage(message) {
	showMessage(message, 'primary');

}
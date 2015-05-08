var defaultReviewWizardStep = ""
var preflightError;


$('#wizard').on('actionclicked.fu.wizard', function (event, data) {
	if (data.step == 2 && data.direction == 'next') {
		validateHypervisors (event);
	}
	if (data.step == 3 && data.direction == 'next') {
		validateNetworkLayout (event);
	}
	if (data.step == 4 && data.direction == 'next') {
		validateLeoConfig (event);
	}
	if (data.step == 5 && data.direction == 'next') {
		validateVMSecurityConfig (event);
		defaultReviewWizardStep = $("#defaultReviewWizardStep").html();
	}
	if (data.step == 6 && data.direction == 'previous') {
		$('#wizardButtonNext').show();
		$("#defaultReviewWizardStep").html(defaultReviewWizardStep);
	}
	if (data.step == 6 && data.direction == 'next') {
		setTimeout(function () {
			l = window.location
			window.webSocket = new WebSocket("ws://" + l.hostname + ":9010");
			window.webSocket.onmessage = function(e) {
				newtext = ansispan(e.data.replace(/(?:\r\n|\r|\n)/g, '<br />'));
        $("#leash-log-viewer").append(newtext);
				var objDiv = document.getElementById("leash-log-viewer");
				objDiv.scrollTop = objDiv.scrollHeight;
      }
			set_vm_keys();
			run_install();
		}, 500);
	}

});

function set_hypervisor_keys(){

	if (! $('#radioHyperAuthPassword').radio('isChecked')){
		postData = {
				"type" : "hypervisor_priv",
				"key" :$('#inputHypervisorPrivKey').val()
			};

		$.ajax({
				url: "/api/addKey",
				method: "POST",
				data: postData,
				async: false
			});
	}

}


function set_vm_keys(){

	if ($('#radioToggleNewKeyset').radio('isChecked')){
		postData = {
				"type" : "vm_new"
			};

		$.ajax({
				url: "/api/addKey",
				method: "POST",
				data: postData,
				async: false
			});
	}
	else {

		postData = {
				"type" : "vm_priv",
				"key" :$('#inputKeysetPrivate').val()
			};

		$.ajax({
				url: "/api/addKey",
				method: "POST",
				data: postData,
				async: false
			});

		postData = {
				"type" : "vm_pub",
				"key" :$('#inputKeysetPublic').val()
			};

		$.ajax({
				url: "/api/addKey",
				method: "POST",
				data: postData,
				async: false
			});

	}




}


function run_install(){
	var hypervisors = $('#hypervisors').pillbox('items');
	var hypervisorsLength = hypervisors.length;
	(function(hyperList, hyperLength){
		hypervisorList = [];
		for (var i = 0; i < hyperLength; i++) {
			hypervisorList.push(hyperList[i].value);
		}
		var postData = {
			hypervisors : hypervisorList,
			leoNodes : $('#inputLeoStorageNodes').val(),
			leoReplicaN : $('#inputLeoConsistancyReplicas').val(),
			leoReplicaR : $('#inputLeoConsistancyReads').val(),
			leoReplicaW : $('#inputLeoConsistancyWrites').val(),
			leoReplicaD : $('#inputLeoConsistancyDeletes').val(),
			adminNetStart : $('#inputAdminNetAssignableStart').val(),
			adminNetEnd : $('#inputAdminNetAssignableEnd').val()
			}


		if ($('#radioHyperAuthPassword').radio('isChecked')){
			postData.password = $('#inputHypervisorPassword').val()
		}

			$.ajax({
					url: "/api/install",
					method: "POST",
					data: postData
				})
				.done(function(data) {
					newContent = ""
					if (data.result == "ok"){
						fifo_ip = $('#inputAdminNetAssignableStart').val()
						newContent =
							'<div> \
									Installation is complete. To access your new Fifo install \
									navigate to ' + fifo_ip + ' and login with admin/admin \
								</div>';
					}
					else{
						newContent = data
					}
					$('#installationProgress').html(newContent);
				})
				.fail(function() {
					newContent =
						'<div> \
								There was an error installing fifo on your system. \
							</div>';
					$('#installationProgress').html(newContent);
				})
				.always(function(){
					window.webSocket = null;
				});
	})(hypervisors, hypervisorsLength);
}


$('#wizard').on('click', '#btnBeginCheck', function () {

	preflightError = false;

	$('#reviewPane').html("<div class='row-fluid'><div class='row-fluid' id='reviewPaneContainer'></div></div><div class=\"clearfix\"></div>");
		set_hypervisor_keys();
		var hypervisors = $('#hypervisors').pillbox('items');
		var hypervisorsLength = hypervisors.length;
		for (var i = 0; i < hypervisorsLength; i++) {
			(function (hypervisor) {
					// Draw panel for each hypervisor
					// make interogation request for each hypervisor
					newContent =
						'<div class="panel panel-info flowable-panel" data-hypervisor="' + hypervisor + '"> \
								<div class="panel-heading"> \
									<h3 class="panel-title">' + hypervisor + '</h3> \
								</div> \
								<div class="panel-body" style="background: #f9f9f9!important;"> \
									<div name="results"> \
									<div class="loader"></div> \
									</div> \
									<hr> \
									<label>Zones to be Created:</label><br /> \
									<div name="vms"></div> \
								</div> \
							</div>';
					$('#reviewPaneContainer').append(newContent);

					$('.loader').loader('play');


					var postData = { "host" : hypervisor };
					if ($('#radioHyperAuthPassword').radio('isChecked')){
						postData.password = $('#inputHypervisorPassword').val()
					}


					setTimeout(function () {
						$.ajax({
							  url: "/api/checkHypervisor",
							  method: "POST",
							  data: postData
							})
							.done(function(data) {
								$("[data-hypervisor='" + hypervisor + "'] [name='results']").html(drawResult(data.disk, data.mem, data.threads, data.has_admin, data.platform_image_ok, data.dns_lookup_ok))
							})
							.fail(function() {
								preflightError = true;
								$("[data-hypervisor='" + hypervisor + "']").removeClass("panel-info");
								$("[data-hypervisor='" + hypervisor + "']").addClass("panel-danger");
								$("[data-hypervisor='" + hypervisor + "'] [name='results']").html("Error running preflight. Please check network communications and credentials.");
							});
						}, 500);
			//		$.post( "/api/checkHypervisor", postData)
					})(hypervisors[i].value);
				}


				(function(hyperList, hyperLength){
					hypervisorList = [];
					for (var i = 0; i < hyperLength; i++) {
						hypervisorList.push(hyperList[i].value);

					}

					postData = {
						hypervisors : hypervisorList,
						leoNodes : $('#inputLeoStorageNodes').val()
						}

					setTimeout(function () {
						$.ajax({
								url: "/api/layoutVMs",
								method: "POST",
								data: postData
							})
							.done(function(data) {
								if (data.placements.length > 0){
									for (var k = 0; k < data.placements.length; k++) {
										for (key in data.placements[k]) {
											$("[data-hypervisor='" + data.placements[k][key] + "'] [name='vms']").append('<span class="label label-default">' + key + '</span> ');
										}
									}
								}
								if (preflightError == false){
									if (data.fifo_zone_count > 1){
									//	$('#reviewPaneContainer').prepend('<div><h5><span class="label label-warning">Note:</span> An additional ' + (data.fifo_zone_count - 1) + ' Fifo zones will be created. Their placement is decided by the default Fifo zone provisioning rules.</h5><br /></div><div class="clearfix"></div>');
									}
									$('#reviewPaneMsg').html(' \
											<h4>Congratulations!</h4> \
											<p>Your system has been verified and is now ready to have Fifo installed. \
											 Please review the information below and when you are ready to install click "Next"</p>');

									$('#wizardButtonNext').show();
								}
							})
							.fail(function() {
								console.log("Failed to create VM layout.");
							});
						}, 500);
				})(hypervisors, hypervisorsLength);




});


//


$('#wizard').on('finished.fu.wizard', function (event, data) {

});


/******
/*
/*	VALIDATION FUNCTIONS
/*
*******/


$("input.pillbox-add-item").on("focusout", function (event) {
	if (event.type == "focusout") {
		var enterkeydown = $.Event("keydown");
		enterkeydown.keyCode = 13; // 13 => <enter>
		$(event.currentTarget).trigger(enterkeydown);
	}
});


function validateHypervisors (event){
	if ($('#hypervisors').pillbox('itemCount') < 1) {
		shakeElement($('#hypervisors'));
		event.preventDefault();
		return;
	}
	var badHypers = false;
	var hypervisors = $('#hypervisors').pillbox('items');
	var hypervisorsLength = hypervisors.length;
	for (var i = 0; i < hypervisorsLength; i++) {
	    if (!validateIPaddress(hypervisors[i].value)){
	    	$('#hypervisors li[data-value="' + hypervisors[i].value + '"]')
	    		.css('border-color', '#ebccd1')
	    		.css('background-color', '#f2dede')
	    		.css('color', '#a94442');
	    		badHypers = true;
	    }
	}
	if (badHypers){
		shakeElement($('#hypervisors'));
		event.preventDefault();
		return;
	}

	if ($('#radioHyperAuthPassword').radio('isChecked') && $('#inputHypervisorPassword').val().length < 1) {
		shakeElement($('#inputHypervisorPassword'));
		event.preventDefault();
		return;
	}
	if ($('#radioHyperAuthSSH').radio('isChecked') && $('#inputHypervisorPrivKey').val().length < 1) {
		shakeElement($('#inputHypervisorPrivKey'));
		event.preventDefault();
		return;
	}
}

function validateNetworkLayout (event){
	if(!validateIPaddress($('#inputAdminNetAssignableStart').val())){
		shakeElement($('#inputAdminNetAssignableStart'));
		event.preventDefault();
		return;
	}
	if(!validateIPaddress($('#inputAdminNetAssignableEnd').val())){
		shakeElement($('#inputAdminNetAssignableEnd'));
		event.preventDefault();
		return;
	}
	if(dot2num($('#inputAdminNetAssignableEnd').val()) <= dot2num($('#inputAdminNetAssignableStart').val())){
		shakeElement($('#inputAdminNetAssignableEnd'));
		event.preventDefault();
		return;
	}
}

function validateLeoConfig (event){

	var replicas = parseInt($('#inputLeoConsistancyReplicas').val());
	var reads = parseInt($('#inputLeoConsistancyReads').val());
	var writes = parseInt($('#inputLeoConsistancyWrites').val());
	var deletes = parseInt($('#inputLeoConsistancyDeletes').val());
	var nodes = parseInt($('#inputLeoStorageNodes').val());


	if(!isInt(replicas) || replicas < 1){
		shakeElement($('#inputLeoConsistancyReplicas'));
		event.preventDefault();
		return;
	}
	if( (!isInt(reads)) || reads < 1 || replicas < reads ){
		shakeElement($('#inputLeoConsistancyReads'));
		event.preventDefault();
		return;
	}
	if( (!isInt(writes)) || writes < 1 || replicas < writes ){
		shakeElement($('#inputLeoConsistancyWrites'));
		event.preventDefault();
		return;
	}
	if( (!isInt(deletes)) || deletes < 1 || replicas < deletes ){
		shakeElement($('#inputLeoConsistancyDeletes'));
		event.preventDefault();
		return;
	}

	if ( (!isInt(nodes)) || nodes < 1 || $('#hypervisors').pillbox('itemCount') < nodes || replicas > nodes) {
		shakeElement($('#inputLeoStorageNodes'));
		event.preventDefault();
		return;
	}
}


function validateVMSecurityConfig (event){
	if ($('#radioVMKeysetExisting').radio('isChecked') && $('#inputKeysetPrivate').val().length < 1) {
		shakeElement($('#inputKeysetPrivate'));
		event.preventDefault();
		return;
	}
	if ($('#radioVMKeysetExisting').radio('isChecked') && $('#inputKeysetPublic').val().length < 1) {
		shakeElement($('#inputKeysetPublic'));
		event.preventDefault();
		return;
	}
	$('#wizardButtonNext').hide();
}


/******
/*
/*	DRAWING FUNCTIONS
/*
*******/


function drawResult(disk, memory, processor, admin, platform, dns_lookups){
	return '<label>Disk Space:'+sp(2)+'</label><span class="pull-right">' + disk.value + badge(disk.status) + '</span><br /> \
		<label>Total Memory:'+sp(2)+'</label><span class="pull-right">' + memory.value + badge(memory.status) + '</span><br /> \
		<label>Processor Threads:'+sp(2)+'</label><span class="pull-right">' + processor.value + badge(processor.status) + '</span><br /> \
		<label>Admin Network:'+sp(2)+'</label><span class="pull-right">' + admin.value + badge(admin.status) + '</span><br /> \
		<label>DNS Resolves Correctly:'+sp(2)+'</label><span class="pull-right">' + dns_lookups.value + badge(dns_lookups.status) + '</span><br /> \
		<label>Tested Platform Image:'+sp(2)+'</label><span class="pull-right">' + platform.value + badge(platform.status) + '</span><br />'
}

function sp(num){

	return Array(num + 1).join("&nbsp;")
}

function badge(status){
	switch(status) {
		case "ok":
			return sp(2) + '<span class="label label-success label-as-badge"><span class="glyphicon glyphicon-ok"></span></span>'
			break;
		case "error":
			return sp(2) + '<span class="label label-danger label-as-badge"><span class="glyphicon glyphicon-remove"></span></span>'
			break;
		case "warning":
			return sp(2) + '<span class="label label-warning label-as-badge"><span class="glyphicon glyphicon-flag"></span></span>'
			break;
	}
}



/******
/*
/*	UTILITY FUNCTIONS
/*
*******/



function shakeElement(selector) {
	var l = 20;
	for( var i = 0; i < 10; i++ )
		selector.animate( { 'margin-left': "+=" + ( l = -l ) + 'px' }, 50);
 }

function validateIPaddress(ipaddress)
{
	if (/^(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/.test(ipaddress))
		return true
	return false
}

function dot2num(dot)
{
    var d = dot.split('.');
    return ((((((+d[0])*256)+(+d[1]))*256)+(+d[2]))*256)+(+d[3]);
}

function isInt(value) {
  return !isNaN(value) &&
         parseInt(Number(value)) == value &&
         !isNaN(parseInt(value, 10));
}

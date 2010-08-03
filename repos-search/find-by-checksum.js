/**
 * Sample script to locate resource, any revision, based on checksum.
 */
$(document).ready(function() {
	
	var search = function(fieldname, value, callback) {
		$.ajax({
			dataType: 'json',
			url: '/solr/svnrev/select/?wt=json&q=' + fieldname + ':' + encodeURIComponent(value),
			success: callback
		});
	};
	
	var find = function(ev) {
		ev.preventDefault();
		var form = $(this);
		var md5 = $('#findmd5', form).val();
		var sha1 = $('#findsha1', form).val();
		var run = function(fieldname, value) {
			search(fieldname, value, function(solr) {
				// TODO show results
				window.console && console.log(solr);
				alert('Found ' + solr.response.numFound + ' items with ' + fieldname + ' ' + value);
			});
		};
		if (md5) run('md5', md5);
		if (sha1) run('sha1', sha1);
	};
	
	$('form#findchecksum').submit(find);
	
});


// Disable repos-search default init so that url can be changed
ReposSearch_onready = false;

$().ready(function() {
	// search
	ReposSearch.init({
		url: '/solr/svnhead/select/',
		uiUrl: '/repos-search/',
		parent: searchroot_parentUrl,
		// customize some of the default ui using css
		css: $.extend({}, ReposSearch.cssDefault, {
			list: null,
			resultindex: null
		})
	});
	// schema statistics
	$.ajax({
		url: $('.stat_numDocs').attr('href'),
		dataType: 'xml',
		success: stats
	});
	// more statistics
	$.ajax({
		url: $('.stat_parseErrors').attr('href'),
		dataType: 'xml',
		success: function(xml) {
			$('.stat_parseErrors').text(countDocs(xml));
		}
	});
});

$().bind('repos-search-started', function(ev, type, userQuery, r) {
	$(r).bind('repos-search-result', function(ev, microformatElement, solrDoc) {
		// if we don't have a parentUrl none of the links can work, unless prefix is server+parent
		if (solrDoc.id.indexOf('://') == -1 && !searchroot_parentUrl) {
			$('a', this).removeAttr('href');
		}
	});
});

function stats(xml) {
	var stat = {};
	$('entry', xml).each(function() {
		if (/\s+searcher\s+/im.test($('name', this).text())) {
			$('stat', this).each(function() {
				stat[$(this).attr('name')] = $(this).text(); // needs to be trimmed
			});
		}
	});
	for (s in stat) {
		$('.stat_' + s).text(stat[s]);
	}
}

function countDocs(xml) {
	return $('doc', xml).size();
}

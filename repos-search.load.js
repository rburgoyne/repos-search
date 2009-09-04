/*
 * Repos Search GUI (c) Staffan Olsson repossearch.com
 * Include in Repos Style header to get a search box in the menu bar.
 * Requires jQuery 1.3+
 * $LastChangedRevision$
 */

// minimal style, enough for css theming to be optional
reposSearchFormCss = {
	display: 'inline',
	marginLeft: 10
};
reposSearchInputCss = {
	background: "white url('/repos-search/magnifier.png') no-repeat right"
};
reposSearchDialogCss = {
	position: 'absolute',
	overflow: 'auto',
	top: 50,
	left: 30,
	right: 30,
	bottom: 30,
	opacity: 0.9,
	paddingLeft: 30,
	paddingRight: 30,
	backgroundColor: '#fff',
	border: '2px solid #eee'
};
reposSearchDialogTitleCss = {
	width: '100%',
	textAlign: 'center',
};
reposSearchDialogTitleLinkCss = {
	textDecoration: 'none',
	color: '#666'
};
reposSearchCloseCss = {
	textAlign: 'right',
	float: 'right',
	fontSize: '82.5%',
	cursor: 'pointer',
	color: '#666'
};
reposSearchListCss = {
	listStyleType: 'none',
	listStylePosition: 'inside'
};

$().ready(function() {
	reposSearchShow();
});

reposSearchShow = function() {
	// the page that includes Repos Search can provide an element with
	// class "repos-search-container" to control the placement of the input box
	var container = $('.repos-search-container').add('#commandbar').add('body').eq(0);
	var box = $('<input id="repos-search-input" type="text" name="repossearch" size="20"/>').css(reposSearchInputCss);
	var form = $('<form id="repos-search-form"><input type="submit" style="display:none"/></form>').append(box);
	form.css(reposSearchFormCss).appendTo(container); // TODO display settings should be set in css
	// urlMode appends the query to browser's location so back button is supported
	// urlMode works if the page has no other query parameters
	var urlMode = true;
	if (urlMode) {
		var s = location.search.indexOf('repossearch=');
		if (s > 0) {
			// repossearch is the last query parameter
			var q = decodeURIComponent(location.search.substr(s + 12).replace('+',' '));
			$('#repos-search-input').val(q);
			reposSearchSubmit();
		}
		form.attr('method', 'GET').attr('action','');
	} else {
		form.submit(reposSearchSubmit);
	}
};

reposSearchClose = function(ev) {
	$('#repos-search-dialog').remove();
	// clear input if this is a user event
	if (ev) $('#repos-search-input').val('');
};

reposSearchSubmit = function(ev) {
	ev && ev.stopPropagation();
	try {
		reposSearchStart();
	} catch (e) {
		if (window.console) console.error('Repos Search error', e);
	}
	return false; // don't submit form	
};

reposSearchStart = function() {
	var query = $('#repos-search-input').val();
	if (!query) return;
	// create search result container
	reposSearchClose(false);
	var dialog = $('<div id="repos-search-dialog"/>').css(reposSearchDialogCss);
	// start search request
	var titles = $('<div id="repos-search-titles"/>');
	reposSearchTitles(query, titles);
	// build results layout
	var title = $('<div class="repos-search-dialog-title"/>').css(reposSearchDialogTitleCss)
		.append($('<a target="_blank" href="http://repossearch.com/" title="repossearch.com">Repos Search</a>"')
		.attr('id', 'repos-search-dialog-title-link').css(reposSearchDialogTitleLinkCss));
	var close = $('<div class="repos-search-close">close</div>').css(reposSearchCloseCss).click(reposSearchClose);
	dialog.append(title);
	title.append(close);
	//dialog.append('<h1>Search results</h1>'); // would be better as title bar
	$('<h2/>').text('Titles matching ').append($('<em/>').text(query)).appendTo(dialog);
	dialog.append(titles);
	var fulltexth = $('<h2/>').text('Documents containing ').append($('<em/>').text(query)).hide();
	var fulltext = $('<div id="repos-search-fulltext"/>');
	var enablefulltext = $('<input id="repos-search-fulltext-enable" type="checkbox">').change(function() {
		if ($(this).is(':checked')) {
			fulltexth.show();
			fulltext.show();
			reposSearchFulltext(query, fulltext);
		} else {
			fulltexth.hide();
			fulltext.hide();
		}
	});
	$('<p/>').append(enablefulltext).append('<label for="enablefulltext"> Search contents</label>').appendTo(dialog);
	dialog.append(fulltexth).append(fulltext);
	titles.bind('repos-search-noresults', function() {
		enablefulltext.attr('checked', true).trigger('change');
	});
	close.clone(true).addClass("repos-search-close-bottom").appendTo(dialog);
	$('body').append(dialog);
	// publish page wide event so extensions can get hold of search events
	$().trigger('repos-search-started', [dialog[0], titles[0], fulltext[0]]);
};

reposSearchIdPrefix = ''; // if prefix is set in hook this must be the same, for use in id queries

reposSearchTitles = function(query, resultDiv) {
	// if IdPrefix is not set we can use repository base
	reposSearchIdPrefix = reposSearchIdPrefix ||
		$('meta[name=repos-base]').attr('content') + '/';
	// serach on title or part of path
	reposSearchAjax('/repos-search/?repossearch=title' + encodeURIComponent(':' + query)
			+ encodeURIComponent(' OR id:' + reposSearchIdPrefix + '*' + query + '*'), resultDiv);
};

reposSearchFulltext = function(query, resultDiv) {
	reposSearchAjax('/repos-search/?repossearch=text' + encodeURIComponent(':' + query), resultDiv);
};

reposSearchAjax = function(url, resultContainer) {
	// provide navigation info for search filtering
	var target = $('meta[name=repos-target]').attr('content');
	var base = $('meta[name=repos-base]').attr('content');
	if (target) url += '&target=' + encodeURIComponent(target);
	if (base) url += '&base=' + encodeURIComponent(base);
	// query
	resultContainer.addClass('loading'); // this requires a css so we'll also append image
	resultContainer.append('<img class="loading" src="/repos-search/loading.gif" alt="loading"/>');
	$.ajax({
		url: url,
		dataType: 'json',
		success: function(json) {
			resultContainer.removeClass('loading');
			$('.loading', resultContainer).remove();
			reposSearchResults(json, resultContainer);
		},
		error: function (XMLHttpRequest, textStatus, errorThrown) {
			resultContainer.removeClass('loading');
			$('.loading', resultContainer).remove();
			resultContainer.text('Error ' + textStatus + ": " + errorThrown);
		}
	});
};

reposSearchResults = function(json, resultContainer) {
	resultContainer.empty();
	var num = parseInt(json.response.numFound, 10);
	if (num === 0) {
		$('<p>No matches found</p>').appendTo(resultContainer);
		resultContainer.trigger('repos-search-noresults');
		return;
	}
	var list = $('<u/>').css(reposSearchListCss).appendTo(resultContainer);
	for (var i = 0; i < num; i++) {
		var e = reposSearchPresentItem(json.response.docs[i]);
		e.addClass(i % 2 ? 'even' : 'odd');
		e.appendTo(list);
		resultContainer.trigger('repos-search-result', [e[0]]); // event gets the element, not jQuery
	}
};

/**
 * Produce the element that presents a search hit.
 * To customize, replace this method in a script block below Repos Search import.
 * @param json the item from the solr "response.docs" array
 * @return jQuery element
 */
reposSearchPresentItem = function(json) {
	var m = /([^\/]*)(\/?.*\/)([^\/]*)/.exec(json.id);
	if (!m) return $("<li/>").text("Unknown match: " + json.id);
	var li = $('<li/>');
	var root = '/svn';
	if (m[1]) {
		root += '/' + m[1];
		li.append('<a class="repos-search-resultbase" href="' + root + '">' + m[1] + '</a>');
	}
	li.append('<a class="repos-search-resultpath" href="' + root + m[2] + '">' + m[2] + '</a>');
	li.append('<a class="repos-search-resultfile" href="' + root + m[2] + m[3] + '">' + m[3] + '</a>');
	if (json.title && json.title != m[3]) {
		$('<span class="repos-search-resulttitle">').text('  ' + json.title).appendTo(li);
	}
	// file class and file-extension class for icons (compatible with Repos Style)
	li.addClass('file');
	var d = m[3].lastIndexOf('.');
	if (d > 0 && d > m[3].length - 7) {
		li.addClass('file-' + m[3].substr(d+1).toLowerCase());
	}
	return li;
};

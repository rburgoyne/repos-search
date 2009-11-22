/*
 * Repos Search GUI (c) 2009 Staffan Olsson repossearch.com
 * 
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *    http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

/**
 * Sample search interface for Repos Search.
 * Add this script to Repos Style head to get a search box in the menu bar.
 * Requires jQuery 1.3+
 * $LastChangedRevision$
 */

// minimal style, enough for css theming to be optional
reposSearchFormCss = {
	display: 'inline',
	marginLeft: 10
};
reposSearchInputCss = {
	background: "white url('/repos-search/magnifier.png') no-repeat right",
	verticalAlign: 'middle'
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
	textAlign: 'center'
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

reposSearchShow = function(options) {
	// presentation settings
	var settings = {
		// the small search box in the container
		box: $('<input id="repos-search-input" type="text" name="repossearch" size="20"/>').css(reposSearchInputCss),
		
		// the page that includes Repos Search can provide an element with
		// class "repos-search-container" to control the placement of the input box
		boxparent: $('.repos-search-container').add('#commandbar').add('body').eq(0),
		
		// how to get search terms from the input box
		getTerms: function() {
			var query = $('#repos-search-input').val();
			return query.match(/[^\s"']+|"[^"]+"/g);
		},
		
		// urlMode appends the query to browser's location so back button is supported
		urlMode: true
	};
	$.extend(settings, options);
	// after refactoring settings should be an instance variable
	this.reposSearchSettings = settings;
	
	var form = $('<form id="repos-search-form"><input type="submit" style="display:none"/></form>').append(settings.box);
	form.css(reposSearchFormCss).appendTo(settings.boxparent); // TODO display settings should be set in css
	if (settings.urlMode) {
		var s = location.search.indexOf('repossearch=');
		if (s > 0) {
			// repossearch is the last query parameter
			var q = decodeURIComponent(location.search.substr(s + 12).replace(/\+/g,' '));
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
	// query types
	var titles = {
		id: 'titles',
		name: 'Titles',
		headline: 'Titles matching',
		getSolrQuery: function(terms) {
			// search two different fields, title or part of path
			var title = [];
			var path = [];
			for (i = 0; i < terms.length; i++) {
				title[i] = 'title:' + terms[i];
				//path[i] = 'id:' + reposSearchIdPrefix + '*' + terms[i].replace(/"/g,'').replace(/\s/g,'?') + '*';
				// Name ending with wildcard by default is reasonable because exact
				// filenames with extension will rarely produce false positives anyway
				path[i] = 'name:' + terms[i] + '*';
			}
			// currently tokens are ANDed together which might be too restrictive on name searches
			var query = '(' + title.join(' AND ') + ') OR (' + path.join(' AND ') + ')';
			return query;
		}
	};
	// get input
	// create search result container
	reposSearchClose(false);
	var dialog = $('<div id="repos-search-dialog"/>').css(reposSearchDialogCss);
	// start search request
	var terms = this.reposSearchSettings.getTerms()
	var titlesdiv = reposSearchQuery(titles, terms);
	// text for presentation
	var query = terms.join(' ');
	// build results layout
	var title = $('<div class="repos-search-dialog-title"/>').css(reposSearchDialogTitleCss)
		.append($('<a target="_blank" href="http://repossearch.com/" title="repossearch.com">Repos Search</a>"')
		.attr('id', 'repos-search-dialog-title-link').css(reposSearchDialogTitleLinkCss));
	var close = $('<div class="repos-search-close">close</div>').css(reposSearchCloseCss).click(reposSearchClose);
	dialog.append(title);
	title.append(close);
	//dialog.append('<h1>Search results</h1>'); // would be better as title bar
	$('<h2/>').text('Titles matching ').append($('<em/>').text(query)).appendTo(dialog);
	dialog.append(titlesdiv);
	var fulltexth = $('<h2/>').text('Documents containing ').append($('<em/>').text(query)).hide();
	var fulltext = $('<div id="repos-search-fulltext"/>');
	var enablefulltext = $('<input id="repos-search-fulltext-enable" type="checkbox">').change(function() {
		if ($(this).is(':checked')) {
			fulltexth.show();
			fulltext.show();
			reposSearchFulltext(terms, fulltext);
		} else {
			fulltexth.hide();
			fulltext.hide();
		}
	});
	$('<p/>').append(enablefulltext).append('<label for="enablefulltext"> Search contents</label>').appendTo(dialog);
	dialog.append(fulltexth).append(fulltext);
	titlesdiv.bind('repos-search-noresults', function() {
		enablefulltext.attr('checked', true).trigger('change');
	});
	close.clone(true).addClass("repos-search-close-bottom").appendTo(dialog);
	$('body').append(dialog);
	if ($.browser.msie) reposSearchIEFix(dialog);
	// publish page wide event so extensions can get hold of search events
	$().trigger('repos-search-started', [dialog[0], titles[0], fulltext[0]]);
};

reposSearchIEFix = function(dialog) {
	// is there jQuery feature detection for checkbox onchange event?
	$('input[type=checkbox]', dialog).click(function(ev) {
		ev.stopPropagation();
		$(this).attr('checked', $(this).is(':checked')).trigger('change');
	});
};

reposSearchQuery = function(type, terms) {
	var resultDiv = $('<div id="repos-search-' + type.id + '"/>');
	// Get search context from page metadata
	var reposBase = $('meta[name=repos-base]').attr('content');
	var reposTarget = $('meta[name=repos-target]').attr('content');
	// Build query
	var q = encodeURIComponent(type.getSolrQuery(terms));
	// seach context for use in proxy
	var context = reposTarget ? '&target=' + encodeURIComponent(reposTarget) : '';
	// we could restrict matches to current repository in the query, but the proxy knows more about schema internals
	context += reposBase ? '&base=' + reposBase : '';
	// execute search
	reposSearchAjax('/repos-search/?q=' + q + context, resultDiv);
	// return the container where results will be displayed
	return resultDiv;
};

reposSearchFulltext = function(terms, resultDiv) {
	var query = 'text:' + terms.join(' AND text:');
	reposSearchAjax('/repos-search/?q=' + encodeURIComponent(query), resultDiv);
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
		error: function (xhr, textStatus, errorThrown) {
			resultContainer.removeClass('loading');
			$('.loading', resultContainer).remove();
			// error message
			resultContainer.text('Got status ' + xhr.status + " " + xhr.statusText + ".");
			resultContainer.prepend('<h3>Error</h3>');
			// 403 is because of access control or, more likely, that index.py is not handled as DirectoryIndex
			if (xhr.status == 403) resultContainer.append('<br />The index script at <a href="/repos-search/">/repos-search/</a> might not be configured yet.');
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
 * 
 * The element is also a microformat for processing in repos-search-result event handlers:
 * $('.repos-search-resultbase').text() contains the base
 * $('.repos-search-resultpath').text() contains path to file excluding filename
 * $('.repos-search-resultfile').text() contains filename
 * 
 * @param json the item from the solr "response.docs" array
 * @return jQuery element
 */
reposSearchPresentItem = function(json) {
	var m = /([^\/]*)(\/?.*\/)([^\/]*)/.exec(json.id);
	if (!m) return $("<li/>").text("Unknown id format in seach result: " + json.id);
	var li = $('<li/>');
	var root = '/svn';
	if (m[1]) {
		root += '/' + m[1];
		li.append('<a class="repos-search-resultbase" href="' + root + '">' + m[1] + '</a>');
	}
	li.append('<a class="repos-search-resultpath" href="' + root + m[2] + '">' + m[2] + '</a>');
	li.append('<a class="repos-search-resultfile" href="' + root + m[2] + m[3] + '">' + m[3] + '</a>');
	if (json.title && json.title != m[3]) {
		$('<div class="repos-search-resulttitle"/>').text('  ' + json.title).appendTo(li);
	}
	// file class and file-extension class for icons (compatible with Repos Style)
	li.addClass('file');
	var d = m[3].lastIndexOf('.');
	if (d > 0 && d > m[3].length - 7) {
		li.addClass('file-' + m[3].substr(d+1).toLowerCase());
	}
	return li;
};

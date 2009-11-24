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
	if (window.console && window.console.log) {
		new ReposSearchEventLogger(console);
	}
	// set up results UI, single dialog instance
	var ui = new ReposSearchDialog({});
	// use mini search input to invoke Repos Search
	reposSearchSampleSearchBox();
});

reposSearchSampleSearchBox = function(options) {
	// presentation settings
	var settings = {
		// the small search box in the container
		box: $('<input id="repos-search-input" type="text" name="repossearch" size="20"/>').css(reposSearchInputCss),
		
		// the page that includes Repos Search can provide an element with
		// class "repos-search-container" to control the placement of the input box
		boxparent: $('.repos-search-container').add('#commandbar').add('body').eq(0),
		
		// how to get search terms from the input box
		getSearchString: function() {
			return $('#repos-search-input').val();
		},
		
		// urlMode appends the query to browser's location so back button is supported
		urlMode: true,
		
		// form event handler, with error handling so we never risk to trigger default submit
		submit: function(ev) {
			ev && ev.stopPropagation();
			try {
				reposSearchStart(this.getSearchString());
			} catch (e) {
				if (window.console) {
					console.error('Repos Search error', e, e.lineNumber);
				} else {
					alert('Repos Search error: ' + e);
				}
			}
			return false; // don't submit form	
		}
	};
	$.extend(settings, options);
	// build mini UI
	var form = $('<form id="repos-search-form"><input type="submit" style="display:none"/></form>');
	form.append(settings.box);
	form.css(reposSearchFormCss).appendTo(settings.boxparent); // TODO display settings should be set in css
	if (settings.urlMode) {
		var s = location.search.indexOf('repossearch=');
		if (s > 0) {
			// repossearch is the last query parameter
			var q = decodeURIComponent(location.search.substr(s + 12).replace(/\+/g,' '));
			$('#repos-search-input').val(q);
			settings.submit();
		}
		form.attr('method', 'GET').attr('action','');
	} else {
		form.submit(settings.submit);
	}
	// the search UI decides the execution model, and this one supports only one search at a time
	$().bind('repos-search-dialog-close', function(ev, dialog) {
		$.trigger('repos-search-exited');
	});
	// update mini UI based on dialog events
	$().bind('repos-search-exited', function() {
		$('#repos-search-input').val('');
	});
	$().bind('repos-search-string-changed', function(ev, searchString) {
		$('#repos-search-input').val(searchString);
	});	
};

/**
 * Runs queries for a list of search terms and triggers
 * events that can be used to build UI.
 * Could be refactored to a class that supports multiple searches.
 */
reposSearchStart = function(searchString) {
	// query types in order
	var schemes = [{
			id: 'title',
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
		},{
			id: 'fulltext',
			getSolrQuery: function(terms) {
				return 'text:' + terms.join(' AND text:');
			}
		},{
			id: 'metadata',
			getSolrQuery: function(terms) {
				return 'metadata:' + terms.join(' AND metadata:');
			}
		}];
	// get input
	var searchTerms = searchString.match(/[^\s"']+|"[^"]+"/g);
	// build query flow based on the schemes
	var schemeIds = [];
	for (var i = 0; i < schemes.length; i++) {
		var s = schemes[i];
		schemeIds.push(s.id);
	}
	// global initialize
	$().trigger('repos-search-started', [searchString, schemeIds]);
	// automatically start search using first scheme
	new ReposSearchQuery(schemes[0], searchTerms);
	// start the other schemes too
	new ReposSearchQuery(schemes[1], searchTerms);
	new ReposSearchQuery(schemes[2], searchTerms);
};

/**
 * @param {Object} scheme Scheme properties including id
 * @param {Array} terms Search terms
 */
function ReposSearchQuery(scheme, terms) {
	// Get search context from page metadata
	var reposBase = $('meta[name=repos-base]').attr('content');
	var reposTarget = $('meta[name=repos-target]').attr('content');
	// Build query
	var q = encodeURIComponent(scheme.getSolrQuery(terms));
	// Pass seach context to proxy for filtering
	var context = reposTarget ? '&target=' + encodeURIComponent(reposTarget) : '';
	// we could restrict matches to current repository in the query, but the proxy knows more about schema internals
	context += reposBase ? '&base=' + reposBase : '';
	// Execute search
	var url = '/repos-search/?q=' + q + context;
	// query
	$().trigger('repos-search-query-sent', [scheme.id, terms]);
	$.ajax({
		url: url,
		dataType: 'json',
		success: function(json) {
			$().trigger('repos-search-query-returned', [scheme.id, json]);
			reposSearchResults(json, scheme.id);
		},
		error: function (xhr, textStatus, errorThrown) {
			$().trigger('repos-search-query-failed', [scheme.id, xhr.status, xhr.statusText]);
		}
	});
};

/**
 * Logs all Repos Search events with parameters.
 * Also serves as a good event reference.
 * @param {Object} consoleApi Firebug console or equivalent API
 */
function ReposSearchEventLogger(consoleApi) {
	var logger = consoleApi;
	// all events bound to document node, at least until live events support arguments
	$().bind('repos-search-started', function(ev, searchString, schemeIds) {
		logger.log(ev.type, searchString, schemeIds);
	});
	$().bind('repos-search-query-sent', function(ev, schemeId, terms) {
		logger.log(ev.type, schemeId, terms);
	});
	$().bind('repos-search-query-returned', function(ev, schemeId, json) {
		logger.log(ev.type, schemeId, json);
	});
	$().bind('repos-search-query-failed', function(ev, schemeId, httpStatus, httpStatusText) {
		logger.log(ev.type, schemeId, 'status=' + httpStatus + ' statusText=' + httpStatusText);
	});
	$().bind('repos-search-result', function(ev, microformatElement, solrDoc, schemeId) {
		var e = microformatElement;
		logger.log(ev.type, e, 
			'base=' + $('.repos-search-resultbase', e).text(),
			'path=' + $('.repos-search-resultpath', e).text(),
			'file=' + $('.repos-search-resultfile', e).text(),
			solrDoc, 
			'id=' + solrDoc.id,
			schemeId);
	});
	$().bind('repos-search-result-truncated', function(ev, start, shown, numFound, schemeId) {
		logger.log(ev.type, schemeId + ': showed ' + start + ' to ' + (start+shown) + ' of ' + numFound);
	});
	// Standard UI's events
	$().bind('repos-search-dialog-opened', function() {
		logger.log(arguments);
	});
	$().bind('repos-search-query-wanted', function(ev, schemeId) {
		logger.log(ev.type, schemeId);
	});
}

function ReposSearchDialog(options) {
	
	var settings = $.extend({
		id: 'repos-search-dialog'
	}, options);
	
	var knownSchemes = 	{
		title: {
			name: 'Titles',
			description: 'Matches filenames that start with the search term' +
				' and documents containing a format-specific title that contains the terms',
			headline: 'Titles matching'
		},
		fulltext: {
			name: 'Fulltext',
			description: 'Matches documents that contain the search terms',
			headline: 'Files containing'
		},
		metadata: {
			name: 'Metadata',
			description: 'Searches document metadata including subversion properties',
			headline: 'Files with metadata',
		}
	};
	
	var close = function(ev) {
		var d = $('#' + settings.id);
		$().trigger('repos-search-dialog-closing', [d[0]]);
		d.remove();
	};
	
	var dialog = $('<div/>').attr('id', settings.id).css(reposSearchDialogCss);
	
	$().bind('repos-search-started', function(ev, searchString, seachTerms, schemeIds) {
		var title = $('<div class="repos-search-dialog-title"/>').css(reposSearchDialogTitleCss)
			.append($('<a target="_blank" href="http://repossearch.com/" title="repossearch.com">Repos Search</a>"')
			.attr('id', 'repos-search-dialog-title-link').css(reposSearchDialogTitleLinkCss));
		var closeAction = $('<div class="repos-search-close">close</div>').css(reposSearchCloseCss).click(close);
		dialog.append(title);
		title.append(closeAction);
		//closeAction.clone(true).addClass("repos-search-close-bottom").appendTo(dialog);
		$('body').append(dialog);
		if ($.browser.msie) reposSearchIEFix(dialog);
		// publish page wide event so extensions can get hold of search events
		$().trigger('repos-search-dialog-opened', [dialog[0]]);	
	});
	
	$().bind('repos-search-query-sent', function(ev, schemeId, terms) {
		var scheme = knownSchemes[schemeId];
		var schemediv = $('<div/>').attr('id', 'repos-search-results-' + schemeId).addClass('repos-search-results');
		$('<ul/>').css(reposSearchListCss).appendTo(schemediv);
		$('<h2/>').text(scheme.headline || '').append('&nbsp;').append($('<em/>').text(terms.join(' '))).appendTo(dialog);
		dialog.append(schemediv);
		/* TODO checkboxes for different search schemes
		var enablefulltext = $('<input id="repos-search-ui-enable-fulltext" type="checkbox">').change(function(){
			if ($(this).is(':checked')) {
			} else {
			}
		});
		$('<p/>').append(enablefulltext).append('<label for="enablefulltext"> Search contents</label>').appendTo(dialog);
		*/
		/* TODO automatically trigger next search on no results?
		schemediv.bind('repos-search-noresults', function() {
			$().trigger('repos-search-ui-scheme-requested', ['fulltext']);
		});
		*/
	});
	
	$().bind('repos-search-ui-scheme-requested', function(ev, schemeId) {
		var checkbox = $('#repos-search-ui-enable-' + schemeId);
		if (!checkbox.is(':checked')) {
			checkbox.attr('checked', true);
			checkbox.trigger('change');
		}
	});
	
	$().bind('repos-search-result', function(ev, microformatElement, solrDoc, schemeId) {
		var s = $('#repos-search-results-' + schemeId);
		$('> ul', s).append(microformatElement);
	});
	
}

reposSearchIEFix = function(dialog) {
	// is there jQuery feature detection for checkbox onchange event?
	$('input[type=checkbox]', dialog).click(function(ev) {
		ev.stopPropagation();
		$(this).attr('checked', $(this).is(':checked')).trigger('change');
	});
};

/**
 * Produces event for search result.
 * @param {String} json Response from Solr wt=json
 * @param {String} scheme Search scheme id
 */
reposSearchResults = function(json, scheme) {
	var num = parseInt(json.response.numFound, 10);
	if (num === 0) {
		$().trigger('repos-search-noresults', [scheme]);
		return;
	}
	var n = json.response.docs.length;
	for (var i = 0; i < n; i++) {
		var doc = json.response.docs[i];
		var e = reposSearchPresentItem(doc);
		e.addClass(i % 2 ? 'even' : 'odd');
		$().trigger('repos-search-result', [e[0], doc, scheme]); // event gets the element, not jQuery
	}
	if (n < num) {
		$().trigger('repos-search-result-truncated', [json.response.start, n, num, scheme]);
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

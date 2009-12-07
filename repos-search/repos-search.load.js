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

/**
 * @constructor
var ReposSearch = function() {
	this.init();
};
ReposSearch.options.onready = function() {
		// default init
	}
};
 */

var ReposSearch = {
	init: function(options) {
		if (window.console && window.console.log) {
			new ReposSearchEventLogger(console);
		}
		// use mini search input to invoke Repos Search
		ReposSearch.SampleSearchBox({
			submithandler: ReposSearch.LightUI
		});
	},
	onready: function(){
		ReposSearch.init();
	}
};

$().ready(function() {
	if (ReposSearch.onready) {
		ReposSearch.onready();
	}
});

// minimal style, enough for css theming to be optional
ReposSearch.FormCss = {
	display: 'inline',
	marginLeft: 10
};
ReposSearch.InputCss = {
	background: "white url('/repos-search/magnifier.png') no-repeat right",
	verticalAlign: 'middle'
};
ReposSearch.DialogCss = {
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
ReposSearch.DialogTitleCss = {
	width: '100%',
	textAlign: 'center'
};
ReposSearch.DialogTitleLinkCss = {
	textDecoration: 'none',
	color: '#666'
};
ReposSearch.CloseCss = {
	textAlign: 'right',
	float: 'right',
	fontSize: '82.5%',
	cursor: 'pointer',
	color: '#666'
};
ReposSearch.ListCss = {
	listStyleType: 'none',
	listStylePosition: 'inside'
};

/**
 * Wraps the search request+response as a layer above
 * installation settings.
 * Provides accessors for the response structure and
 * direct access to the docs array from the Solr response.
 * 
 * @param {Object} options Query parameters, success callback
 * 
 * @constructor
 */
function ReposSearchRequest(options) {
	var instance = this;
	// Get search context from page metadata
	var reposBase = $('meta[name=repos-base]').attr('content');
	var reposTarget = $('meta[name=repos-target]').attr('content');
	// Request parameters
	var params = {
		// proxy
		base: reposBase || '',
		target: reposBase || '',
		// solr
		q: options.q,
		qt: options.type || 'meta',
		wt: 'json'
	};
	// Query the proxy
	$.ajax({
		url: '/repos-search/',
		data: params,
		dataType: 'json',
		success: function(json) {
			// old event
			$().trigger('repos-search-query-returned', [params.qt, json]);
			// new handling based on callback
			instance.json = json;
			options.success(instance);
		},
		error: function (xhr, textStatus, errorThrown) {
			// old event
			$().trigger('repos-search-query-failed', [params.qt, xhr.status, xhr.statusText]);
		}
	});
	// Public response access methods
	$.extend(instance, {
		getDocs: function() {
			return this.json.response.docs;
		},
		getStart: function() {
			return this.json.response.start;
		},
		getNumFound: function() {
			return this.json.response.numFound;
		},
		getNumReturned: function(){
			return this.getDocs().length;
		}
	});
};

/**
 * Takes the user's query and a result container and produces
 * a series of search events.
 * 
 * Results are appended to the resultList using a
 * microformat.
 * 
 * @param {String} type Query type: 'meta', 'content' or any other type from the Solr schema
 * @param {String} userQuery The search query
 * @param {Element|jQuery} resultList OL or UL, possibly containing old results
 */
function ReposSearchQuery(type, userQuery, resultList) {
	listQ = $(resultList);
	listE = listQ[0];
	$().trigger('repos-search-started', [type, userQuery, listE]);
	var r = new ReposSearchRequest({
		type: type,
		q: userQuery,
		success: function(searchRequest) {
			// This event can be used to hide previous results, if there are any
			listQ.trigger('repos-search-query-returned', [searchRequest]);
			ReposSearch.Results(searchRequest.json, listQ);
		}
	});
	listQ.trigger('repos-search-query-sent', [r]);
}

/**
 * Produces event for search result.
 * @param {String} json Response from Solr wt=json
 * @param {jQuery} listQ OL or UL, possibly containing old results
 */
ReposSearch.Results = function(json, listQ) {
	// TODO move to query class
	var num = parseInt(json.response.numFound, 10);
	if (num === 0) {
		listQ.trigger('repos-search-noresults');
		return;
	}
	var n = json.response.docs.length;
	for (var i = 0; i < n; i++) {
		var doc = json.response.docs[i];
		var e = ReposSearch.presentItem(doc);
		e.addClass(i % 2 ? 'even' : 'odd');
		// TODO add to list
		listQ.append(e);
		listQ.trigger('repos-search-result', [e[0], doc]); // event gets the element, not jQuery
	}
	if (n < num) {
		listQ.trigger('repos-search-result-truncated', [json.response.start, n, num]);
	}
};

ReposSearch.getPropFields = function(json) {
	var f = [];
	for (key in json) f.push(key);
	f.sort(function(a, b) {
		if (a == 'title') return -1;
		if (b == 'title') return 1;
		if (a < b) return -1;
		return 1;
	});
	return f;
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
ReposSearch.presentItem = function(json) {
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
	// add all indexed info to hidded definition list
	var indexed = $('<dl class="repos-search-resultindex"/>').appendTo(li).hide();
	var fields = ReposSearch.getPropFields(json);
	for (var i = 0; i < fields.length; i++) {
		var key = fields[i];
		if (!json[key]) continue;
		var cs = 'indexed_' + key;
		$('<dt/>').addClass(cs).text(key).appendTo(indexed);
		if (typeof json[key] == 'array') {
			for (var j = 0; j < json[key].length; j++) {
				$('<dd/>').addClass(cs).text("" + json[key][j]).appendTo(indexed);
			}
		} else {
			$('<dd/>').addClass(cs).text("" + json[key]).appendTo(indexed);
		}
	}	
	// file class and file-extension class for icons (compatible with Repos Style)
	li.addClass('file');
	var d = m[3].lastIndexOf('.');
	if (d > 0 && d > m[3].length - 7) {
		li.addClass('file-' + m[3].substr(d+1).toLowerCase());
	}
	return li;
};

/**
 * Logs all Repos Search events with parameters.
 * Also serves as a good event reference.
 * @param {Object} consoleApi Firebug console or equivalent API
 */
function ReposSearchEventLogger(consoleApi) {
	var logger = consoleApi;
	// root event bound to document node
	$().bind('repos-search-started', function(ev, type, userQuery, r) {
		logger.log(ev.type, this, type, userQuery, r);
		
		$(r).bind('repos-search-query-sent', function(ev, searchRequest) {
			logger.log(ev.type, this, searchRequest);
		});
		$(r).bind('repos-search-query-returned', function(ev, searchRequest) {
			logger.log(ev.type, this, searchRequest);
		});
		$(r).bind('repos-search-query-failed', function(ev, searchRequest, httpStatus, httpStatusText) {
			logger.log(ev.type, this, searchRequest, 'status=' + httpStatus + ' statusText=' + httpStatusText);
		});
		$(r).bind('repos-search-result', function(ev, microformatElement, solrDoc, schemeId) {
			var e = microformatElement;
			logger.log(ev.type, this, e, 
				'base=' + $('.repos-search-resultbase', e).text(),
				'path=' + $('.repos-search-resultpath', e).text(),
				'file=' + $('.repos-search-resultfile', e).text(),
				solrDoc, 
				'id=' + solrDoc.id,
				schemeId);
		});
		$(r).bind('repos-search-result-truncated', function(ev, start, shown, numFound) {
			logger.log(ev.type, this, 'showed ' + start + ' to ' + (start+shown) + ' of ' + numFound);
		});
	});
	
	// Standard UI's events
	$().bind('repos-search-dialog-opened', function() {
		logger.log(arguments);
	});
	$().bind('repos-search-query-wanted', function(ev, schemeId) {
		logger.log(ev.type, schemeId);
	});
}

/**
 * Small search box that is suitable for integration with Repos Style.
 * @param {Object} options
 */
ReposSearch.SampleSearchBox = function(options) {
	// presentation settings
	var settings = {
		// the small search box in the container
		box: $('<input id="repos-search-input" type="text" name="repossearch" size="20"/>').css(ReposSearch.InputCss),
		
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
				options.submithandler({
					q: this.getSearchString()
				});
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
	form.css(ReposSearch.FormCss).appendTo(settings.boxparent); // TODO display settings should be set in css
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
 * Very lightweight presentation of search results.
 * @param {Object} options
 */
ReposSearch.LightUI = function(options) {
	
	console.log('lightui', options);
	
	var settings = $.extend({
		id: 'repos-search-dialog'
	}, options);
	
	var knownSchemes = {
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
			headline: 'Files with metadata'
		}
	};
	
	var close = function(ev) {
		var d = $('#' + settings.id);
		$().trigger('repos-search-dialog-closing', [d[0]]);
		d.remove();
	};
	
	$().bind('repos-search-started', function(ev, searchString, seachTerms) {
		var title = $('<div class="repos-search-dialog-title"/>').css(ReposSearch.DialogTitleCss)
			.append($('<a target="_blank" href="http://repossearch.com/" title="repossearch.com">Repos Search</a>"')
			.attr('id', 'repos-search-dialog-title-link').css(ReposSearch.DialogTitleLinkCss));
		var closeAction = $('<div class="repos-search-close">close</div>').css(ReposSearch.CloseCss).click(close);
		dialog.append(title);
		title.append(closeAction);
		//closeAction.clone(true).addClass("repos-search-close-bottom").appendTo(dialog);
		$('body').append(dialog);
		if ($.browser.msie) ReposSearch.IEFix(dialog);
		// publish page wide event so extensions can get hold of search events
		$().trigger('repos-search-dialog-opened', [dialog[0]]);	
	});
	
	var dialog = $('<div/>').attr('id', settings.id).css(ReposSearch.DialogCss);
	var meta = $('<ul/>').css(ReposSearch.ListCss);
	new ReposSearchQuery('meta', settings.q, meta);
	meta.appendTo(dialog);
	
	$().bind('repos-search-query-sent', function(ev, schemeId, terms) {
		var scheme = knownSchemes[schemeId];
		var schemediv = $('<div/>').attr('id', 'repos-search-results-' + schemeId).addClass('repos-search-results');
		$('<ul/>').css(ReposSearch.ListCss).appendTo(schemediv);
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
	
};

ReposSearch.IEFix = function(dialog) {
	// is there jQuery feature detection for checkbox onchange event?
	$('input[type=checkbox]', dialog).click(function(ev) {
		ev.stopPropagation();
		$(this).attr('checked', $(this).is(':checked')).trigger('change');
	});
};

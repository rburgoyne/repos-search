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

var ReposSearch = {
	url: '/repos-search/',
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

/**
 * Minimal style, enough for css theming to be optional.
 * To disable do "ReposSearch.css = {};" before init.
 */
ReposSearch.css = {
	form: {
		display: 'inline',
		marginLeft: 10
	},
	input: {
		background: "white url(" + ReposSearch.url + "'magnifier.png') no-repeat right",
		verticalAlign: 'middle'
	},
	dialog: {
		position: 'absolute',
		overflow: 'auto',
		top: 50,
		left: 30,
		right: 30,
		bottom: 30,
		opacity: 0.9,
		backgroundColor: '#fff',
		border: '3px solid #aaa'
	},
	dialogTitle: {
		width: '100%',
		textAlign: 'center',
		backgroundColor: '#eee'
	},
	dialogTitleLink: {
		textDecoration: 'none',
		color: '#666'
	},
	headline: {
		verticalAlign: 'middle'
	},
	headlineCheckbox: {
		marginRight: '1em',
		verticalAlign: 'middle'
	},
	close: {
		textAlign: 'right',
		float: 'right',
		fontSize: '82.5%',
		cursor: 'pointer',
		color: '#666',
		padding: '0.1em'
	},
	closeBottom: {
		clear: 'both'
	},
	queryDiv: {
		float: 'left',
		paddingLeft: '1em'
	},
	list: {
		listStyleType: 'none',
		listStylePosition: 'inside',
		paddingLeft: '0.4em'
	}
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
		url: ReposSearch.url,
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
}

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
	var listQ = $(resultList);
	var listE = listQ[0];
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
	// TODO move this to query class
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
		listQ.trigger('repos-search-truncated', [json.response.start, n, num]);
	}
};

ReposSearch.getPropFields = function(json) {
	var f = [];
	for (var key in json) f.push(key);
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
		$(r).bind('repos-search-truncated', function(ev, start, shown, numFound) {
			logger.log(ev.type, this, 'showed ' + start + ' to ' + (start+shown) + ' of ' + numFound);
		});
	});
	
	// LightUI's events, triggered on the divs
	$().bind('repos-search-dialog-open', function(ev, dialog) {
		logger.log(ev.type, dialog);
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
		box: $('<input id="repos-search-input" type="text" name="repossearch" size="20"/>').css(ReposSearch.css.input),
		
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
	form.css(ReposSearch.css.form).appendTo(settings.boxparent); // TODO display settings should be set in css
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
		$().trigger('repos-search-exited');
	});
	// update mini UI based on dialog events
	$().bind('repos-search-exited', function() {
		$('#repos-search-input').val('');
	});
	$().bind('repos-search-input-change', function(ev, searchString) {
		$('#repos-search-input').val(searchString);
	});	
};

/**
 * Very lightweight presentation of search results.
 * @param {Object} options
 */
ReposSearch.LightUI = function(options) {
	
	var css = ReposSearch.css;
	
	var settings = $.extend({
		id: 'repos-search-'
	}, options);
	
	var close = function(ev) {
		var d = $('#' + settings.id + 'dialog');
		$().trigger('repos-search-dialog-close', [d[0]]);
		d.remove();
	};
	
	// light dialog
	var dialog = $('<div/>').attr('id', settings.id+'dialog').css(css.dialog);
	var title = $('<div class="repos-search-dialog-title"/>').css(css.dialogTitle)
		.append($('<a target="_blank" href="http://repossearch.com/" title="repossearch.com">Repos Search</a>"')
		.attr('id', settings.id+'dialog-title-link').css(css.dialogTitleLink));
	$('<span class="repos-search-dialog-title-separator"/>').text(' - ').appendTo(title);
	$('<em class="repos-search-dialog-title-label"/>').text(options.q).appendTo(title);	
	dialog.append(title);
	
	var closeAction = $('<div class="repos-search-close">close</div>').css(css.close).click(close);
 	title.append(closeAction);
	
	// helper to create query container
	var querydiv = function(id, headline) {
		var div = $('<div/>').attr('id', id + '-div').css(css.queryDiv);
		var h = $('<h3/>').text(headline).css(css.headline).appendTo(div);
		// checkbox to enable/disable
		var c = $('<input type="checkbox">').attr('id', id + '-enable').prependTo(h);
		c.css(css.headlineCheckbox).change(function(){
			if ($(this).is(':checked')) {
				div.trigger('repos-search-ui-query-enable', [id]);
			} else {
				div.trigger('repos-search-ui-query-disable', [id]);
			}
		});
		// return the element that gets the events, use .parent() to get the div
		div.appendTo(dialog);
		return div;
	};
	
	var meta = querydiv(settings.id+'meta', 'Titles and keywords');
	var content = querydiv(settings.id+'content', 'Text contents');
	var all = $(meta).add(content);
	
	all.bind('repos-search-ui-query-disable', function() {
		$('ul, ol', this).remove();
	}).bind('repos-search-ui-query-enable', function(ev, id) {
		var list = $('<ul/>').attr('id', id).css(css.list).appendTo(this);
		var qname = list.attr('id').substr(settings.id.length);
		var query = new ReposSearchQuery(qname, settings.q, list);
		// result presentation
		list.bind('repos-search-noresults', function() {
			var nohits = $('<li class="repos-search-nohits"/>').text('No hits').appendTo(this);
		});
		list.bind('repos-search-truncated', function(ev, start, shown, numFound) {
			var next = $('<li class="repos-search-next"/>').appendTo(this);
			var nexta = $('<a href="javascript:void(0)"/>').html('&raquo; more results').click(function() {
				alert('not implemented');
			}).appendTo(next);
		});	
	});

	// run query for metadata by default
	var enable = function(querydiv) {
		var c = $('input', querydiv);
		if (!c.is(':checked')) {
			c.attr('checked', true).trigger('change');
		}
	};
	enable(meta);
	// automatically search fulltext if there are no results in meta
	$('ul, ol', meta).one('repos-search-noresults', function() {
		enable(content);
	});
	
	// close button at bottom of page
	closeAction.clone(true).addClass('repos-search-close-bottom').css(css.closeBottom).appendTo(dialog);
	
	$('body').append(dialog);
	if ($.browser.msie) ReposSearch.IEFix(dialog);
	
	// publish page wide event so extensions can get hold of search events
	$().trigger('repos-search-dialog-open', [dialog[0]]);	
	
};

ReposSearch.IEFix = function(dialog) {
	// is there jQuery feature detection for checkbox onchange event?
	$('input[type=checkbox]', dialog).click(function(ev) {
		ev.stopPropagation();
		$(this).attr('checked', $(this).is(':checked')).trigger('change');
	});
};

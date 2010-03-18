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

// namespace
var ReposSearch = {};

/**
 * Initializes default search UI.
 * @param {Object} options including url and css
 */
ReposSearch.init = function(options) {
	var settings = $.extend({
		// search
		/* url to the search service */
		url: '/repos-search/',
		/* url to UI files, false for same as url */
		uiUrl: false,
		/* coded css, see default, empty object to do all styling in real css */
		css: ReposSearch.cssDefault,
		/* URL to the parent path for search result links, no trailing slash.
		   false to use default parent or parent from document prefix */
		parent: false,		
		/* true to enable event logger if there is a window.console */
		logger: false
	}, options);
	// logger
	if (settings.logger && window.console && window.console.log) {
		new ReposSearch.EventLogger(console);
	}
	// insert base url in css properties that can contain urls
	// TODO real css would be better here as it has relative urls
	if (settings.css && settings.css.input) {
		var c = settings.css && settings.css.input;
		c.background = c.background && c.background.replace('{url}', settings.url);
	}
	// initialize query class
	settings.uiUrl = settings.uiUrl || settings.url;
	ReposSearchRequest.prototype.url = settings.url || ReposSearchRequest.prototype.url;
	// use mini search input to invoke Repos Search
	var ui = new ReposSearch.LightUI({
		parent: settings.parent,
		css: settings.css
	});
	var box = new ReposSearch.SampleSearchBox({
		submithandler: function(q){ ui.run(q); },
		css: settings.css
	});
};

// The point with this initialization method is that
// no additional scripts should be needed to get the default GUI
// Set "ReposSearch_onready = false;" to disable automatic initialization 
ReposSearch_onready = ReposSearch.onready || ReposSearch.init;

$(document).ready(function() {
	if (ReposSearch_onready) {
		ReposSearch_onready();
	}
});

/**
 * Minimal style, enough for css theming to be optional.
 * @static
 */
ReposSearch.cssDefault = {
	form: {
		display: 'inline',
		marginLeft: 10
	},
	input: {
		background: "white url('{url}magnifier.png') no-repeat right"
	},
	dialog: {
		position: 'absolute',
		overflow: 'auto',
		top: 50,
		bottom: 30,
		left: '1%',
		right: '1%',
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
		width: '48.5%',
		minWidth: '500px',
		float: 'left',
		paddingLeft: '1em'
	},
	list: {
		listStyleType: 'none',
		listStylePosition: 'inside',
		paddingLeft: '0.4em'
	},
	result: {
		marginLeft: '1em',
		textIndent: '-1em'
	},
	resultindex: {
		display: 'none'
	},
	resultPrevious: {
		fontSize: '82.5%'
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
		start: options.start || 0,
		rows: options.rows || 10,
		wt: 'json'
	};
	// Query the proxy
	$.ajax({
		url: instance.url,
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
		getRows: function() { // valid even if request has not completed
			return params.rows;
		},
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

// Settings for the requests that the rest of the application should not need to care about
ReposSearchRequest.prototype.url = './';

/**
 * Takes the user's query and a result container and produces
 * a series of search events.
 * 
 * Results are appended to the resultList using a
 * microformat.
 * 
 * @param {String} type Query type: 'meta', 'content' or any other type from the Solr schema
 * @param {String} userQuery The search query
 * @param {String} parentUrl For presentation of the results, the prefix to base and path
 * @param {Element|jQuery} resultList OL or UL, possibly containing old results
 */
function ReposSearchQuery(type, userQuery, parentUrl, resultList) {
	this.type = type;
	this.query = userQuery;
	this.listQ = $(resultList);
	this.listE = this.listQ[0];
	this.parentUrl = parentUrl;
	this.parentUrlDefault = '/svn/';
	this.start = 0;
	this.r = null;
	$().trigger('repos-search-started', [this.type, this.query, this.listE]);
	this.exec();
}

ReposSearchQuery.prototype.exec = function() {
	var instance = this;
	var listQ = this.listQ; // closure scope
	this.r = new ReposSearchRequest({
		type: this.type,
		q: this.query,
		start: this.start,
		success: function(searchRequest){
			// This event can be used to hide previous results, if there are any
			listQ.trigger('repos-search-query-returned', [searchRequest]);
			instance.presentResults(searchRequest.json, listQ);
		}
	});
	listQ.trigger('repos-search-query-sent', [this.r]);
};

ReposSearchQuery.prototype.pageNext = function() {	
	this.start = this.start + this.r.getRows();
	this.exec();
};

/**
 * Produces event for search result.
 * @param {String} json Response from Solr wt=json
 * @param {jQuery} listQ OL or UL, possibly containing old results
 */
ReposSearchQuery.prototype.presentResults = function(json, listQ) {
	var num = parseInt(json.response.numFound, 10);
	var start = parseInt(json.response.start, 10);
	if (num === 0) {
		listQ.trigger('repos-search-noresults');
		return;
	}
	var n = json.response.docs.length;
	for (var i = 0; i < n; i++) {
		var doc = json.response.docs[i];
		var e = this.presentItem(doc);
		e.addClass(i % 2 ? 'even' : 'odd');
		listQ.append(e);
		listQ.trigger('repos-search-result', [e[0], doc]); // event arg is the element, not jQuery bucket
	}
	if (start + n < num) {
		listQ.trigger('repos-search-truncated', [json.response.start, n, num]);
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
ReposSearchQuery.prototype.presentItem = function(json) {
	var m = /(.*\/)?([^\/]*)?\^(\/?.*\/)([^\/]*)/.exec(json.id);
	if (!m) return $("<li/>").text("Unknown id format in seach result: " + json.id);
	var li = $('<li/>').addClass('repos-search-result');
	var root = m[1] || this.parentUrl || this.parentUrlDefault;
	if (m[2]) {
		root += m[2];
		li.append('<a class="repos-search-resultbase" href="' + root + '/">' + m[2] + '</a>');
	}
	li.append('<a class="repos-search-resultpath" href="' + root + m[3] + '">' + m[3] + '</a>');
	li.append('<a class="repos-search-resultfile" href="' + root + m[3] + m[4] + '">' + m[4] + '</a>');
	var indexed = $('<dl class="repos-search-resultindex"/>').appendTo(li);
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
	var d = m[4].lastIndexOf('.');
	if (d > 0 && d > m[4].length - 7) {
		li.addClass('file-' + m[4].substr(d+1).toLowerCase());
	}
	return li;
};


/**
 * @param {Object} json Solr doc
 * @return {Array} fieldnames to display
 * @static
 */
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
 * Logs all Repos Search events with parameters.
 * Also serves as a good event reference.
 * @param {Object} consoleApi Firebug console or equivalent API
 * @constructor
 */
ReposSearch.EventLogger = function(consoleApi) {
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
		$(r).bind('repos-search-result', function(ev, microformatElement, solrDoc) {
			var e = microformatElement;
			logger.log(ev.type, this, e, 
				'base=' + $('.repos-search-resultbase', e).text(),
				'path=' + $('.repos-search-resultpath', e).text(),
				'file=' + $('.repos-search-resultfile', e).text(),
				solrDoc);
		});
		$(r).bind('repos-search-truncated', function(ev, start, shown, numFound) {
			logger.log(ev.type, this, 'showed ' + start + ' to ' + (start+shown) + ' of ' + numFound);
		});
	});
	
	// LightUI's events, triggered on the divs
	$().bind('repos-search-dialog-open', function(ev, dialog) {
		logger.log(ev.type, dialog);
	});
};

/**
 * Small search box that is suitable for integration with Repos Style.
 * @param {Object} options
 */
ReposSearch.SampleSearchBox = function(options) {
	// presentation settings
	var settings = {
		// the small search box in the container
		box: $('<input id="repos-search-input" type="text" name="repossearch" size="20"/>').css(options.css.input),
		
		// the page that includes Repos Search can provide an element with
		// class "repos-search-container" to control the placement of the input box
		boxparent: $('.repos-search-container')[0] || $('#commandbar')[0] || $('body')[0],
		
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
				options.submithandler(this.getSearchString());
			} catch (e) {
				alert('Repos Search error: ' + e);
			}
			return false; // don't submit form	
		}
	};
	$.extend(settings, options);
	// build mini UI
	var form = $('<form id="repos-search-form"><input type="submit" style="display:none"/></form>');
	form.append(settings.box);
	form.css(options.css.form).appendTo(settings.boxparent); // TODO display settings should be set in css
	if (settings.urlMode) {
		var s = location.search.indexOf('repossearch=');
		if (s > 0) {
			// repossearch is the last query parameter
			var q = decodeURIComponent(location.search.substr(s + 12).replace(/\+/g,' '));
			$('#repos-search-input').val(q);
			settings.submit();
		}
		// Can not use browser's submit because then we need hidden fields for all existing query params
		//form.attr('method', 'GET').attr('action','');		
		form.submit(function(ev) {
			ev.stopPropagation();
			var href = location.href;
			href += href.indexOf('?') == -1 ? '?' : '&';
			href += 'repossearch=' + enccodeURIComponent(q);
			location.href = href;
		});
	} else {
		form.submit(settings.submit);
	}
	// the search UI decides the execution model, and this one supports only one search at a time
	$().bind('repos-search-dialog-close', function(ev, dialog) {
		$().trigger('repos-search-exited');
		if (settings.urlMode) {
			var s = location.href.indexOf('repossearch=');
			if (s > 0) {
				location.href = location.href.substr(0, s);
			}	
		}		
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
 * @constructor
 */
ReposSearch.LightUI = function(options) {
	
	this.settings = $.extend({
		id: 'repos-search-',
		parent: '/svn'
	}, options);
	
	// for closure scope, 
	var uiCss = this.settings.css;
	var uiSettings = this.settings;

	/**
	 * Removes the dialog.
	 */	
	this.destroy = function(ev) {
		var d = $('#' + uiSettings.id + 'dialog');
		$().trigger('repos-search-dialog-close', [d[0]]);
		d.remove();
	};
	
	/**
	 * Creates interactive search result presentation.
	 * @param {String} query Valid solr query from the user
	 */
	this.run = function(query) {
		$('.repos-search-dialog-title-label', this.dialog).text(query);
		var meta = this.queryCreate(uiSettings.id + 'meta', 'Titles and keywords');
		var content = this.queryCreate(uiSettings.id + 'content', 'Text contents');
		
		var all = $(meta).add(content);
		all.bind('disabled', function() {
			$('ul, ol', this).remove();
		}).bind('enabled', function(ev, id) {
			var list = $('<ul/>').attr('id', id).addClass('repos-search-result-list').css(uiCss.list).appendTo(this);
			var qname = list.attr('id').substr(uiSettings.id.length);
			var q = new ReposSearchQuery(qname, query, uiSettings.parent, list);
			// result presentation
			list.bind('repos-search-result', function(ev, microformatElement, solrDoc) {
				$(microformatElement).css(uiCss.result);
				$('.repos-search-resultindex', microformatElement).css(uiCss.resultindex);
			});
			list.bind('repos-search-noresults', function() {
				var nohits = $('<li class="repos-search-nohits"/>').text('No hits').appendTo(this);
			});
			list.bind('repos-search-truncated', function(ev, start, shown, numFound) {
				var next = $('<li class="repos-search-next"/>').appendTo(this);
				var nexta = $('<a href="javascript:void(0)"/>').html('&raquo; more results').click(function() {
					$('.repos-search-result', list).css(uiCss.resultPrevious);
					next.remove();
					q.pageNext();
				}).appendTo(next);
			});	
		});
		
		// close button at bottom of dialog
		var closeBottom = $('.repos-search-dialog-close-button', this.dialog).clone(true).css(uiCss.closeBottom);
		closeBottom.appendTo(this.dialog);
			
		// show ui
		this.dialog.show('slow');
	
		// run query for metadata by default
		meta.trigger('enable');
		// automatically search fulltext if there are no results in meta
		$('ul, ol', meta).one('repos-search-noresults', function() {
			content.trigger('enable');
		});
	};
	
	/**
	 * Creates container for a query type.
	 * @param {String} id The query type id
	 * @param {String} headline Text to explain the query
	 * @return {jQuery} the div, UI events will be triggered on this div
	 * @private Not tested to be callable from outside LightUI
	 */
	this.queryCreate = function(id, headline) {
		var div = $('<div/>').attr('id', id + '-div').css(uiCss.queryDiv);
		var h = $('<h3/>').text(headline).css(uiCss.headline).appendTo(div);
		// checkbox to enable/disable
		var c = $('<input type="checkbox">').attr('id', id + '-enable').prependTo(h);
		c.css(uiCss.headlineCheckbox).change(function(){
			if ($(this).is(':checked')) {
				div.trigger('enabled', [id]);
			} else {
				div.trigger('disabled', [id]);
			}
		});
		// event to programmatically enable/disable
		div.bind('enable', function() {
			var c = $(':checkbox', this);
			if (!c.is(':checked')) {
				c.attr('checked', true).trigger('change');
			}
		});
		// there's always someting	
		if ($.browser.msie) this.fixIE(div);
		// return the element that gets the events, use .parent() to get the div
		div.appendTo(this.dialog);
		return div;
	};
	
	/**
	 * @return {jQuery} Title div
	 * @private
	 */
	this.titleCreate = function() {
		var title = $('<div class="repos-search-dialog-title"/>').css(uiCss.dialogTitle)
			.append($('<a target="_blank" href="http://repossearch.com/" title="repossearch.com">Repos Search</a>"')
			.attr('id', this.settings.id+'dialog-title-link').css(uiCss.dialogTitleLink));
		$('<span class="repos-search-dialog-title-separator"/>').text(' - ').appendTo(title);
		$('<em class="repos-search-dialog-title-label"/>').appendTo(title);
		return title;
	};
		
	this.fixIE = function(context) {
		$(':checkbox', context).click(function(ev) {
			ev.stopPropagation();
			$(this).attr('checked', $(this).is(':checked')).trigger('change');
		});
	};

	// init light dialog, hidden until we have a query
	this.dialog = $('<div/>').attr('id', this.settings.id+'dialog').css(uiCss.dialog);
	
	var title = this.titleCreate();
	this.dialog.append(title);
	
	var closeAction = $('<a href="javascript:void(0)" class="repos-search-dialog-close-button">close</a>').css(uiCss.close).click(this.destroy);
	title.append(closeAction);

	$('body').append(this.dialog.hide());
	
	// publish page wide event so extensions can get hold of search events
	$().trigger('repos-search-dialog-open', [this.dialog[0]]);	
	
};

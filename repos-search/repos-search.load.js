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

// dependencies
if (!$.param) { // http://gist.github.com/206323
	(function($){var r20=/%20/g;$.param=function(a,traditional){var s=[];if(traditional===undefined){traditional=jQuery.ajaxSettings.traditional;}
	if(jQuery.isArray(a)||a.jquery){jQuery.each(a,function(){add(this.name,this.value);});}else{for(var prefix in a){buildParams(prefix,a[prefix]);}}
	return s.join("&").replace(r20,"+");function buildParams(prefix,obj){if(jQuery.isArray(obj)){jQuery.each(obj,function(i,v){if(traditional||/\[\]$/.test(prefix)){add(prefix,v);}else{buildParams(prefix+"["+(typeof v==="object"||jQuery.isArray(v)?i:"")+"]",v);}});}else if(!traditional&&obj!=null&&typeof obj==="object"){jQuery.each(obj,function(k,v){buildParams(prefix+"["+k+"]",v);});}else{add(prefix,obj);}}
	function add(key,value){value=jQuery.isFunction(value)?value():value;s[s.length]=encodeURIComponent(key)+"="+encodeURIComponent(value);}}})(jQuery);
}

if (!$.bbq) {
	/*
	 * jQuery BBQ: Back Button & Query Library - v1.2.1 - 2/17/2010
	 * http://benalman.com/projects/jquery-bbq-plugin/
	 * 
	 * Copyright (c) 2010 "Cowboy" Ben Alman
	 * Dual licensed under the MIT and GPL licenses.
	 * http://benalman.com/about/license/
	 */
	(function($,p){var i,m=Array.prototype.slice,r=decodeURIComponent,a=$.param,c,l,v,b=$.bbq=$.bbq||{},q,u,j,e=$.event.special,d="hashchange",A="querystring",D="fragment",y="elemUrlAttr",g="location",k="href",t="src",x=/^.*\?|#.*$/g,w=/^.*\#/,h,C={};function E(F){return typeof F==="string"}function B(G){var F=m.call(arguments,1);return function(){return G.apply(this,F.concat(m.call(arguments)))}}function n(F){return F.replace(/^[^#]*#?(.*)$/,"$1")}function o(F){return F.replace(/(?:^[^?#]*\?([^#]*).*$)?.*/,"$1")}function f(H,M,F,I,G){var O,L,K,N,J;if(I!==i){K=F.match(H?/^([^#]*)\#?(.*)$/:/^([^#?]*)\??([^#]*)(#?.*)/);J=K[3]||"";if(G===2&&E(I)){L=I.replace(H?w:x,"")}else{N=l(K[2]);I=E(I)?l[H?D:A](I):I;L=G===2?I:G===1?$.extend({},I,N):$.extend({},N,I);L=a(L);if(H){L=L.replace(h,r)}}O=K[1]+(H?"#":L||!K[1]?"?":"")+L+J}else{O=M(F!==i?F:p[g][k])}return O}a[A]=B(f,0,o);a[D]=c=B(f,1,n);c.noEscape=function(G){G=G||"";var F=$.map(G.split(""),encodeURIComponent);h=new RegExp(F.join("|"),"g")};c.noEscape(",/");$.deparam=l=function(I,F){var H={},G={"true":!0,"false":!1,"null":null};$.each(I.replace(/\+/g," ").split("&"),function(L,Q){var K=Q.split("="),P=r(K[0]),J,O=H,M=0,R=P.split("]["),N=R.length-1;if(/\[/.test(R[0])&&/\]$/.test(R[N])){R[N]=R[N].replace(/\]$/,"");R=R.shift().split("[").concat(R);N=R.length-1}else{N=0}if(K.length===2){J=r(K[1]);if(F){J=J&&!isNaN(J)?+J:J==="undefined"?i:G[J]!==i?G[J]:J}if(N){for(;M<=N;M++){P=R[M]===""?O.length:R[M];O=O[P]=M<N?O[P]||(R[M+1]&&isNaN(R[M+1])?{}:[]):J}}else{if($.isArray(H[P])){H[P].push(J)}else{if(H[P]!==i){H[P]=[H[P],J]}else{H[P]=J}}}}else{if(P){H[P]=F?i:""}}});return H};function z(H,F,G){if(F===i||typeof F==="boolean"){G=F;F=a[H?D:A]()}else{F=E(F)?F.replace(H?w:x,""):F}return l(F,G)}l[A]=B(z,0);l[D]=v=B(z,1);$[y]||($[y]=function(F){return $.extend(C,F)})({a:k,base:k,iframe:t,img:t,input:t,form:"action",link:k,script:t});j=$[y];function s(I,G,H,F){if(!E(H)&&typeof H!=="object"){F=H;H=G;G=i}return this.each(function(){var L=$(this),J=G||j()[(this.nodeName||"").toLowerCase()]||"",K=J&&L.attr(J)||"";L.attr(J,a[I](K,H,F))})}$.fn[A]=B(s,A);$.fn[D]=B(s,D);b.pushState=q=function(I,F){if(E(I)&&/^#/.test(I)&&F===i){F=2}var H=I!==i,G=c(p[g][k],H?I:{},H?F:2);p[g][k]=G+(/#/.test(G)?"":"#")};b.getState=u=function(F,G){return F===i||typeof F==="boolean"?v(F):v(G)[F]};b.removeState=function(F){var G={};if(F!==i){G=u();$.each($.isArray(F)?F:arguments,function(I,H){delete G[H]})}q(G,2)};e[d]=$.extend(e[d],{add:function(F){var H;function G(J){var I=J[D]=c();J.getState=function(K,L){return K===i||typeof K==="boolean"?l(I,K):l(I,L)[K]};H.apply(this,arguments)}if($.isFunction(F)){H=F;return G}else{H=F.handler;F.handler=G}}})})(jQuery,this);
	/*
	 * jQuery hashchange event - v1.2 - 2/11/2010
	 * http://benalman.com/projects/jquery-hashchange-plugin/
	 * 
	 * Copyright (c) 2010 "Cowboy" Ben Alman
	 * Dual licensed under the MIT and GPL licenses.
	 * http://benalman.com/about/license/
	 */
	(function($,i,b){var j,k=$.event.special,c="location",d="hashchange",l="href",f=$.browser,g=document.documentMode,h=f.msie&&(g===b||g<8),e="on"+d in i&&!h;function a(m){m=m||i[c][l];return m.replace(/^[^#]*#?(.*)$/,"$1")}$[d+"Delay"]=100;k[d]=$.extend(k[d],{setup:function(){if(e){return false}$(j.start)},teardown:function(){if(e){return false}$(j.stop)}});j=(function(){var m={},r,n,o,q;function p(){o=q=function(s){return s};if(h){n=$('<iframe src="javascript:0"/>').hide().insertAfter("body")[0].contentWindow;q=function(){return a(n.document[c][l])};o=function(u,s){if(u!==s){var t=n.document;t.open().close();t[c].hash="#"+u}};o(a())}}m.start=function(){if(r){return}var t=a();o||p();(function s(){var v=a(),u=q(t);if(v!==t){o(t=v,u);$(i).trigger(d)}else{if(u!==t){i[c][l]=i[c][l].replace(/#.*/,"")+"#"+u}}r=setTimeout(s,$[d+"Delay"])})()};m.stop=function(){if(!n){r&&clearTimeout(r);r=0}};return m})()})(jQuery,this);	
}

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
	// initialize query class
	settings.uiUrl = settings.uiUrl || settings.url;
	ReposSearchRequest.prototype.url = settings.url || ReposSearchRequest.prototype.url;
	// use mini search box input to invoke Repos Search sample ui
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

ReposSearch.images = {
	magnifier: 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAAAAAA6mKC9AAAAxUlEQVQYGVWOzwqCQBDGv11FiFBEESLoJEgQePYFeoLoaYPOdhWKEiOICAlCwoMh7dpMQtFclvnt92dEh/+RvOruh00oqffHK8bhVAr6FEqqNP24koSJKbFL7ThCnqXOjABlFIgTz0tiFIqiCJSI2BKh1PQQ+DZ0qrcEyFmRIwBJTGByzkifZxhxi+hQbbasAJyFKxk868PlDt8/1e7SFgR027QvGKJeE3EoA5ahFdUN5qv65pCisQxO0KqpHuGQAC98Tz9vISxGFMQIZLQAAAAASUVORK5CYII=',
	loading: 'data:image/gif;base64,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',
	close: 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAA0AAAANCAMAAABFNRROAAAABGdBTUEAANbY1E9YMgAAABl0RVh0U29mdHdhcmUAQWRvYmUgSW1hZ2VSZWFkeXHJZTwAAAAGUExURSQiJP///621nPAAAAACdFJOU/8A5bcwSgAAADFJREFUeNpiYEQGDOg8BgaQEJiE8BggBIzHAOcxwjkQU2AcTDlUfRhmItmH02UAAQYAJa4AaSNjZIQAAAAASUVORK5CYII='
};

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
		background: "white url('" + ReposSearch.images.magnifier + "') no-repeat right"
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
		float: 'right',
		fontSize: '82.5%',
		cursor: 'pointer',
		color: '#666',
		padding: '2px 5px 2px 20px'
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
	resultinfo: {
		listStyleType: 'none',
		fontSize: '82.5%',
		lineHeight: '200%'
	},
	pagelink: {
		paddingLeft: '.3em',
		paddingRight: '.3em'
	},
	result: {
		marginLeft: '1em',
		textIndent: '-1em'
	},
	resultindex: {
		display: 'none'
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
			// old global event
			$().trigger('repossearch-query-returned', [params.qt, json]);
			// new handling based on callback
			instance.json = json;
			options.success(instance);
		},
		error: function (xhr, textStatus, errorThrown) {
			// old global event
			$().trigger('repossearch-query-failed', [params.qt, xhr.status, xhr.statusText]);
			// new handling based on callback
			options.error(instance, xhr.status, xhr.statusText);
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
 * Takes the user's query and a result container and produces,
 * at .exec(), a series of search events.
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
	// signal that a query type has been initiated
	$().trigger('repossearch-started', [this.type, this.query, this.listE]);	
}

ReposSearchQuery.prototype.setStart = function(fromZero) {
	this.start = fromZero;
};

ReposSearchQuery.prototype.exec = function() {
	var instance = this;
	var listQ = this.listQ; // closure scope
	this.r = new ReposSearchRequest({
		type: this.type,
		q: this.query,
		start: this.start,
		success: function(searchRequest) {
			// This event can be used to hide previous results, if there are any
			listQ.trigger('repossearch-query-returned', [searchRequest]);
			instance.presentResults(searchRequest.json, listQ);
		},
		error: function(searchRequest, httpStatus, httpStatusText) {
			listQ.trigger('repossearch-query-failed', [searchRequest, httpStatus, httpStatusText]);
		}
	});
	listQ.trigger('repossearch-query-sent', [this.r]);
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
		listQ.trigger('repossearch-noresults');
		return;
	}
	var n = json.response.docs.length;
	for (var i = 0; i < n; i++) {
		var doc = json.response.docs[i];
		var e = this.presentItem(doc);
		e.addClass(i % 2 ? 'even' : 'odd');
		listQ.append(e);
		listQ.trigger('repossearch-result', [e[0], doc, start + i]); // event arg is the element, not jQuery bucket
	}
	listQ.trigger('repossearch-displayed', [json.response.start, n, num]);
};

/**
 * Produce the element that presents a search hit.
 * 
 * The element is also a microformat for processing in repossearch-result event handlers:
 * $('.repossearch-resultbase').text() contains the base
 * $('.repossearch-resultpath').text() contains path to file excluding filename
 * $('.repossearch-resultfile').text() contains filename
 * 
 * @param json the item from the solr "response.docs" array
 * @return jQuery element
 */
ReposSearchQuery.prototype.presentItem = function(json) {
	var m = /(.*\/)?([^\/]*)?\^(\/?.*\/)([^\/]*)/.exec(json.id);
	if (!m) return $("<li/>").text("Unknown id format in seach result: " + json.id);
	var li = $('<li/>').addClass('repossearch-result');
	var root = m[1] || this.parentUrl || this.parentUrlDefault;
	if (m[2]) {
		root += m[2];
		li.append('<a class="repossearch-resultbase" href="' + root + '/">' + m[2] + '</a>');
	}
	li.append('<a class="repossearch-resultpath" href="' + root + m[3] + '">' + m[3] + '</a>');
	li.append('<a class="repossearch-resultfile" href="' + root + m[3] + m[4] + '">' + m[4] + '</a>');
	var indexed = $('<dl class="repossearch-resultindex"/>').appendTo(li);
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
	$().bind('repossearch-started', function(ev, type, userQuery, r) {
		logger.log(ev.type, this, type, userQuery, r);
		
		$(r).bind('repossearch-query-sent', function(ev, searchRequest) {
			logger.log(ev.type, this, searchRequest);
		});
		$(r).bind('repossearch-query-returned', function(ev, searchRequest) {
			logger.log(ev.type, this, searchRequest);
		});
		$(r).bind('repossearch-query-failed', function(ev, searchRequest, httpStatus, httpStatusText) {
			logger.log(ev.type, this, searchRequest, 'status=' + httpStatus + ' statusText=' + httpStatusText);
		});
		$(r).bind('repossearch-result', function(ev, microformatElement, solrDoc, hitNumber) {
			var e = microformatElement;
			logger.log(ev.type, this, e, hitNumber,
				'base=' + $('.repossearch-resultbase', e).text(),
				'path=' + $('.repossearch-resultpath', e).text(),
				'file=' + $('.repossearch-resultfile', e).text(),
				solrDoc);
		});
		$(r).bind('repossearch-displayed', function(ev, start, shown, numFound) {
			logger.log(ev.type, this, 'showed from index ' + (start) + ' to ' + (start+shown) + ', total count ' + numFound);
		});
	});
	
	// LightUI's events, triggered on the divs
	$().bind('repossearch-dialog-open', function(ev, dialog) {
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
		box: $('<input id="repossearch-input" type="text" name="repossearch" size="20"/>').css(options.css.input),
		
		// the page that includes Repos Search can provide an element with
		// class "repossearch-container" to control the placement of the input box
		boxparent: $('.repossearch-container')[0] || $('#commandbar')[0] || $('body')[0],
		
		// how to get search terms from the input box
		getSearchString: function() {
			return $('#repossearch-input').val();
		},
		
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
	var form = $('<form id="repossearch-form"><input type="submit" style="display:none"/></form>');
	form.append(settings.box);
	form.css(options.css.form).appendTo(settings.boxparent);
	// make search box icon clickable
	settings.box.click(function(ev) {
		if (!$(this).val()) return; // don't react on click if input is empty
		var iconw = 20; // clickable area's width in pixels
		var clickx = ev.pageX;
		var inputright = $(this).offset().left + $(this).width(); // x coordinate of right border of input with icon
		if (clickx >= inputright - iconw) {
			form.submit();
		}
	});
	// get current query string
	var qs = $.deparam.querystring();
	// preserve existing params in submit
	for (var qsp in qs) {
		if (qsp == 'repossearch') continue;
		$('<input type="hidden"/>').attr('name', qsp).attr('value', qs[qsp]).appendTo(form);
	}
	form.attr('method', 'GET').attr('action', '#'); // as long as IE resets hash on submit we must set action=# for consistency
	// display current search query, and invoke search
	if (qs.repossearch) {
		$('#repossearch-input').val(qs.repossearch);
		settings.submit();
	}
	// the search UI decides the execution model, and this one supports only one search at a time
	$().bind('repossearch-dialog-close', function(ev, dialog) {
		$().trigger('repossearch-exited');
		form.attr('action', '#'); // removes state, maybe done by 'disabled' event handler too
		form.submit();
	});
	// update mini UI based on dialog events
	$().bind('repossearch-exited', function() {
		$('#repossearch-input').val('');
	});
	$().bind('repossearch-input-change', function(ev, searchString) {
		$('#repossearch-input').val(searchString);
	});	
};

/**
 * Very lightweight presentation of search results.
 * @param {Object} options
 * @constructor
 */
ReposSearch.LightUI = function(options) {
	
	this.settings = $.extend({
		id: 'repossearch-',
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
		$().trigger('repossearch-dialog-close', [d[0]]);
		d.remove();
	};
	
	/**
	 * Creates interactive search result presentation.
	 * @param {String} query Valid solr query from the user
	 */
	this.run = function(query) {
		var that = this;
		$('.repossearch-dialog-title-label', this.dialog).text(query);
		var meta = this.queryCreate(uiSettings.id + 'meta', 'Titles and keywords');
		var content = this.queryCreate(uiSettings.id + 'content', 'Text contents');
		var all = $(meta).add(content);
		all.bind('disabled', function(ev, id) {
			$('ul, ol', this).remove();
			$.bbq.removeState(id + '-start');
		}).bind('enabled', function(ev, id) {
			var setQueryState = function(startIndex) {
				var nextstart = {};
				nextstart[id + '-start'] = startIndex;
				$.bbq.pushState(nextstart);
			};
			if (typeof $.deparam.fragment()[id + '-start'] == 'undefined') setQueryState(0); // API not well defined, who sets the hash?
			var list = $('<ul/>').attr('id', id).addClass('repossearch-result-list').css(uiCss.list).appendTo(this);
			var qname = list.attr('id').substr(uiSettings.id.length);
			
			// result presentation
			list.bind('repossearch-query-sent', function() {
				$('.repossearch-result', list).remove();
			});
			list.bind('repossearch-result', function(ev, microformatElement, solrDoc, hitNumber) {
				$(microformatElement).css(uiCss.result);
				$('.repossearch-resultindex', microformatElement).css(uiCss.resultindex);
			});
			list.bind('repossearch-noresults', function() {
				var nohits = $('<li class="repossearch-nohits"/>').css(uiCss.resultinfo).text('No hits').appendTo(this);
				list.one('repossearch-query-sent', function() {
					nohits.remove();
				});	
			});
			list.bind('repossearch-displayed', function(ev, start, shown, numFound) {
				var pagesize = 10;
				if (numFound <= pagesize) return;
				if (start % pagesize !== 0) {
					return; // paging not supported if start index does not match page size
				}
				var pages = $('<span class="repossearch-resultpages"/>');
				var link = function(start, size) {
					return $('<a href="javascript:void(0)" class="repossearch-resultpage"/>')
						.css(uiCss.pagelink)
						.text('' + (start + 1) + '-' + (start + size))
						.click(function() {
							setQueryState(start);
							search(); // instead of relying on hashchange
						});
				};
				// generate page links
				for (var s = 0; s < Math.min(numFound, Math.max(pagesize * 10, start + pagesize * 5)); s += pagesize) {
					var p = link(s, Math.min(pagesize, numFound - s)).appendTo(pages);
				};
				// current page
				var current = $('> :eq(' + Math.floor(start / pagesize) + ')', pages);
				current.prev().clone(true).add('<span/>').slice(0,1).html('&laquo;').prependTo(pages);
				current.next().clone(true).add('<span/>').slice(0,1).html('&raquo;').appendTo(pages);
				// mark current page
				current = current.replaceWith($('<span/>').text(current.text()).attr('class', current.attr('class')).attr('style', current.attr('style')));
				// add to result element
				var pageinfo = $('<li class="repossearch-resultinfo"/>').css(uiCss.resultinfo);
				pageinfo.append(pages).appendTo(this);
				// show at top too://pageinfo = $([pageinfo[0], pageinfo.clone(true).prependTo(this)[0]]);
				$(this).one('repossearch-query-sent', function() {
					pageinfo.remove();
				});
			});
			list.bind('repossearch-query-failed', function(ev, searchRequest, httpStatus, httpStatusText) {
				var error = $('<li class="error repossearch-error"/>').css(uiCss.resultinfo).appendTo(this);
				$('<span/>').text('Error, server status ' + httpStatus).appendTo(error);
				$('<pre/>').text(httpStatusText).appendTo(error);
				list.one('repossearch-query-sent', function() {
					error.remove();
				});
			});
			// loading animation
			var loading = $('<img/>').addClass('loading').attr('src', ReposSearch.images.loading).css({marginLeft: 20});
			list.bind('repossearch-query-sent', function() {
				$(this).parent().append(loading);
			}).bind('repossearch-query-returned', function() {
				loading.remove();
			}).bind('repossearch-query-failed', function() {
				loading.remove();
			});
			// run search request
			var q = new ReposSearchQuery(qname, query, uiSettings.parent, list);
			var search = function() {
				var start = $.deparam.fragment()[id + '-start'] || 0;
				q.setStart(start);
				q.exec();
			};
			// might cause multiple searches if handler does not chech which state it was that changed
			//$(window).bind('hashchange', search);
			// in this UI enable means search immediately
			search();
		});
		
		// show ui
		this.dialog.show('slow');
	
		// run query directly if set in bookmarkable hash
		if (location.hash) {
			var hash = $.deparam.fragment();
			if (typeof hash[uiSettings.id + 'meta-start'] != 'undefined') {
				meta.trigger('enable');
			}
			if (typeof hash[uiSettings.id + 'content-start'] != 'undefined') {
				content.trigger('enable');
			}
		} else {
			// default after submit
			meta.trigger('enable');
			// automatically search fulltext if there are no results in meta
			$('ul, ol', meta).one('repossearch-noresults', function() {
				// TODO set hash, and set/unset hash och checkbox click
				content.trigger('enable');
			});
		}
		// Instead of the above, we could have a generic hashchange handler here
		// probably with a trigger onload
		// which should also replace the hashchange handling in run		
		// but how do we detect which search query that changed?
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
		// event to programmatically enable, unlike 'enabled' which is triggered any time the query type is started
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
		var title = $('<div class="repossearch-dialog-title"/>').css(uiCss.dialogTitle)
			.append($('<a target="_blank" href="http://repossearch.com/" title="repossearch.com">Repos Search</a>"')
			.attr('id', this.settings.id+'dialog-title-link').css(uiCss.dialogTitleLink));
		$('<img alt="close"/>').attr('src', ReposSearch.images.close).css(uiCss.close).click(this.destroy).prependTo(title);
		$('<span class="repossearch-dialog-title-separator"/>').text(' - ').appendTo(title);
		$('<em class="repossearch-dialog-title-label"/>').appendTo(title);
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
	
	$('body').append(this.dialog.hide());
	
	// publish page wide event so extensions can get hold of search events
	$().trigger('repossearch-dialog-open', [this.dialog[0]]);	
	
};

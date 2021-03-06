
module('static');

test('global settings', function() {
	/*
	ok(ReposSearch.options, "There should be a static global settings object with defaults");
	ok(ReposSearch.options.onready, "Autostart property should exist");
	equals(typeof ReposSearch.options.onready, 'function', 'default onload should start the mini GUI');
	*/
	// disable onready so that no code is executed automatically
	ReposSearch.onready = null;
});

test('getFieldsToShow', function() {
	var f = ReposSearch.getPropFields({c:null, a:null, title:null, b:null});
	equals(f.length, 4);
	equals(f[0], 'title');
	equals(f[1], 'a');
	equals(f[2], 'b');
	equals(f[3], 'c');
});

test('presentItem', function() {
	var doc = {
		id: 'arepo^/file.txt',
		svnprop_some_prop: 'some prop value'
	};
	var q = new ReposSearchQuery();
	var li = q.presentItem(doc);
	// test the microformat
	equals($('.repos-search-resultbase', li).text(), 'arepo',
		'base should be the part from the last slash in prefix to the root marker');
	equals($('.repos-search-resultpath', li).text(),'/');
	equals($('.repos-search-resultfile', li).text(),'file.txt');
	var fields = $('dl.repos-search-resultindex', li);
	ok(fields.size(), 'Should find a dl with fields');
});

test('presentItemWithPrefix', function() {
	var doc = {
		// for absolute URLs id can start with slash or the full protocol+hostname
		id: 'whatever/r1^/file.txt'
	};
	var q = new ReposSearchQuery();
	var li = q.presentItem(doc);
	console.log(li);
	var base = $('.repos-search-resultbase', li);
	equals(base.text(), 'r1', 'base should be the part from the last slash in prefix to the root marker');
	equals(base.attr('href'), 'whatever/r1/', 'basse url should use the prefix from id');
});

test('presentItemOnlyPrefix', function() {
	var doc = {
		// we can not distinguish base from nobase unless prefix ends with /
		id: '/someprefix/^/file.txt'
	};
	var q = new ReposSearchQuery();
	var li = q.presentItem(doc);
	console.log(li);
	var base = $('.repos-search-resultbase', li);
	equals(base.size(), 0, 'no base in this id');
});

module('solr requests');

test('new reqest', function() {
	// mock ajax
	var _a = $.ajax
	$.ajax = function(opt) {
		ok(opt.url, 'Should set a solr select URI');
		ok(opt.data, 'Should have parameters');
		equals(opt.data.q, 'paint');
		equals(opt.data.qt, 'meta');
		equals(typeof opt.success, 'function');
		
		// mock data copied from an actual solr response 
		docs = [{"svnprop_svn_mime_type":"application/octet-stream",
				 "svnrevision":13,
				 "id":"repo1^/Images/Paint.png",
				 "content_type":["image/png"]}];
		opt.success(
			{"responseHeader":{
			  "status":0,
			  "QTime":1},
			 "response":{"numFound":2,"start":1,"docs":docs
			 }});
	};
	
	// run with query specific parameters, request object should handle the rest
	var test = {};
	new ReposSearchRequest({
		q: 'paint',
		type: 'meta',
		start: 1,
		success: function(req) {
			test.req = req;
		}
	});
	// normally this is asynchronous and nothing has happended yet
	ok(test.req.getDocs(), 'After callback there should be a response');
	equals(test.req.getStart(), 1);
	equals(test.req.getNumFound(), 2);
	equals(test.req.getNumReturned(), 1);
	equals(test.req.getDocs().length, 1);
	
	// unmock
	$.ajax = _a;
});

module('query abstraction');

test('search interaction', function() {
	// mock query
	var _r = ReposSearchRequest;
	ReposSearchRequest = function(options) {
		equals(options.q, 'repos search', 'Query should be passed on to search request');
		if (options.type == 'meta') {
			this.json = {
				response: {
					docs: [{
						"svnprop_svn_mime_type": "application/octet-stream",
						"svnrevision": 13,
						"id": "repo1/Images/Paint.png",
						"content_type": ["image/png"]
					}]
				}
			};
		}
		options.success(this);
	};
	// log all events for later assertions
	var testlog = {
		logged: [],
		log: function() {
			this.logged.push(arguments);
		},
		assert: function(f) {
			ok(this.logged.length > 0, 'should have got event');
			f(this.logged.shift());
		}
	};
	new ReposSearch.EventLogger(testlog);
	
	// new query instance
	var list = $('<ol/>');
	var q = new ReposSearchQuery('meta', 'repos search', '/svn', list);
	testlog.assert(function(a) {
		equals(a[0], 'repos-search-started');
		equals(a[2], 'meta');
		equals(a[3], 'repos search');
		equals(a[4], list[0], 'event should see the element, not the jQuery object');
	});
	// request mock is synchronous so the query should return immediately
	testlog.assert(function(a) {
		equals(a[0], 'repos-search-query-returned');
		equals(a[1], list[0]);
		ok(a[2].json, 'public json needed because presentItem was written before the class-based design');
	});
	// request mock is synchronous so the query should return immediately
	testlog.assert(function(a) {
		equals(a[0], 'repos-search-result');
		equals(a[1], list[0]);
	});
	
	// happens after results because mock is synchronous
	// query with default parameters should be sent directly
	testlog.assert(function(a) {
		equals(a[0], 'repos-search-query-sent');
		equals(a[1], list[0]);
	});
	
	// unmock
	ReposSearchRequest = _r;
});


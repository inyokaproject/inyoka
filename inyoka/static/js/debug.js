/*
  debug tools
  ===========

  features:
  - overlay basic 20px pattern
  - overlay orientation 100px pattern
  - overlay grid
  - analyse html elements
  - use via menu or keybindings

  Taken with permissions from Martin Balfanz <martin@defadvice.org>

*/

var keyCodes = {
  shift: 16, ctrl: 17, alt: 18,
  a: 65, b: 66, c: 67, d: 68, e: 69, f: 70,
  g: 71, h: 72, i: 73, j: 74, k: 75, l: 76,
  m: 77, n: 78, o: 79, p: 80, q: 81, r: 82,
  s: 83, t: 84, u: 85, v: 86, w: 87, x: 88,
  y: 89, z:90
};

function getDocumentHeight () {
  // return document height, or min-height of 1000
  if (document.body !== null) {
    return Math.max(
      Math.max(document.body.scrollHeight, document.documentElement.scrollHeight),
      Math.max(document.body.offsetHeight, document.documentElement.offsetHeight),
      Math.max(document.body.clientHeight, document.documentElement.clientHeight)
    );
  } else {
    return 1000;
  }
}

function toggle(id) {
  var el = document.getElementById(id);
  if (el.style.length !== 0) {
    el.removeAttribute('style');
  } else {
    el.setAttribute('style', 'display:none;');
  }
}

function addElement(elem, id) {
  var el = document.createElement(elem);
  el.setAttribute('id', id);
  document.body.appendChild(el);
}

function debugTools() {
  this.columns = 24;
  this.columnWidth = 30;
  this.gutterWidth = 10;
  this.contentWidth = this.columns * this.columnWidth + (this.columns - 1) * this.gutterWidth;
  this.contentHeight = getDocumentHeight();

  this.style = {
    debugMenu: '#debug-menu { ' +
      'background:rgba(0,0,0,.5);' +
      'color:#ddd;' +
      'z-index:100;' +
      'position:fixed;' +
      'top:0;' +
      'left:0px;' +
      'padding:15px;' +
      '-moz-border-radius-bottomright:10px;' +
      '-webkit-border-bottom-right-radius:10px;' +
      'border-bottom-right-radius:10px;' +
      '-webkit-transition:left .25s ease-out;' +
      '-moz-transition:left .25s ease-out;' +
      '-o-transition:left .25s ease-out;' +
      'transition:left .25s ease-out;' +
      '}' +
      '#debug-menu:hover {' +
      'left:0;' +
      '-webkit-transition:left .25s ease-out;' +
      '-moz-transition:left .25s ease-out;' +
      '-o-transition:left .25s ease-out;' +
      'transition:left .25s ease-out;' +
      '}' +
      '#debug-menu a {' +
      'font:11px/1.231 Menlo, monospace;' +
      'color:#ddd;' +
      'text-decoration:none;' +
      '-webkit-transition:color .25s ease-in;' +
      '-moz-transition:color .25s ease-in;' +
      '-o-transition:color .25s ease-in;' +
      'transition:color .25s ease-in;' +
      '}' +
      '#debug-menu a:hover {' +
      'color:#fff;' +
      '-webkit-transition:color .25s ease-in;' +
      '-moz-transition:color .25s ease-in;' +
      '-o-transition:color .25s ease-in;' +
      'transition:color .25s ease-in;' +
      '}' +
      '#debug-menu ul, #debug-menu li {' +
      'list-style-type:none;' +
      'padding:0;' +
      'margin:0;} ',
    debugGrid: '#debug-grid {' +
      'height: 100%;' +
      'width: 100%;' +
      'position: fixed;' +
      'opacity: .33;' +
      'z-index: 66;' +
      'top: 0;' +
      '}' +
      '#debug-grid .content {' +
      'height: 100%;' +
      'width: ' + this.contentWidth + 'px;' +
      'margin: 0 auto;' +
      'outline: 10px solid #333;' +
      '}' +
      '#debug-grid .content > div {' +
      'width: ' + this.columnWidth + 'px;' +
      'margin-right: ' + this.gutterWidth + 'px;' +
      'height: 100%;' +
      'background: #ff5e99;' +
      'float: left;' +
      '}' +
      '#debug-grid .content > div:last-child {' +
      'margin-right: 0;}',
    debugPattern: '#debug-pattern {' +
      'background: url(data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABQAAAAUAgMAAADw5/WeAAAACVBMVEUAAAAAiv8Aiv9KXthOAAAAA3RSTlMAVKj8rHdUAAAAJklEQVQIW2NcxQAEjA0NLH+A5IQvf/+jsFsOgGUxxCHsqQfI1gsA34Y0nMzmY4kAAAAASUVORK5CYII=);' +
      'height: ' + this.contentHeight + 'px;' +
      'width: 100%;' +
      'position: absolute;' +
      'top: 0;' +
      'left: 0;' +
      'opacity: .33;' +
      'z-index: 60;}',
    debugOrientation: '#debug-orientation {' +
      'background: url(data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAGQAAABkAgMAAAANjH3HAAAACVBMVEX///9/AAB/AADbiDkkAAAAA3RSTlMAqACcqPI/AAAANUlEQVRIS2MIY8AORBmycMho4pFZgEOGCY/MKBgFo2AUjIJRMApGwSigDkjAIc6IRwZnaxAAWwwEA+q99U0AAAAASUVORK5CYII=);' +
      'height: ' + this.contentHeight + 'px;' +
      'width: 100%;' +
      'position: absolute;' +
      'top: 0;' +
      'left: 0;' +
      'opacity: .33;' +
      'z-index: 61;}',
    debugEmptyElements: '/* inspired by Eric Meyer */' +
      'div:empty, span:empty,' +
      'li:empty, p:empty,' +
      'td:empty, th:empty {padding: 0.5em; background: yellow;}' +
      '*[style], font, center {outline: 5px solid red;}' +
      '*[class=""], *[id=""] {outline: 5px dotted red;}' +
      'img[alt=""] {border: 3px dotted red;}' +
      'img:not([alt]) {border: 5px solid red;}' +
      'img[title=""] {outline: 3px dotted fuchsia;}' +
      'img:not([title]) {outline: 5px solid fuchsia;}' +
      'table:not([summary]) {outline: 5px solid red;}' +
      'table[summary=""] {outline: 3px dotted red;}' +
      'th {border: 2px solid red;}' +
      'th[scope="col"], th[scope="row"] {border: none;}' +
      'a[href]:not([title]) {border: 5px solid red;}' +
      'a[title=""] {outline: 3px dotted red;}' +
      'a[href="#"] {background: lime;}' +
      'a[href=""] {background: fuchsia;}'
  };

  this.init = function () {
    this.defineGrid();
    this.definePattern();
    this.defineOrientation();
    this.defineMenu();

    // hide elements at start
    toggle('debug-grid');
    toggle('debug-pattern');
    toggle('debug-orientation');
    toggle('debug-menu');

    this.defineStyles();
    this.defineShortcuts();
  };

  this.defineGrid = function () {
    addElement('div', 'debug-grid');

    var el = document.getElementById('debug-grid');
    el.innerHTML += '<div class="content"></div>';
    el = el.firstChild;
    var i = 0;
    for (i = 0; i < this.columns; i += 1) {
      el.innerHTML += '<div></div>';
    }
  };

  this.definePattern = function () {
    addElement('div', 'debug-pattern');
  };

  this.defineOrientation = function () {
    addElement('div', 'debug-orientation');
  };

  this.defineMenu = function () {
    addElement('div', 'debug-menu');
    var el = document.getElementById('debug-menu');
    el.innerHTML = '<ul>' +
      '<li><a href="#" title="toggle grid" id="debug-toggle-grid")" onclick="toggle(\'debug-grid\');">toggle grid (C-S-g)</a></li>' +
      '<li><a href="#" title="toggle pattern" id="debug-toggle-pattern" onclick="toggle(\'debug-pattern\');">toggle pattern (C-S-p)</a></li>' +
      '<li><a href="#" title="toggle orientation" id="debug-toggle-orientation" onclick="toggle(\'debug-orientation\');">toggle orientation(C-S-o)</a></li>' +
      '<li><a href="#" title="toggle empty elements" id="debug-toggle-empty-elements" onclick="debugTools.toggleEmptyElements();">toggle empty elements(C-S-e)</a></li>';
  };

  this.defineStyles = function () {
    addElement('style', 'debug-styles');
    var el = document.getElementById('debug-styles');
    el.innerHTML = this.style.debugMenu +
      this.style.debugGrid +
      this.style.debugPattern +
      this.style.debugOrientation;
  };

  this.toggleEmptyElements = function () {
    var el = document.getElementById('debug-empty-elements');
    if (!el) {
      addElement('style', 'debug-empty-elements');
      var tmp = document.getElementById('debug-empty-elements');
      tmp.innerHTML = this.style.debugEmptyElements;
    } else {
      document.body.removeChild(el);
    }
  };

  this.defineShortcuts = function () {
    // define Shortcuts
    var obj = this,
    ctrlDown = false,
    shiftDown = false;

    document.onkeyup = function(key) {
      if (key.which === keyCodes.shift) { shiftDown = false; }
      if (key.which === keyCodes.ctrl) { ctrlDown = false; }
    };

    document.onkeydown = function(key) {
      if (key.which === keyCodes.shift) { shiftDown = true; }
      if (key.which === keyCodes.ctrl) { ctrlDown = true; }

      if (ctrlDown && shiftDown && key.which === keyCodes.e) { obj.toggleEmptyElements(); }
      if (ctrlDown && shiftDown && key.which === keyCodes.g) { toggle('debug-grid'); }
      if (ctrlDown && shiftDown && key.which === keyCodes.o) { toggle('debug-orientation'); }
      if (ctrlDown && shiftDown && key.which === keyCodes.p) { toggle('debug-pattern'); }
      if (ctrlDown && shiftDown && key.which === keyCodes.m) { toggle('debug-menu'); }

      /* if you're on a mac, you can use C-g, C-p, C-e, C-o */
      if (navigator.platform === 'MacIntel' && !shiftDown) {
        if (ctrlDown && key.which === keyCodes.e) { obj.toggleEmptyElements(); }
        if (ctrlDown && key.which === keyCodes.g) { toggle('debug-grid'); }
        if (ctrlDown && key.which === keyCodes.o) { toggle('debug-orientation'); }
        if (ctrlDown && key.which === keyCodes.p) { toggle('debug-pattern'); }
        if (ctrlDown && key.which === keyCodes.m) { toggle('debug-menu'); }
      }
    };
  };
}

debugTools = new debugTools();

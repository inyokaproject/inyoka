// Taken from jQuery source directory, modified for our
// needs. - Christopher Grebs.

load("extra/jslint.js");

var files = 

for (var file in files) {
  var src = readFile("inyoka/static/js/" + files[file]);
  print( "check " + files[file] + " with jslint");

  JSLINT(src, { evil: true, forin: true, maxerr: 100 });

  var e = JSLINT.errors, found = 0, w;

  for ( var i = 0; i < e.length; i++ ) {
    w = e[i];

    if ( !(w.reason.indexOf("Expected '{' and instead saw"))) {
      found++;
      print( "\n" + w.evidence + "\n" );
      print( "    Problem at line " + w.line + " character " + w.character + ": " + w.reason );
    }
  }

  if ( found > 0 ) {
    print( "\n" + found + " Error(s) found." );

  } else {
    print( "JSLint check passed." );
  }
}

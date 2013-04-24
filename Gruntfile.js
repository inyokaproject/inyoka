module.exports = function(grunt) {

  // Project configuration.
  grunt.initConfig({
    pkg: grunt.file.readJSON('package.json'),
    uglify: {
      options: {
        banner: '/*! <%= pkg.name %> <%= grunt.template.today("yyyy-mm-dd") %> */\n'
      },
      build: {
        src: ['inyoka/forum/static/forum/js/overall.m.js',
              'inyoka/static/js/DateTime.js',
              'inyoka/static/js/FeedSelector.js',
              'inyoka/static/js/NewTopic.js',
              'inyoka/static/js/PrivilegeBox.js',
              'inyoka/static/js/UserGroupBos.js',
              'inyoka/static/js/admin.js',
              'inyoka/static/js/forum.js',
              'inyoka/static/js/ikhaya.js',
              'inyoka/static/js/jquery.autocomplete.js',
              'inyoka/static/js/jquery.ba-hashchange.js',
              'inyoka/static/js/jquery.cookie.js',
              'inyoka/static/js/jquery.tokenfield.js',
              'inyoka/static/js/jstableform.js',
              'inyoka/static/js/overall.js',
              'inyoka/static/js/overall.m.js'],
        dest: '<%= pkg.name %>.min.js'
      }
    },
    jshint: {
      all: ['inyoka/static/js/*.js']
    }
  });

  grunt.loadNpmTasks('grunt-contrib-uglify');
  grunt.loadNpmTasks('grunt-contrib-jshint');
  grunt.loadNpmTasks('grunt-contrib-uglify');

  // Default task(s).
  grunt.registerTask('default', ['uglify']);

};

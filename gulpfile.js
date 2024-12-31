var gulp = require('gulp');
var sass = require('gulp-sass')(require('sass'));
var header = require('gulp-header');
var cleanCSS = require('gulp-clean-css');
var rename = require("gulp-rename");
var uglify = require('gulp-uglify');
var pkg = require('./package.json');
var browserSync = require('browser-sync').create();
var colors = require('ansi-colors');
var template = require('lodash.template');


// Set the banner content
var banner = ['/*!\n',
  ' * Start Bootstrap - <%= pkg.title %> v<%= pkg.version %> (<%= pkg.homepage %>)\n',
  ' * Copyright 2013-' + (new Date()).getFullYear(), ' <%= pkg.author %>\n',
  ' * Licensed under <%= pkg.license %> (https://github.com/BlackrockDigital/<%= pkg.name %>/blob/master/LICENSE)\n',
  ' * Modified by Ken Cavagnolo\n',
  ' */\n',
  ''
].join('');

// Copy third party libraries from /node_modules into /vendor
gulp.task('vendor', done => {

  // Bootstrap
  gulp.src([
      './node_modules/bootstrap/dist/**/*',
      '!./node_modules/bootstrap/dist/css/bootstrap-grid*',
      '!./node_modules/bootstrap/dist/css/bootstrap-reboot*'
    ])
    .pipe(gulp.dest('./libs/bootstrap'))

  // Font Awesome
  gulp.src([
      './node_modules/font-awesome/**/*',
      '!./node_modules/font-awesome/{less,less/*}',
      '!./node_modules/font-awesome/{scss,scss/*}',
      '!./node_modules/font-awesome/.*',
      '!./node_modules/font-awesome/*.{txt,json,md}'
    ])
    .pipe(gulp.dest('./libs/font-awesome'))

  // jQuery
  gulp.src([
      './node_modules/jquery/dist/*',
      '!./node_modules/jquery/dist/core.js'
    ])
    .pipe(gulp.dest('./libs/jquery'))

  // jQuery Easing
  gulp.src([
      './node_modules/jquery.easing/*.js'
    ])
    .pipe(gulp.dest('./libs/jquery-easing'))

  done();

});

// Compile SCSS
gulp.task('css:compile', function(done) {
  return gulp.src('./scss/**/*.scss')
    .pipe(sass.sync({outputStyle: 'expanded'})
        .on('error', function (err) { console.log(colors.red('[Error]'), err.toString()); })
     )
    .pipe(header(template(banner), {pkg: pkg}))
    .pipe(gulp.dest('./_includes/css'))
    .on('end', done);
});

// Minify CSS
gulp.task('css:minify', gulp.series('css:compile', function() {
  return gulp.src(['./_includes/css/*.css', '!./_includes/css/*.min.css'])
    .pipe(cleanCSS()
        .on('error', function (err) { console.log(colors.red('[Error]'), err.toString()); })
     )
    .pipe(rename({suffix: '.min'}))
    .pipe(gulp.dest('./_includes/css'))
    .pipe(browserSync.stream());
}));

// CSS
gulp.task('css', gulp.series('css:compile', 'css:minify'));

// Minify JavaScript
gulp.task('js:minify', function() {
  return gulp.src(['./js/*.js', '!./js/*.min.js', '!./js/google*'])
    .pipe(uglify()
        .on('error', function (err) { console.log(colors.red('[Error]'), err.toString()); })
     )
    .pipe(rename({suffix: '.min'}))
    .pipe(header(banner, {pkg: pkg}))
    .pipe(gulp.dest('./js'))
    .pipe(browserSync.stream());
});

// JS
gulp.task('js', gulp.series('js:minify'));

// Default task
gulp.task('default', gulp.series('css', 'js', 'vendor'));

// Configure the browserSync task
gulp.task('browserSync', function() {
  browserSync.init({
    server: {
      baseDir: "./"
    }
  });
});

// Dev task
gulp.task('dev', gulp.series('css', 'js', 'vendor', 'browserSync', function() {
  gulp.watch('./_scss/*.scss', ['css']);
  gulp.watch('./js/*.js', ['js']);
  gulp.watch('./*.html', browserSync.reload);
}));
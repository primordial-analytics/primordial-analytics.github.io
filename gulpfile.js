var gulp = require('gulp');
var sass = require('gulp-sass')(require('sass'));
var header = require('gulp-header');
var cleanCSS = require('gulp-clean-css');
var rename = require("gulp-rename");
var uglify = require('gulp-uglify');
var pkg = require('./package.json');
var browserSync = require('browser-sync').create();
var colors = require('ansi-colors');
var cp = require('child_process');


// Set the banner content
var banner = ['/*!\n',
  ' * Start Bootstrap - <%= pkg.title %> v<%= pkg.version %> (<%= pkg.homepage %>)\n',
  ' * Copyright 2013-' + (new Date()).getFullYear(), ' <%= pkg.author %>\n',
  ' * Licensed under <%= pkg.license %> (https://github.com/BlackrockDigital/<%= pkg.name %>/blob/master/LICENSE)\n',
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
    .pipe(header(banner, {pkg: pkg}))
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

// Build the Jekyll Site
gulp.task('jekyll-build', function (done) {
  return cp.spawn('bundle', ['exec', 'jekyll', 'build'], {stdio: 'inherit'})
    .on('close', done);
});

// Rebuild Jekyll & do page reload
gulp.task('jekyll-rebuild', gulp.series('jekyll-build', function (done) {
  browserSync.reload();
  done();
}));

// Default task
gulp.task('default', gulp.series('css', 'js', 'vendor', 'jekyll-build'));

// Configure the browserSync task
gulp.task('browserSync', function() {
  browserSync.init({
    server: {
      baseDir: "_site"
    }
  });
});

// Dev task
gulp.task('dev', gulp.series('default', 'browserSync', function() {
  gulp.watch('./scss/**/*.scss', gulp.series('css', 'jekyll-rebuild'));
  gulp.watch('./js/*.js', gulp.series('js', 'jekyll-rebuild'));
  gulp.watch(['./*.html', './_includes/*.html', './_layouts/*.html', './_posts/*', './_casestudies/*', './_team/*', './_testimonials/*'], gulp.series('jekyll-rebuild'));
}));
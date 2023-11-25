var gulp = require('gulp');
var uglify = require('gulp-uglify');
var concat = require('gulp-concat');
var sourcemaps = require('gulp-sourcemaps');
var less = require('gulp-less');
var cssmin = require('gulp-cssmin');

gulp.task('js', function() {
    return gulp.src(['d3.v2.min.js',
                     'jquery-1.8.2.min.js',
                     'jquery.simplemodal.js',
                     'jquery.ba-bbq.min.js',
                     'jquery.jsPlumb-1.3.10-all-min.js',
                     'jquery-ui-1.8.24.custom.min.js',
                     'pytutor.js'])
        .pipe(sourcemaps.init({loadMaps: true}))
        .pipe(uglify())
        .pipe(concat(`pytutor-main.min.js`))
        .pipe(sourcemaps.write('./'))
        .pipe(gulp.dest('../extern/'));
});

gulp.task('css', function () {
    return gulp.src(['jquery-ui-1.8.24.custom.css',
                     'pytutor.css'])
        .pipe(less())
        .pipe(cssmin())
        .pipe(concat('pytutor-main.min.css'))
        .pipe(gulp.dest('../extern/'));
});

gulp.task('all', gulp.parallel('js', 'css'));

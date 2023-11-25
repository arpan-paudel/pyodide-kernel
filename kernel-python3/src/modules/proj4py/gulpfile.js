const gulp = require('gulp'),
      uglify = require('gulp-uglify'),
      concat = require('gulp-concat'),
      sourcemaps = require('gulp-sourcemaps');

gulp.task('js', function() {
    return gulp.src(['proj4py/proj4.js'])
        .pipe(sourcemaps.init({loadMaps: true}))
        .pipe(uglify())
        .pipe(concat(`proj4.min.js`))
        .pipe(sourcemaps.write('./'))
        .pipe(gulp.dest('./proj4py/'));
});

gulp.task('all', gulp.parallel('js'));

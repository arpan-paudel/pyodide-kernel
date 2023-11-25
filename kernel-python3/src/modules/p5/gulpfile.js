const gulp = require('gulp'),
      uglify = require('gulp-uglify'),
      concat = require('gulp-concat'),
      sourcemaps = require('gulp-sourcemaps');

gulp.task('js', function() {
    return gulp.src(['p5/p5.js'])
        .pipe(sourcemaps.init({loadMaps: true}))
        .pipe(uglify())
        .pipe(concat(`p5.min.js`))
        .pipe(sourcemaps.write('./'))
        .pipe(gulp.dest('./p5/'));
});

gulp.task('all', gulp.parallel('js'));

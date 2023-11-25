const gulp = require('gulp'),
      uglify = require('gulp-uglify'),
      concat = require('gulp-concat'),
      sourcemaps = require('gulp-sourcemaps');

gulp.task('js', function() {
    return gulp.src(['graphviz/viz.js'])
        .pipe(sourcemaps.init({loadMaps: true}))
        .pipe(uglify())
        .pipe(concat(`viz.min.js`))
        .pipe(sourcemaps.write('./'))
        .pipe(gulp.dest('./graphviz/'));
});

gulp.task('all', gulp.parallel('js'));

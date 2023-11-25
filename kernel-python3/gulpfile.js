const gulp = require("gulp"),
  ts = require("gulp-typescript"),
  merge = require("merge-stream");

/**
 * Compiling kernel.
 */
gulp.task("all", function () {
  const tsProject = ts.createProject("tsconfig.json");
  const tsResult = tsProject.src().pipe(tsProject());
  return merge(tsResult, tsResult.js).pipe(gulp.dest("lib/"));
});

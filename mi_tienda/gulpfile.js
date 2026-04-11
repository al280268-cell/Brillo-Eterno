// Archivo de Configuración de Gulp
// Sirve para compilar los estilos de SCSS a CSS.
const gulp = require('gulp');
const sass = require('gulp-sass')(require('sass'));

gulp.task('styles', function () {
    return gulp.src('./static/scss/**/*.scss')
        .pipe(sass({ outputStyle: 'compressed' }).on('error', sass.logError))
        .pipe(gulp.dest('./static/css'));
});

gulp.task('watch', function () {
    gulp.watch('./static/scss/**/*.scss', gulp.series('styles'));
});

gulp.task('default', gulp.series('styles', 'watch'));

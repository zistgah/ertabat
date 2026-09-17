dnl © 1993–2026 Abhishek Choudhary. All rights reserved. AyeAI.
AC_INIT([ertabat], [0.1.0], [abhishek@ayeai.in])
AC_CONFIG_AUX_DIR([build-aux])
AC_CONFIG_MACRO_DIRS([m4])
AM_INIT_AUTOMAKE([foreign subdir-objects -Wall])

AM_PATH_PYTHON([3.8],, [AC_MSG_ERROR([python3 >= 3.8 is required])])

AC_ARG_WITH([sgp4], AS_HELP_STRING([--with-sgp4],
  [require the sgp4 propagator; without it TLE propagation declares itself absent]))
AS_IF([test "x$with_sgp4" = "xyes"], [
  AC_MSG_CHECKING([for python sgp4])
  AS_IF([$PYTHON -c "import sgp4" >/dev/null 2>&1],
        [AC_MSG_RESULT([yes])],
        [AC_MSG_ERROR([sgp4 not installed])])])

AC_CONFIG_FILES([Makefile])
AC_OUTPUT

AC_MSG_NOTICE([
  ertabat $VERSION
  python      : $PYTHON ($PYTHON_VERSION)
  make check  : unit suite + contract + gate-bite proofs
])

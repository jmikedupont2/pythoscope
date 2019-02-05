This is a fork of the excellent [pythoscope.org](http://pythoscope.org/)
by [Matt Wiatkowski](https://github.com/mkwiatkowski/pythoscope)

Support for Python 3 was added by Philippe Guglielmetti


## Installation


You can get the [source from GitHub](https://github.com/goulu/pythoscope)


To install the package from the source directory do:

    $ python setup.py install

You don't need setuptools for this to work, a bare Python will do just fine.

However, if you *do* have setuptools installed, you may also consider running
the whole test suite of Pythoscope:

    $ python setup.py test

## Usage

You can use the tool through a single `pythoscope` command. To prepare
your project for use with Pythoscope, type:

    $ pythoscope --init path/to/your/project/

It's only doing static analysis, and doesn't import your modules or
execute your code in any way, so you're perfectly safe to run it on
anything you want. After that, a directory named `.pythoscope` will be
created in the current directory. To generate test stubs based on your
project, select files you want to generate tests for:

    $ pythoscope  path/to/your/project/specific/file.py  path/to/your/project/other/*.py

Test files will be saved to your test directory, if you have one, or
into a new `tests/` directory otherwise. Test cases are aggregated
into `TestCase` classes. Currently each production class and each
production function gets its own `TestCase` class.

Some of the classes and functions are ignored by the generator - all
which name begins with an underscore, exception classes, and some
others.

Generator itself is configurable to some extent, see:

    $ pythoscope --help

for more information on available options.

## Editor Integration

### Emacs

We put out an elisp script that integrates Pythoscope into Emacs. The file is in the the `misc/` directory of the source distribution. You can also [look at the file on github](https://github.com/mkwiatkowski/pythoscope/blob/master/misc/pythoscope.el). Usage and installation instructions are in the comments at the top of the file.

### Vim

There is interest in Vim integration and someone is working on it but we have nothing for you right now.

## License

All Pythoscope source code is licensed under an MIT license (see LICENSE file).
All files under lib2to3/ are licensed under PSF license.
File named imputil.py under bytecode_tracer/ is also licensed under PSF license.

"""A setuptools based setup module.

See:
https://packaging.python.org/en/latest/distributing.html
https://github.com/pypa/sampleproject
"""

# Always prefer setuptools over distutils
from setuptools import setup, find_packages
# To use a consistent encoding
from codecs import open
from os import path
from sys import version_info

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

# Arguments marked as "Required" below must be included for upload to PyPI.
# Fields marked as "Optional" may be commented out.

setup(
    # This is the name of your project. The first time you publish this
    # package, this name will be registered for you. It will determine how
    # users can install this project, e.g.:
    #
    # $ pip install sampleproject
    #
    # And where it will live on PyPI: https://pypi.org/project/sampleproject/
    #
    # There are some restrictions on what makes a valid project name
    # specification here:
    # https://packaging.python.org/specifications/core-metadata/#name
    name='LbDevTools',  # Required

    # Versions should comply with PEP 440:
    # https://www.python.org/dev/peps/pep-0440/
    #
    # For a discussion on single-sourcing the version across setup.py and the
    # project code, see
    # https://packaging.python.org/en/latest/single_source_version.html
    # version='0.0.1',  # Required
    use_scm_version=True,

    # This is a one-line description or tagline of what your project does. This
    # corresponds to the "Summary" metadata field:
    # https://packaging.python.org/specifications/core-metadata/#summary
    description='LHCb development tools',  # Required

    # This is an optional longer description of your project that represents
    # the body of text which users will see when they visit PyPI.
    #
    # Often, this is the same as your README, so you can just read it in from
    # that file directly (as we have already done above)
    #
    # This field corresponds to the "Description" metadata field:
    # https://packaging.python.org/specifications/core-metadata/#description-optional
    long_description=long_description,  # Optional

    # This should be a valid link to your project's main homepage.
    #
    # This field corresponds to the "Home-Page" metadata field:
    # https://packaging.python.org/specifications/core-metadata/#home-page-optional
    url='https://gitlab.cern.ch/lhcb-core/LbDevTools',  # Optional

    # This should be your name or the name of the organization which owns the
    # project.
    author='CERN - LHCb Core Software',  # Optional

    # This should be a valid email address corresponding to the author listed
    # above.
    author_email='lhcb-core-soft@cern.ch',  # Optional

    license='GPLv3+',

    # Classifiers help users find your project by categorizing it.
    #
    # For a list of valid classifiers, see
    # https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[  # Optional
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 4 - Beta',

        # Indicate who your project is intended for
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',

        # Pick your license as you wish
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],

    python_requires='>=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*, !=3.4.*, <4',

    # This field adds keywords for your project which will appear on the
    # project page. What does your project relate to?
    #
    # Note that this is a string of words separated by whitespace, not a list.
    # keywords='LHCb Dirac LHCbDirac',  # Optional

    # You can just specify package directories manually here if your project is
    # simple. Or you can use find_packages().
    #
    # Alternatively, if you just want to distribute a single Python file, use
    # the `py_modules` argument instead as follows, which will expect a file
    # called `my_module.py` to exist:
    #
    #   py_modules=["my_module"],
    #
    packages=find_packages(exclude=['*.tests']
                           if version_info < (3, 0) else []),

    # This field lists other packages that your project depends on to run.
    # Any package you put here will be installed by pip when your project is
    # installed, so they must be valid existing projects.
    #
    # For an analysis of "install_requires" vs pip's requirements files see:
    # https://packaging.python.org/en/latest/requirements.html
    install_requires=['LbEnv>=0.3.0', 'LbPlatformUtils',
                      'GitPython' + ('<2.1.12' if version_info < (3, 0) else ''),
                      'python-gitlab', 'jinja2', 'yapf==0.24.0', 'whichcraft'],

    # List additional groups of dependencies here (e.g. development
    # dependencies). Users will be able to install these using the "extras"
    # syntax, for example:
    #
    #   $ pip install sampleproject[dev]
    #
    # Similar to `install_requires` above, these must be valid existing
    # projects.
    extras_require={},  # Optional
    tests_require=['coverage'],
    setup_requires=['nose>=1.0', 'setuptools_scm'],
    # If there are data files included in your packages that need to be
    # installed, specify them here.
    #
    # If using Python 2.6 or earlier, then these have to be included in
    # MANIFEST.in as well.
    # package_data={  # Optional
    #     'LbDevTools': [],
    # },
    include_package_data=True,

    # Although 'package_data' is the preferred approach, in some case you may
    # need to place data files outside of your packages. See:
    # http://docs.python.org/3.4/distutils/setupscript.html#installing-additional-files
    #
    # In this case, 'data_file' will be installed into '<sys.prefix>/my_data'
    data_files=[
        ('share/bash-completion/completions',
         [
             'shell-completion/bash/LbDevTools_git_commands'
         ]),
        ('share/zsh/completions',
         [
             'shell-completion/zsh/_git-lb-checkout',
             'shell-completion/zsh/_git-lb-push',
             'shell-completion/zsh/_git-lb-use'
         ])],  # Optional
    # To provide executable scripts, use entry points in preference to the
    # "scripts" keyword. Entry points provide cross-platform support and allow
    # `pip` to create the appropriate form of executable for the target
    # platform.
    #
    scripts=['bin/lb-gen-compiler-wrapper'],
    entry_points={
        'console_scripts': [
            'lb-project-init=LbDevTools.ProjectInit:main',
            'lb-dev=LbDevTools.ProjectDev:main',
            'lb-devtools-datadir=LbDevTools:_print_data_location',
            'lb-gen-release-notes=LbDevTools.ReleaseNotes:main',
            'lb-check-copyright=LbDevTools.SourceTools:check_copyright',
            'lb-add-copyright=LbDevTools.SourceTools:add_copyright',
            'lb-format=LbDevTools.SourceTools:format',
            'lb-clang-format=LbDevTools.SourceTools:clang_format',
            'lb-glimpse=LbDevTools.Indexing:search',
            'git-lb-use=LbDevTools.GitTools.use:main',
            'git-lb-checkout=LbDevTools.GitTools.checkout:main',
            'git-lb-push=LbDevTools.GitTools.push:main',
            'git-lb-clone-pkg=LbDevTools.GitTools.clone_pkg:main',
        ],
    },

    # The package can be safely distributed as a ZIP file
    zip_safe=False,

    # Process files with 2to3 to run with Python 3
    use_2to3=version_info >= (3, 0),
)

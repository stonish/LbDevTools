# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

## [Unreleased][]


## [0.3.1][] - 2018-10-25
### Added
- Build of compiler wrappers RPM in Gitlab-CI job (!32)

### Changed
- Add `.ent` and `.xsd` as XML extensions for `lb-check-copyright` (#12, !35)
- Improved the report of `lb-check-copyright` to better fit Gitlab-CI failure
  report (#13)

### Fixed
- Make sure Python source encoding declaration
  ([PEP-263](https://www.python.org/dev/peps/pep-0263/)) is preserved by
  `lb-add-copyright`(#14)


## [0.3.0][] - 2018-10-19
### Added
- Scripts to check and add copyright statements in files (!25, [LBCORE-1619][])
  - `lb-check-copyright`
  - `lb-add-copyright`

### Fixed
- Fix generation of `.clang-format` in `lb-dev` (!27)
- Improved handling of diffs in `git lb-push` (!28)


## [0.2.0][] - 2018-09-26
### Added
- Port script for generating release notes from LbScripts (!23)
- Create `.clang-format` file in `lb-project-init` and `lb-dev` (!24)


## [0.1.4][] - 2018-09-26
### Fixed
- Use `MYSITEROOT` to find binutils in `gen-compiler-wrapper` (!22)


## [0.1.3][] - 2018-07-26
### Added
- Preliminary support for shell completion (!18)

### Changed
- Updated `lb-gen-compiler-wrapper` with latest LbScritps (!19, !21)

### Fixed
- Fixed exclusion of LCG Ninja (!17)
- Fixed to `git-lb-push` (!15, !16)


## [0.1.2][] - 2018-05-22
### Added
- Provide instructions for local installation of nightly slots (!13, !14)
- `git lb-checkout`
  - added `--list` option to `git lb-checkout` (!5)
  - print suggestions for misspelled branch or package name (!5)
- Added `--version` option to Git subcommands (!4)

### Changed
- Reformatted with yapf 0.21.0 (!11)
- Fix `lb-gen-compiler-wrapper` to handle SFT build of clang 6.0.0 (7a7450ad)
- Renamed `LbDevTools.data_location` to `_print_data_location` (!7)
- Allow `git lb-checkout` only for packages and _hats_ (#3)
- Replaced Git custom wrappers with [GitPython][] (#2)
- Automatic commit of `git lb-checkout` metadata after `git lb-push` (!4)

### Fixed
- Make sure we do not use ninja from LCG (!10, !12)
- `lb-env`: bail out if neither CMake nor CMT configuration is found (!9)
- Fixed use of CMT Makefile wrapper (!8)
- Fixed missing import in `git lb-push`, introduces with !4 (!5)
- Fixed project name case for remote name in `git lb-use` (!5)
- Unused variable "pushurl" in LbDevTools.GitTool.push (#4)
- Removed references to LbScripts (#5)

## [0.1.1][] - 2018-03-26
### Added
- Script to generate compiler wrappers (`lb-gen-compiler-wrapper`)

## 0.1.0
### Added
- Changelog
- Scripts:
  - `lb-project-init`
  - `lb-dev`
  - `lb-devtools-datadir`
  - Git custom commands
    - `git lb-use`
    - `git lb-checkout`
    - `git lb-push`
    - `git lb-clone-pkg`
  - `lb-gen-compiler-wrapper`
- Generic makefiles for CMT and CMake
- CMake support modules (from [Gaudi v30r2][])


[Unreleased]: https://gitlab.cern.ch/lhcb-core/LbDevTools/compare/0.3.1...master
[0.3.1]: https://gitlab.cern.ch/lhcb-core/LbDevTools/compare/0.3.0...0.3.1
[0.3.0]: https://gitlab.cern.ch/lhcb-core/LbDevTools/compare/0.2.0...0.3.0
[0.2.0]: https://gitlab.cern.ch/lhcb-core/LbDevTools/compare/0.1.4...0.2.0
[0.1.4]: https://gitlab.cern.ch/lhcb-core/LbDevTools/compare/0.1.3...0.1.4
[0.1.3]: https://gitlab.cern.ch/lhcb-core/LbDevTools/compare/0.1.2...0.1.3
[0.1.2]: https://gitlab.cern.ch/lhcb-core/LbDevTools/compare/0.1.1...0.1.2
[0.1.1]: https://gitlab.cern.ch/lhcb-core/LbDevTools/compare/0.1.0...0.1.1

[Gaudi v30r2]: https://gitlab.cern.ch/gaudi/Gaudi/tags/v30r2
[GitPython]: http://gitpython.readthedocs.io/en/stable/
[LBCORE-1619]: https://its.cern.ch/jira/browse/LBCORE-1619

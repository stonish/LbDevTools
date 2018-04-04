# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

## [Unreleased][]
### Added
- `git lb-checkout`
  - added `--list` option to `git lb-checkout` (!5)
  - print suggestions for misspelled branch or package name (!5)
- Added `--version` option to Git subcommands (!4)

### Changed
- Allow `git lb-checkout` only for packages and _hats_ (#3)
- Replaced Git custom wrappers with [GitPython][] (#2)
- Automatic commit of `git lb-checkout` metadata after `git lb-push` (!4)

### Fixed
- Fixed missing import in `git lb-push` (!5)
- Fixed project name case for remote name in `git lb-use` (!5)
- Unused variable "pushurl" in LbDevTools.GitTool.push (#4)
- Removed references to LbScripts (#5)

## [0.1.1][]
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


[Unreleased]: https://gitlab.cern.ch/lhcb-core/LbDevTools/compare/0.1.1...master
[0.1.1]: https://gitlab.cern.ch/lhcb-core/LbDevTools/compare/0.1.0...0.1.1

[Gaudi v30r2]: https://gitlab.cern.ch/gaudi/Gaudi/tags/v30r2
[GitPython]: http://gitpython.readthedocs.io/en/stable/

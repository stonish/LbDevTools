# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

## [Unreleased][]

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

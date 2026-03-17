# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## [0.1.1] - 2026-03-17

### Fixed

- Fixed static file namespace collision by moving `static/css/project.css` to `static/websourcemonitor/css/diff.css` to follow Django reusable app conventions and prevent conflicts with host projects
- Fixed missing CSS styles in diff.html template by adding `{% load static %}` tag and proper CSS link with `{{ block.super }}` to preserve host project styles

## [0.1.0]

### Added

- Started new project based on the app within the `op-sources-verification` project.

### Changed


## Release Checklist

### 1. Prepare

- [ ] Set the version in `pyproject.toml`, for example `0.1.0`.
- [ ] Add the matching `## [0.1.0]` section to `CHANGELOG.md`.
- [ ] Open a release PR and merge it into `master`.
- [ ] Check out the updated `master` branch locally:

	```bash
	git checkout master
	git pull origin master
	```

- [ ] Create and push the matching tag **on `master`**:

	```bash
	git tag -a v0.1.0 -m "Release v0.1.0"
	git push origin v0.1.0
	```

### 2. Verify and build

- [ ] Run `make release` **from the tagged, clean `master` checkout**.
- [ ] Confirm that tests, examples, formatting, documentation, licenses, and
	package metadata pass.
- [ ] Choose `test` in the upload prompt first, verify the TestPyPI package,
	then use `pypi` for the final upload.

The command creates these files in `dist/`:

- `ares-<version>-release.zip`: release bundle for GitHub
- `ares-<version>-py3-none-any.whl`: Python installation package
- `ares-<version>.tar.gz`: Python source package
- `ares` or `ares.exe`: available standalone executable
- `SHA256SUMS.txt`: checksums for the bundle contents

The ZIP is created locally by `make release`; it is not uploaded to the Git
repository. A Windows executable is included automatically when it is present
in `dist/`. Otherwise, upload the Windows CI artefact separately.

### 3. Create the GitHub release

1. Open **Releases** on GitHub and select **Draft a new release**.
2. Select the existing tag `v<version>`.
3. Use `v<version>` as the release title.
4. Add the relevant `CHANGELOG.md` entries as the release notes.
5. Upload `dist/ares-<version>-release.zip` under GitHub's **Assets** section.
6. Mark it as a pre-release if it is not stable yet.
7. Select **Publish release**.

GitHub creates source ZIP and tarball downloads automatically. The project
release ZIP is the curated bundle containing the built artefacts and checksums.

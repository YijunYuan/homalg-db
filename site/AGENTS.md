# Site contributor instructions

Read `../docs/SITE.md` and the root contributor instructions. Use English.

- Components read data through `data/loaders.ts` and the `DataSource` interface.
- Keep every UI string in `src/i18n/en.json`; call `t()` with literal keys except
  the reserved `enum.*` namespace. Source document prose is not translated.
- Generate `src/data/types.ts` from the schemas. Python validates actual JSON.
- Keep graph layout and search in workers, with shared pure ESM helpers for CI.
- Use local fonts and assets. Runtime network access is limited to the data
  directory or the explicitly selected API; external links require a user click.
- Run `npm test`, `npm run lint`, `npm run build` and `npm run test:e2e`.
- Generated fixture data comes from `make fixture-site`; do not hand-edit it after
  the Python pipeline is available. Test against the fixture fallback.

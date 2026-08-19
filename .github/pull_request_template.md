<!--
PR title must follow Conventional Commits — it becomes the merge commit message.
Format: type(scope): short description
Examples: feat(skills): add covecto suite / docs(readme): update product versions
-->

## What
<!-- One or two sentences describing the change. -->

## Why
<!-- The problem you're solving. Link to the issue if there is one (e.g. "Closes #42"). -->

## How
<!-- Brief notes on the approach, only if non-obvious. -->

## Validation

- [ ] Skill files parse (valid YAML frontmatter + markdown)
- [ ] Tested the changed skill locally in a Hermes/agent session
- [ ] Docs updated if the skill surface changed (README, examples)

## Related Issues
<!-- Link to related issues, e.g. Closes #123 -->

## Checklist

- [ ] Branch name follows convention (`fix/`, `feat/`, `docs/`, `chore/`, `refactor/`, `test/`)
- [ ] Branch is from `develop`
- [ ] Commit messages follow [Conventional Commits](https://www.conventionalcommits.org/)
- [ ] No secrets or credentials committed
- [ ] One logical change per PR (no mixed concerns)
- [ ] [CLA](https://github.com/codecoradev/.github/blob/main/.cla/signatures.json) signed (or will sign when the bot asks)

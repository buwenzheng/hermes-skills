# Hermes Skills

Custom skills for [Hermes Agent](https://github.com/nousresearch/hermes-agent).

## Available Skills

### skill-publisher
Safely publish a local Hermes skill to GitHub with security audit + format review.

**Category:** productivity

**Usage:** `hermes skills install buwenzheng/hermes-skills/skill-publisher`

---

## Install a Skill

```bash
hermes skills install <owner>/<repo>/<skill-name>
```

Example:
```bash
hermes skills install buwenzheng/hermes-skills/skill-publisher
```

## Submit a New Skill

1. Create your skill in `~/.hermes/skills/<category>/<skill-name>/`
2. Make sure it has a valid `SKILL.md` with frontmatter
3. Ask Hermes to run `skill-publisher` and specify your skill name

## Repo Structure

```
hermes-skills/
├── README.md
└── <skill-name>/
    ├── SKILL.md
    └── README.md
```

Each skill lives at the root level (flat structure, not nested under `skills/`).

## Security

All skills are scanned for sensitive data before publishing. See [skill-publisher](https://github.com/buwenzheng/hermes-skills/tree/main/skill-publisher) for details.

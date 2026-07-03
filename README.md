# Skill Evaluator

Production-grade quality gate for Codex skills.

`skill-evaluator` audits Codex skills and `.skill` packages for trust, reliability, adaptability, convention, effectiveness, and installability. It is designed for release checks, pre-install reviews, and practical improvement planning.

## 中文说明

### 这是什么

`skill-evaluator` 是一个用于评估 Codex Skill 的生产级验收门禁。它会检查一个已安装 skill 目录、源码目录或 `.skill` 包，判断它是否具备发布、安装和复用的基本质量。

它不会执行被测 skill 里的业务逻辑，只做只读检查，重点覆盖：

- 可信任度：权限、凭据、网络、文件写入、生产系统风险是否清楚。
- 可靠性：脚本语法、可运行入口、失败路径、边界输入是否可验证。
- 适用性：frontmatter 描述是否能稳定触发且边界清楚。
- 规范性：目录结构、frontmatter、资源引用、渐进披露是否符合 Codex skill 习惯。
- 有效性：是否能帮助用户完成目标，而不是只输出更多说明。
- 安装可用性：能否从干净目录安装、发现、打包并重新验收。

### 仓库结构

```text
.
├── README.md
├── LICENSE
├── .gitignore
└── skill-evaluator/
    ├── SKILL.md
    ├── agents/
    │   └── openai.yaml
    └── scripts/
        └── audit_skill.py
```

### 安装

```bash
git clone https://github.com/wuhanjieyue/skill-evaluator.git
mkdir -p "${CODEX_HOME:-$HOME/.codex}/skills"
cp -R skill-evaluator/skill-evaluator "${CODEX_HOME:-$HOME/.codex}/skills/skill-evaluator"
```

安装后开启新的 Codex 会话，或重启当前 Codex 应用会话，让 skill 列表重新加载。

### 验收

```bash
python3 "${CODEX_HOME:-$HOME/.codex}/skills/skill-evaluator/scripts/audit_skill.py" --self-test
python3 "${CODEX_HOME:-$HOME/.codex}/skills/skill-evaluator/scripts/audit_skill.py" --strict "${CODEX_HOME:-$HOME/.codex}/skills/skill-evaluator"
python3 "${CODEX_HOME:-$HOME/.codex}/skills/.system/skill-creator/scripts/quick_validate.py" "${CODEX_HOME:-$HOME/.codex}/skills/skill-evaluator"
```

期望结果：

- `--self-test` 输出 4 项 `SELFTEST PASS`。
- `--strict` 输出 `SUMMARY status PASS`。
- `quick_validate.py` 输出 `Skill is valid!`。

### 使用

显式调用：

```text
Use $skill-evaluator to audit /path/to/skill
```

直接运行脚本：

```bash
python3 skill-evaluator/scripts/audit_skill.py --strict /path/to/skill
python3 skill-evaluator/scripts/audit_skill.py --json --strict /path/to/skill
python3 skill-evaluator/scripts/audit_skill.py --strict /path/to/package.skill
```

### 输出含义

- `PASS`：检查项通过。
- `WARN`：存在生产级风险；严格模式下会阻断发布。
- `FAIL`：基础要求不满足。
- `FIX`：对应问题的最小修复建议。
- `SUMMARY status PASS`：严格门禁通过。
- `SUMMARY status BLOCKED`：需要修复后再发布。

### 发布标准

一个 skill 只有在以下条件满足时才应视为生产可用：

- `audit_skill.py --strict` 通过。
- `audit_skill.py --self-test` 通过。
- `quick_validate.py` 通过。
- 没有未解释的网络、凭据、写入或生产系统依赖。
- 核心行为经过真实任务或 fresh-session prompt 验证。

### 许可证

MIT License。

---

## English

### What It Is

`skill-evaluator` is a production-readiness gate for Codex skills. It audits an installed skill folder, source directory, or `.skill` package and reports whether the skill is ready to publish, install, and reuse.

It does not execute the target skill's business logic. The audit is read-only and focuses on:

- Trust: permissions, credentials, network access, file writes, and production-system risks.
- Reliability: script syntax, runnable entrypoints, failure paths, and boundary handling.
- Adaptability: trigger description quality and clear capability boundaries.
- Convention: Codex skill layout, frontmatter, resource references, and progressive disclosure.
- Effectiveness: whether the skill helps users complete the intended job.
- Installability: clean install, discovery, packaging, and verification.

### Repository Layout

```text
.
├── README.md
├── LICENSE
├── .gitignore
└── skill-evaluator/
    ├── SKILL.md
    ├── agents/
    │   └── openai.yaml
    └── scripts/
        └── audit_skill.py
```

### Installation

```bash
git clone https://github.com/wuhanjieyue/skill-evaluator.git
mkdir -p "${CODEX_HOME:-$HOME/.codex}/skills"
cp -R skill-evaluator/skill-evaluator "${CODEX_HOME:-$HOME/.codex}/skills/skill-evaluator"
```

After installation, open a new Codex session or restart the current Codex app session so the skill list reloads.

### Verification

```bash
python3 "${CODEX_HOME:-$HOME/.codex}/skills/skill-evaluator/scripts/audit_skill.py" --self-test
python3 "${CODEX_HOME:-$HOME/.codex}/skills/skill-evaluator/scripts/audit_skill.py" --strict "${CODEX_HOME:-$HOME/.codex}/skills/skill-evaluator"
python3 "${CODEX_HOME:-$HOME/.codex}/skills/.system/skill-creator/scripts/quick_validate.py" "${CODEX_HOME:-$HOME/.codex}/skills/skill-evaluator"
```

Expected results:

- `--self-test` prints four `SELFTEST PASS` lines.
- `--strict` prints `SUMMARY status PASS`.
- `quick_validate.py` prints `Skill is valid!`.

### Usage

Explicit Codex invocation:

```text
Use $skill-evaluator to audit /path/to/skill
```

Direct script usage:

```bash
python3 skill-evaluator/scripts/audit_skill.py --strict /path/to/skill
python3 skill-evaluator/scripts/audit_skill.py --json --strict /path/to/skill
python3 skill-evaluator/scripts/audit_skill.py --strict /path/to/package.skill
```

### Output

- `PASS`: the check passed.
- `WARN`: production risk; strict mode blocks release.
- `FAIL`: baseline requirement is missing.
- `FIX`: smallest suggested repair for the issue.
- `SUMMARY status PASS`: strict gate passed.
- `SUMMARY status BLOCKED`: fix before publishing.

### Release Standard

A skill should be considered production-ready only when:

- `audit_skill.py --strict` passes.
- `audit_skill.py --self-test` passes.
- `quick_validate.py` passes.
- Network, credential, write, or production-system dependencies are documented and verifiable.
- Core behavior has been checked with realistic tasks or fresh-session prompts.

### License

MIT License.

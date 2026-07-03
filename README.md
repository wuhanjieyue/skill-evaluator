# Skill Evaluator

Production-grade quality gate for portable AI agent skills.

`skill-evaluator` audits AI agent skills and `.skill` packages for trust, reliability, adaptability, convention, effectiveness, and installability. It is designed for release checks, pre-install reviews, and practical improvement planning.

## 中文说明

### 这是什么

`skill-evaluator` 是一个用于评估 AI Agent Skill 的生产级验收门禁。它会检查一个已安装 skill 目录、源码目录或 `.skill` 包，判断它是否具备发布、安装和复用的基本质量。

它不会执行被测 skill 里的业务逻辑，只做只读检查，重点覆盖：

- 可信任度：权限、凭据、网络、文件写入、生产系统风险是否清楚。
- 可靠性：脚本语法、可运行入口、失败路径、边界输入是否可验证。
- 适用性：frontmatter 描述是否能稳定触发且边界清楚。
- 规范性：目录结构、frontmatter、资源引用、渐进披露是否符合可移植 skill 习惯。
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
mkdir -p /path/to/agent-skills
cp -R skill-evaluator/skill-evaluator /path/to/agent-skills/skill-evaluator
```

安装后按目标 Agent 的规则刷新或重启会话，让 skill 列表重新加载。

不同 Agent 的 skill 目录不同；把 `skill-evaluator/` 子目录复制到目标 Agent 能发现的 skill 目录即可。

### 验收

```bash
python3 /path/to/agent-skills/skill-evaluator/scripts/audit_skill.py --self-test
python3 /path/to/agent-skills/skill-evaluator/scripts/audit_skill.py --strict /path/to/agent-skills/skill-evaluator
```

期望结果：

- `--self-test` 输出 4 项 `SELFTEST PASS`。
- `--strict` 输出 `SUMMARY status PASS`。
- 如果目标平台提供专属 validator，再额外运行该平台的校验命令。

### 使用

把目标 skill 路径交给已安装该 skill 的 Agent：

```text
使用 skill-evaluator 评估 /path/to/skill 是否达到生产可用标准
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
- 目标平台自己的 validator 通过，如果该平台提供。
- 没有未解释的网络、凭据、写入或生产系统依赖。
- 核心行为经过真实任务或 fresh-session prompt 验证。

### 许可证

MIT License。

---

## English

### What It Is

`skill-evaluator` is a production-readiness gate for portable AI agent skills. It audits an installed skill folder, source directory, or `.skill` package and reports whether the skill is ready to publish, install, and reuse.

It does not execute the target skill's business logic. The audit is read-only and focuses on:

- Trust: permissions, credentials, network access, file writes, and production-system risks.
- Reliability: script syntax, runnable entrypoints, failure paths, and boundary handling.
- Adaptability: trigger description quality and clear capability boundaries.
- Convention: portable skill layout, frontmatter, resource references, and progressive disclosure.
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
mkdir -p /path/to/agent-skills
cp -R skill-evaluator/skill-evaluator /path/to/agent-skills/skill-evaluator
```

After installation, refresh or restart the target agent session according to that agent's skill-loading rules.

Different agents use different skill directories. Copy the `skill-evaluator/` subdirectory into the skill directory that your target agent can discover.

### Verification

```bash
python3 /path/to/agent-skills/skill-evaluator/scripts/audit_skill.py --self-test
python3 /path/to/agent-skills/skill-evaluator/scripts/audit_skill.py --strict /path/to/agent-skills/skill-evaluator
```

Expected results:

- `--self-test` prints four `SELFTEST PASS` lines.
- `--strict` prints `SUMMARY status PASS`.
- If the target platform has its own validator, run that validator as an additional platform-specific check.

### Usage

Ask any agent that has this skill installed:

```text
Use the skill-evaluator skill to audit /path/to/skill for production readiness.
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
- The target platform's own validator passes, if that platform provides one.
- Network, credential, write, or production-system dependencies are documented and verifiable.
- Core behavior has been checked with realistic tasks or fresh-session prompts.

### License

MIT License.

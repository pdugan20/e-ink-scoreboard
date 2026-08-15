#!/usr/bin/env python3
"""Fail-closed checks for the disabled-first Renovate bootstrap."""

import sys

# Guard before any shadowable import: without -P the interpreter puts this
# script's own directory ahead of the stdlib on sys.path, where a committed
# module could neuter the whole gate. sys is builtin and cannot be shadowed.
if not sys.flags.safe_path:
    raise SystemExit("automation-policy.test.py must run under python3 -P")

import json  # noqa: E402
import re  # noqa: E402
import unittest  # noqa: E402
from pathlib import Path  # noqa: E402
from typing import Any  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
RENOVATE_PATH = ROOT / "renovate.json"
CI_PATH = ROOT / ".github" / "workflows" / "ci.yml"

CANONICAL_BOOTSTRAP = """{
  "$schema": "https://docs.renovatebot.com/renovate-schema.json",
  "enabled": false,
  "enabledManagers": ["npm", "github-actions"]
}
"""

EXPECTED_KEYS = ["$schema", "enabled", "enabledManagers"]
EXPECTED_MANAGERS = ["npm", "github-actions"]
EXPECTED_WORKFLOWS = ["ci.yml", "dependabot-auto-merge.yml", "pr-lint.yml"]
WORKFLOWS_DIR = ROOT / ".github" / "workflows"
POLICY_JOB = "python-lint"
POLICY_COMMAND = "python3 -P scripts/automation-policy.test.py"
POLICY_PATH = "scripts/automation-policy.test.py"
EXPECTED_POLICY_SCRIPTS = ["automation-policy.test.py"]
ALTERNATE_RENOVATE_CONFIG_PATHS = [
    ".github/renovate.json",
    ".github/renovate.json5",
    ".gitlab/renovate.json",
    ".gitlab/renovate.json5",
    ".renovaterc",
    ".renovaterc.json",
    ".renovaterc.json5",
    "renovate.json5",
]
POLICY_STEP = f"""      - name: Validate disabled Renovate bootstrap
        env:
          BASH_ENV: /dev/null
          SHELLOPTS: ''
        shell: bash
        run: {POLICY_COMMAND}"""
CHECKOUT_STEP_PATTERN = r"      - uses: actions/checkout@[0-9a-f]{40}(?: # v[\w.-]+)?"
SETUP_PYTHON_STEP_PATTERN = (
    r"      - name: Set up Python\n"
    r"        uses: actions/setup-python@[0-9a-f]{40}(?: # v[\w.-]+)?\n"
    r"        with:\n"
    r"          python-version: '3\.x'"
)


class PolicyError(ValueError):
    """Raised when the bootstrap is ambiguous or expands policy."""


def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    """Build a JSON object while rejecting every duplicate key."""

    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise PolicyError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def validate_bootstrap(contents: str) -> dict[str, Any]:
    """Validate the exact disabled bootstrap without Python equality shortcuts."""

    try:
        config = json.loads(contents, object_pairs_hook=reject_duplicate_keys)
    except (json.JSONDecodeError, PolicyError) as error:
        raise PolicyError("renovate.json is not unambiguous JSON") from error

    if not isinstance(config, dict):
        raise PolicyError("renovate.json must contain one object")
    if list(config) != EXPECTED_KEYS:
        raise PolicyError("renovate.json keys or key order changed")
    if config["$schema"] != "https://docs.renovatebot.com/renovate-schema.json":
        raise PolicyError("Renovate schema changed")
    if config["enabled"] is not False:
        raise PolicyError("Renovate must remain exactly disabled")
    if config["enabledManagers"] != EXPECTED_MANAGERS:
        raise PolicyError("Renovate manager scope changed")
    if contents != CANONICAL_BOOTSTRAP:
        raise PolicyError("renovate.json is not the canonical bootstrap")

    return config


def extract_ci_jobs(contents: str) -> dict[str, str]:
    """Extract the top-level CI jobs from the canonical workflow shape."""

    marker = "\njobs:\n"
    if contents.count(marker) != 1:
        raise PolicyError("CI workflow must contain one jobs mapping")

    jobs_section = contents.split(marker, 1)[1]
    top_level_lines = [
        line
        for line in jobs_section.splitlines()
        if line.startswith("  ")
        and not line.startswith("    ")
        and line.strip()
        and not line.lstrip().startswith("#")
    ]
    if not top_level_lines or any(
        not re.fullmatch(r"  [a-zA-Z0-9_-]+:", line) for line in top_level_lines
    ):
        raise PolicyError("CI jobs must use canonical unquoted block keys")

    matches = list(re.finditer(r"(?m)^  (?P<name>[a-zA-Z0-9_-]+):\n", jobs_section))
    if not matches:
        raise PolicyError("CI workflow has no jobs")

    jobs: dict[str, str] = {}
    for index, match in enumerate(matches):
        name = match.group("name")
        if name in jobs:
            raise PolicyError(f"duplicate CI job: {name}")
        end = (
            matches[index + 1].start()
            if index + 1 < len(matches)
            else len(jobs_section)
        )
        jobs[name] = jobs_section[match.end() : end]

    return jobs


def parse_job_needs(job_name: str, body: str) -> list[str]:
    """Parse one canonical scalar or inline-list needs declaration."""

    matches = re.findall(r"(?m)^    needs:\s*(?P<value>[^\n]+?)\s*$", body)
    if len(matches) > 1:
        raise PolicyError(f"CI job {job_name} has ambiguous needs declarations")
    if not matches:
        return []

    value = matches[0]
    if re.fullmatch(r"[a-zA-Z0-9_-]+", value):
        return [value]
    if value.startswith("[") and value.endswith("]"):
        needs = [item.strip() for item in value[1:-1].split(",")]
        if needs and all(re.fullmatch(r"[a-zA-Z0-9_-]+", item) for item in needs):
            return needs

    raise PolicyError(f"CI job {job_name} has a non-canonical needs declaration")


def job_reaches_policy_gate(
    job_name: str,
    needs_by_job: dict[str, list[str]],
    visiting: frozenset[str] = frozenset(),
) -> bool:
    """Return whether a job is transitively blocked on the policy job."""

    if job_name == POLICY_JOB:
        return True
    if job_name in visiting:
        raise PolicyError("CI job dependency graph contains a cycle")
    if job_name not in needs_by_job:
        raise PolicyError(f"CI job depends on unknown job: {job_name}")

    next_visiting = visiting | {job_name}
    return any(
        job_reaches_policy_gate(dependency, needs_by_job, next_visiting)
        for dependency in needs_by_job[job_name]
    )


def validate_ci_policy_gate(contents: str) -> None:
    """Require one executable gate before every dependency-consuming job."""

    if contents.count(POLICY_PATH) != 1 or contents.count(POLICY_COMMAND) != 1:
        raise PolicyError("CI must contain exactly one policy command reference")
    if re.search(r"""(?m)^\s*(?:-\s+)?(?:["'?!&*%{|>\[]|<<\s*:)""", contents):
        raise PolicyError("CI mapping keys must use canonical plain syntax")
    if re.search(r"(?m)^\s*defaults\s*:", contents):
        raise PolicyError("CI may not override the policy command shell")
    if re.search(r"(?m)^\s+if\s*:", contents):
        raise PolicyError("CI jobs and steps may not bypass the policy gate")

    top_level_lines = [
        line
        for line in contents.splitlines()
        if line and not line[0].isspace() and not line.startswith("#")
    ]
    if top_level_lines != ["name: CI", "on:", "jobs:"]:
        raise PolicyError("CI workflow must preserve its canonical top-level keys")

    jobs = extract_ci_jobs(contents)
    if POLICY_JOB not in jobs:
        raise PolicyError("required Python Lint policy job is missing")

    policy_body = jobs[POLICY_JOB]
    if re.search(r"(?m)^\s+(?:if|continue-on-error)\s*:", policy_body):
        raise PolicyError("policy job may not be conditional or error-tolerant")
    if re.search(
        r"(?m)^    (?:env|container|services|strategy|environment|permissions)\s*:",
        policy_body,
    ):
        raise PolicyError("policy job may not replace its execution environment")
    if re.findall(r"(?m)^    name:\s*([^\n]+?)\s*$", policy_body) != ["Python Lint"]:
        raise PolicyError("policy job must preserve the required context name")
    if re.findall(r"(?m)^    runs-on:\s*([^\n]+?)\s*$", policy_body) != [
        "ubuntu-latest"
    ]:
        raise PolicyError("policy job must run once on ubuntu-latest")

    steps_markers = list(re.finditer(r"(?m)^    steps:\n", policy_body))
    if len(steps_markers) != 1:
        raise PolicyError("policy job must contain one canonical steps list")
    steps_body = policy_body[steps_markers[0].end() :]
    step_matches = list(re.finditer(r"(?m)^      -[^\n]*$", steps_body))
    if not step_matches or steps_body[: step_matches[0].start()].strip():
        raise PolicyError("policy job contains content before its first step")
    step_blocks = []
    for index, match in enumerate(step_matches):
        end = (
            step_matches[index + 1].start()
            if index + 1 < len(step_matches)
            else len(steps_body)
        )
        block = steps_body[match.start() : end].strip("\n")
        step_blocks.append(block)
    policy_steps = [block for block in step_blocks if POLICY_PATH in block]
    if policy_steps != [POLICY_STEP]:
        raise PolicyError("policy command must be one exact unconditional step")
    if len(step_blocks) < 3 or step_blocks[2] != POLICY_STEP:
        raise PolicyError("policy command must be the third policy-job step")
    if not re.fullmatch(CHECKOUT_STEP_PATTERN, step_blocks[0]):
        raise PolicyError("policy job must begin with one SHA-pinned actions/checkout")
    if not re.fullmatch(SETUP_PYTHON_STEP_PATTERN, step_blocks[1]):
        raise PolicyError("policy job must pin actions/setup-python before the gate")

    run_commands = re.findall(r"(?m)^        run:\s*(?P<command>[^\n]*)$", policy_body)
    if not run_commands or run_commands[0] != POLICY_COMMAND:
        raise PolicyError("policy command must be the first run step in Python Lint")
    if parse_job_needs(POLICY_JOB, policy_body):
        raise PolicyError("policy job must be the root CI gate")

    needs_by_job = {
        job_name: parse_job_needs(job_name, body) for job_name, body in jobs.items()
    }
    for job_name in jobs:
        if job_name != POLICY_JOB and not job_reaches_policy_gate(
            job_name, needs_by_job
        ):
            raise PolicyError(f"CI job is not gated by {POLICY_JOB}: {job_name}")


def validate_workflow_allowlist(names: list[str]) -> None:
    """Reject workflow files outside the reviewed allowlist."""

    if sorted(names) != EXPECTED_WORKFLOWS:
        raise PolicyError("workflow files must match the reviewed allowlist")


def validate_script_shadow_surface(entries: list[tuple[str, bool]]) -> None:
    """Reject Python-importable additions beside the policy suite.

    Running the suite by path can put scripts/ on sys.path, where a committed
    module would shadow the standard library; CI passes -P to prevent that,
    and this check makes any such addition a visible policy failure.
    """

    importable = sorted(
        name
        for name, is_dir in entries
        if name != "__pycache__"
        and (is_dir or name.endswith((".py", ".pyc", ".pyd", ".so")))
    )
    if importable != EXPECTED_POLICY_SCRIPTS:
        raise PolicyError("scripts directory gained a Python-importable entry")


class DisabledRenovateBootstrapTests(unittest.TestCase):
    def assert_rejected(self, contents: str) -> None:
        with self.assertRaises(PolicyError):
            validate_bootstrap(contents)

    def assert_workflow_rejected(self, contents: str) -> None:
        with self.assertRaises(PolicyError):
            validate_ci_policy_gate(contents)

    def test_repository_has_exact_disabled_bootstrap(self) -> None:
        config = validate_bootstrap(RENOVATE_PATH.read_text(encoding="utf-8"))

        self.assertIs(config["enabled"], False)
        self.assertEqual(config["enabledManagers"], EXPECTED_MANAGERS)

    def test_duplicate_json_keys_fail_closed(self) -> None:
        mutations = [
            CANONICAL_BOOTSTRAP.replace(
                '  "enabled": false,',
                '  "enabled": true,\n  "enabled": false,',
            ),
            CANONICAL_BOOTSTRAP.replace(
                '  "enabledManagers":',
                '  "enabledManagers": ["custom.regex"],\n  "enabledManagers":',
            ),
        ]

        for mutation in mutations:
            with self.subTest(mutation=mutation):
                self.assert_rejected(mutation)

    def test_activation_and_python_false_equals_zero_tricks_fail_closed(self) -> None:
        for replacement in ["true", "0", "0.0", "null", '"false"']:
            mutation = CANONICAL_BOOTSTRAP.replace("false", replacement, 1)
            with self.subTest(replacement=replacement):
                self.assert_rejected(mutation)

    def test_manager_scope_narrowing_expansion_and_reordering_fail_closed(self) -> None:
        manager_mutations = [
            '["npm"]',
            '["npm", "pip_requirements", "github-actions"]',
            '["npm", "github-actions", "dockerfile"]',
            '["npm", "npm", "github-actions"]',
            '["github-actions", "npm"]',
        ]

        for managers in manager_mutations:
            mutation = re.sub(
                r'\["npm", "github-actions"\]',
                managers,
                CANONICAL_BOOTSTRAP,
                count=1,
            )
            with self.subTest(managers=managers):
                self.assert_rejected(mutation)

    def test_extra_policy_unsafe_classes_and_release_age_drift_fail_closed(
        self,
    ) -> None:
        additions = [
            '  "automerge": true,\n',
            (
                '  "packageRules": [{"matchUpdateTypes": '
                '["pin", "digest", "pinDigest", "lockFileMaintenance"], '
                '"minimumReleaseAge": "1 day", "automerge": true}],\n'
            ),
            (
                '  "lockFileMaintenance": {"enabled": true, '
                '"minimumReleaseAge": "1 day", "automerge": true},\n'
            ),
            '  "minimumReleaseAge": "1 day",\n',
        ]

        for addition in additions:
            mutation = CANONICAL_BOOTSTRAP.replace(
                '  "enabled": false,\n',
                f'  "enabled": false,\n{addition}',
                1,
            )
            with self.subTest(addition=addition):
                self.assert_rejected(mutation)

    def test_ci_gates_every_job_before_dependency_installation(self) -> None:
        workflow = CI_PATH.read_text(encoding="utf-8")

        validate_ci_policy_gate(workflow)

    def test_workflow_directory_matches_reviewed_allowlist(self) -> None:
        validate_workflow_allowlist(
            [path.name for path in WORKFLOWS_DIR.iterdir() if path.is_file()]
        )

    def test_added_removed_or_renamed_workflows_fail_closed(self) -> None:
        rosters = [
            [*EXPECTED_WORKFLOWS, "nightly-deps.yml"],
            ["ci.yml", "pr-lint.yml"],
            ["ci.yaml", "dependabot-auto-merge.yml", "pr-lint.yml"],
            [*EXPECTED_WORKFLOWS, "ci.yml"],
        ]

        for roster in rosters:
            with self.subTest(roster=roster):
                with self.assertRaises(PolicyError):
                    validate_workflow_allowlist(roster)

    def test_scripts_directory_has_no_stdlib_shadow_surface(self) -> None:
        validate_script_shadow_surface(
            [(entry.name, entry.is_dir()) for entry in (ROOT / "scripts").iterdir()]
        )

    def test_stdlib_shadow_additions_fail_closed(self) -> None:
        policy_entry = ("automation-policy.test.py", False)
        rosters = [
            [policy_entry, ("unittest.py", False)],
            [policy_entry, ("json", True)],
            [policy_entry, ("re.so", False)],
            [policy_entry, ("pathlib.pyc", False)],
            [("unittest.py", False)],
        ]

        for roster in rosters:
            with self.subTest(roster=roster):
                with self.assertRaises(PolicyError):
                    validate_script_shadow_surface(roster)

    def test_no_alternate_renovate_config_sources_exist(self) -> None:
        for rel_path in ALTERNATE_RENOVATE_CONFIG_PATHS:
            with self.subTest(path=rel_path):
                self.assertFalse((ROOT / rel_path).exists())

        package_manifest = json.loads(
            (ROOT / "package.json").read_text(encoding="utf-8")
        )
        self.assertNotIn("renovate", package_manifest)

    def live_pin(self, workflow: str, prefix: str, action: str) -> str:
        """Read an action's current pin from a real step line in the workflow."""

        match = re.search(
            rf"(?m)^{re.escape(prefix)}"
            rf"(?P<pin>{re.escape(action)}@[0-9a-f]{{40}}(?: # v[\w.-]+)?)$",
            workflow,
        )
        if match is None:
            self.fail(f"fixture no longer applies: no pinned {action} in ci.yml")
        return match.group("pin")

    def assert_mutated(self, mutation: str, workflow: str) -> str:
        """Guard against fixtures that silently no-op after workflow drift."""

        self.assertNotEqual(
            mutation, workflow, "fixture no longer applies: mutation is a no-op"
        )
        return mutation

    def test_pinned_prerequisite_sha_bumps_stay_valid(self) -> None:
        workflow = CI_PATH.read_text(encoding="utf-8")
        checkout = self.live_pin(workflow, "      - uses: ", "actions/checkout")
        setup_python = self.live_pin(workflow, "        uses: ", "actions/setup-python")
        bumped = workflow.replace(
            checkout, f"actions/checkout@{'0' * 40} # v99.9.9"
        ).replace(setup_python, f"actions/setup-python@{'1' * 40} # v99")

        self.assert_mutated(bumped, workflow)
        validate_ci_policy_gate(bumped)

    def test_untrusted_or_unpinned_prerequisites_fail_closed(self) -> None:
        workflow = CI_PATH.read_text(encoding="utf-8")
        checkout = self.live_pin(workflow, "      - uses: ", "actions/checkout")
        setup_python = self.live_pin(workflow, "        uses: ", "actions/setup-python")
        mutations = [
            workflow.replace(
                f"      - uses: {checkout}",
                f"      - uses: attacker/checkout@{'a' * 40} # v6",
                1,
            ),
            workflow.replace(f"- uses: {checkout}", "- uses: actions/checkout@v6", 1),
            workflow.replace(
                f"- uses: {checkout}",
                f"- uses: actions/checkout@{'b' * 39} # v6",
                1,
            ),
            workflow.replace(
                "          python-version: '3.x'\n",
                "          python-version: '3.x'\n          cache: pip\n",
                1,
            ),
            workflow.replace(
                f"        uses: {setup_python}\n",
                f"        uses: attacker/setup-python@{'c' * 40} # v6\n",
                1,
            ),
        ]

        for mutation in mutations:
            with self.subTest(mutation=mutation):
                self.assert_mutated(mutation, workflow)
                self.assert_workflow_rejected(mutation)

    def test_ci_policy_execution_bypasses_fail_closed(self) -> None:
        workflow = CI_PATH.read_text(encoding="utf-8")
        mutations = [
            workflow.replace(
                "      - name: Validate disabled Renovate bootstrap\n",
                "      - name: Validate disabled Renovate bootstrap\n"
                "        if: false\n",
                1,
            ),
            workflow.replace(
                f"        run: {POLICY_COMMAND}\n",
                f"        run: {POLICY_COMMAND}\n" "        continue-on-error: true\n",
                1,
            ),
            workflow.replace(
                f"        run: {POLICY_COMMAND}",
                f"        run: echo {POLICY_COMMAND}",
                1,
            ),
            workflow.replace(
                f"        run: {POLICY_COMMAND}",
                f"        # run: {POLICY_COMMAND}",
                1,
            ),
            workflow.replace(
                "      - name: Install Python dependencies\n",
                "      - name: Duplicate disabled Renovate bootstrap\n"
                f"        run: {POLICY_COMMAND}\n\n"
                "      - name: Install Python dependencies\n",
                1,
            ),
            workflow.replace(
                f"        run: {POLICY_COMMAND}\n",
                f"        run: {POLICY_COMMAND}\n" "        shell: python\n",
                1,
            ),
            workflow.replace(
                "        shell: bash\n",
                "        shell: python\n",
                1,
            ),
            workflow.replace(
                "          SHELLOPTS: ''\n",
                "          SHELLOPTS: noexec\n",
                1,
            ),
            workflow.replace(
                "          BASH_ENV: /dev/null\n",
                "          BASH_ENV: /tmp/bypass\n",
                1,
            ),
            workflow.replace(
                "  python-lint:\n",
                "  python-lint:\n    if: false\n",
                1,
            ),
            workflow.replace(
                "  python-lint:\n",
                "  python-lint:\n    if : false\n",
                1,
            ),
            workflow.replace(
                "jobs:\n",
                "defaults:\n  run:\n    shell: python\n\njobs:\n",
                1,
            ),
            workflow.replace(
                "jobs:\n",
                "defaults : {run: {shell: python}}\n\njobs:\n",
                1,
            ),
            workflow.replace(
                "jobs:\n",
                '"defaults": {"run": {"shell": "true {0}"}}\n\njobs:\n',
                1,
            ),
            workflow.replace(
                "jobs:\n",
                "'defaults': {'run': {'shell': 'true {0}'}}\n\njobs:\n",
                1,
            ),
            workflow.replace(
                "jobs:\n",
                '"def\\u0061ults": {"run": {"shell": "true {0}"}}\n\njobs:\n',
                1,
            ),
            workflow.replace(
                "  python-lint:\n",
                '  python-lint:\n    "if": false\n',
                1,
            ),
            workflow.replace(
                "  python-lint:\n",
                '  python-lint:\n    "continue-on-error": true\n',
                1,
            ),
            workflow.replace(
                "  python-lint:\n",
                "  python-lint:\n    !!str continue-on-error: true\n",
                1,
            ),
            workflow.replace(
                "  python-lint:\n",
                "  python-lint:\n    &control continue-on-error: true\n",
                1,
            ),
            workflow.replace(
                "  python-lint:\n",
                "  python-lint:\n    <<: {continue-on-error: true}\n",
                1,
            ),
            workflow.replace(
                "name: CI\n",
                "%YAML 1.2\n---\nname: CI\n",
                1,
            ),
            workflow.replace(
                "jobs:\n",
                "env:\n  CONTROL: &control continue-on-error\n\njobs:\n",
                1,
            ).replace(
                "  python-lint:\n",
                "  python-lint:\n    *control: true\n",
                1,
            ),
            workflow.replace(
                "  python-lint:\n",
                "  python-lint:\n" "    env:\n" "      SHELLOPTS: noexec\n",
                1,
            ),
            workflow.replace(
                "jobs:\n",
                "env:\n  SHELLOPTS: noexec\n\njobs:\n",
                1,
            ),
            workflow.replace(
                "    runs-on: ubuntu-latest\n",
                "    runs-on: self-hosted\n",
                1,
            ),
            workflow.replace(
                "    runs-on: ubuntu-latest\n",
                "    runs-on: ubuntu-latest\n" "    container: attacker/image\n",
                1,
            ),
            workflow.replace(
                "    runs-on: ubuntu-latest\n",
                "    runs-on: ubuntu-latest\n"
                "    strategy:\n"
                "      matrix:\n"
                "        shard: [one, two]\n",
                1,
            ),
            workflow.replace(
                "    runs-on: ubuntu-latest\n",
                "    runs-on: ubuntu-latest\n"
                "    strategy:\n"
                "      matrix:\n"
                "        shard: [only]\n"
                "        exclude:\n"
                "          - shard: only\n",
                1,
            ),
            workflow.replace(
                "    name: Python Lint\n",
                "    name: Alternate Lint\n",
                1,
            ),
            workflow.replace(
                "    runs-on: ubuntu-latest\n",
                "    runs-on: ubuntu-latest\n" "    environment: production\n",
                1,
            ),
            workflow.replace(
                "    runs-on: ubuntu-latest\n",
                "    runs-on: ubuntu-latest\n" "    permissions: write-all\n",
                1,
            ),
            workflow.replace(
                "    runs-on: ubuntu-latest\n",
                "    |-\n"
                "      container\n"
                "    : attacker/image\n"
                "    runs-on: ubuntu-latest\n",
                1,
            ),
            workflow.replace(
                "    runs-on: ubuntu-latest\n",
                "    >-\n"
                "      env\n"
                "    :\n"
                '      BASH_FUNC_python3%%: "() { return 0; }"\n'
                "    runs-on: ubuntu-latest\n",
                1,
            ),
            workflow.replace(
                "      - name: Validate disabled Renovate bootstrap\n",
                "      - uses: attacker/environment-action@deadbeef\n\n"
                "      - name: Validate disabled Renovate bootstrap\n",
                1,
            ),
            workflow.replace(
                "    steps:\n",
                "    steps:\n"
                "      - run: mkdir -p /tmp/b && printf shim > /tmp/b/python3\n",
                1,
            ),
            workflow.replace(
                "    steps:\n",
                "    steps:\n"
                "      -\n"
                "        run: mkdir -p /tmp/b && printf shim > /tmp/b/python3\n",
                1,
            ),
            workflow
            + "\nenv:\n"
            + "    PATH: /home/runner/work/repo/repo/bin:/usr/local/bin:/usr/bin:/bin\n",
        ]

        for mutation in mutations:
            with self.subTest(mutation=mutation):
                self.assert_workflow_rejected(mutation)

    def test_ci_dependency_gate_bypasses_fail_closed(self) -> None:
        workflow = CI_PATH.read_text(encoding="utf-8")
        mutations = [
            workflow.replace("    needs: python-lint\n", "", 1),
            workflow.replace(
                "    needs: python-lint\n",
                "    needs: python-lint\n    needs: python-lint\n",
                1,
            ),
            workflow.replace(
                "  javascript-lint:\n",
                "  ungated-install:\n"
                "    name: Ungated install\n"
                "    runs-on: ubuntu-latest\n"
                "    steps:\n"
                "      - run: npm ci\n\n"
                "  javascript-lint:\n",
                1,
            ),
            workflow.replace(
                "    needs: [test-python, test-javascript]\n",
                "    needs: []\n",
                1,
            ),
            workflow.replace(
                "  javascript-lint:\n",
                "  javascript-lint:\n    if: always()\n",
                1,
            ),
            workflow.replace(
                "  javascript-lint:\n",
                '  "ungated-install":\n'
                "    runs-on: ubuntu-latest\n"
                "    steps:\n"
                "      - run: npm ci\n\n"
                "  javascript-lint:\n",
                1,
            ),
        ]

        for mutation in mutations:
            with self.subTest(mutation=mutation):
                self.assert_workflow_rejected(mutation)


if __name__ == "__main__":
    unittest.main()

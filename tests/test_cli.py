"""Tests for the hcskills CLI."""

from pathlib import Path

from click.testing import CliRunner

from hcskills.cli import TEAM_SKILLS_REPO, TEAM_SKILLS_REPO_URL, cli


class TestCli:
    def test_version(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert "0.1" in result.output

    def test_list(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["list"])
        assert result.exit_code == 0
        assert "834-file-check" in result.output
        assert "free" in result.output
        assert "team" in result.output

    def test_memory_init(self):
        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(cli, ["memory", "init"])
            assert result.exit_code == 0
            assert "CREATE" in result.output

    def test_guard_no_files(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["guard"])
        assert result.exit_code == 0
        assert "No files" in result.output

    def test_guard_clean_file(self):
        runner = CliRunner()
        with runner.isolated_filesystem():
            with open("clean.csv", "w") as f:
                f.write("code,value\nE11.9,test\n")
            result = runner.invoke(cli, ["guard", "clean.csv"])
            assert result.exit_code == 0
            assert "No PHI" in result.output

    def test_guard_phi_file(self):
        runner = CliRunner()
        with runner.isolated_filesystem():
            with open("phi.csv", "w") as f:
                f.write("name,ssn\nFake,987-65-4320\n")
            result = runner.invoke(cli, ["guard", "phi.csv"])
            assert result.exit_code == 1
            assert "PHI DETECTED" in result.output

    def test_update_points_at_team_repo(self):
        assert TEAM_SKILLS_REPO == "blacktj/hc-data-skills-pro"
        assert TEAM_SKILLS_REPO_URL == "https://github.com/blacktj/hc-data-skills-pro.git"
        runner = CliRunner()
        result = runner.invoke(cli, ["update", "--help"])
        assert result.exit_code == 0
        assert "blacktj/hc-data-skills-pro" in result.output

    def test_update_falls_back_to_local_skills(self, monkeypatch):
        monkeypatch.setattr("hcskills.cli._try_clone_skills", lambda repo: None)
        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(cli, ["update", "--target", "cursor"])
            assert result.exit_code == 0
            assert "blacktj/hc-data-skills-pro" in result.output
            dest = Path(".cursor/skills/hc-data-skills")
            assert (dest / "hl7v2-parse" / "SKILL.md").exists()
            assert (dest / "834-file-check" / "SKILL.md").exists()

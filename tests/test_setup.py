"""Installer checks use temporary homes; package/network/system writes are mocked."""
import hashlib
import io
import json
import os
from pathlib import Path
import plistlib
import shutil
import subprocess
import tarfile
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class SetupTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="macos-setup-test-")
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.home = self.base / "home"
        self.home.mkdir()
        self.env = os.environ.copy()
        for key in ("BASH_ENV", "ENV", "XDG_CONFIG_HOME", "BLE_VERSION"):
            self.env.pop(key, None)
        self.env.update(HOME=str(self.home), SETUP_SCRIPT=str(ROOT / "setup.sh"))

    def shell(self, code, *, success=True):
        result = subprocess.run(
            ["/bin/bash", "--noprofile", "--norc", "-c",
             'source "$SETUP_SCRIPT"\n' + code],
            env=self.env, cwd=self.base, stdin=subprocess.DEVNULL,
            text=True, capture_output=True,
        )
        if success:
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        else:
            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        return result

    def test_dry_run_has_no_writes_or_external_actions(self):
        result = self.shell("""
download() { exit 91; }
setup_homebrew() { exit 92; }
sudo() { exit 93; }
main --dry-run
""")
        self.assertIn("brew bundle install --no-upgrade", result.stdout)
        self.assertEqual(list(self.home.iterdir()), [])
        self.assertEqual(list(self.base.iterdir()), [self.home])

    def test_review_displays_the_complete_manifest_only(self):
        result = self.shell("main --review-packages")
        self.assertEqual(result.stdout, (ROOT / "Brewfile").read_text())
        self.assertEqual(list(self.home.iterdir()), [])

    def test_unknown_option_is_rejected(self):
        self.shell("main --unknown", success=False)
        self.assertEqual(list(self.home.iterdir()), [])

    def test_unreviewed_noninteractive_install_is_rejected(self):
        result = self.shell("confirm_packages", success=False)
        self.assertIn("--yes", result.stderr)
        self.assertEqual(list(self.home.iterdir()), [])

    def test_rosetta_is_rejected(self):
        result = self.shell("""
uname() { printf 'Darwin\n'; }
sysctl() { printf '1\n'; }
preflight
""", success=False)
        self.assertIn("原生 Apple Silicon", result.stderr)

    def test_intel_is_rejected(self):
        result = self.shell("""
uname() { if [[ $1 == -s ]]; then echo Darwin; else echo x86_64; fi; }
sysctl() { return 1; }
preflight
""", success=False)
        self.assertIn("只支持 Apple Silicon", result.stderr)

    def test_backup_keeps_original_and_rerun_is_unchanged(self):
        target = self.home / ".bashrc"
        target.write_text("original settings\n")
        self.shell('install_file "$ROOT_DIR/config/bash/bashrc" "$HOME/.bashrc"')
        backups = list(self.home.glob(".local/state/macos-setup/backups/*"))
        self.assertEqual(len(backups), 1)
        self.assertEqual((backups[0] / ".bashrc").read_text(), "original settings\n")
        self.assertEqual(backups[0].stat().st_mode & 0o777, 0o700)
        modified = target.stat().st_mtime_ns
        self.shell('install_file "$ROOT_DIR/config/bash/bashrc" "$HOME/.bashrc"')
        self.assertEqual(target.stat().st_mtime_ns, modified)
        self.assertEqual(list(self.home.glob(".local/state/macos-setup/backups/*")), backups)

    def test_replacing_symlink_preserves_link_and_its_source(self):
        original = self.base / "original-bashrc"
        original.write_text("private settings\n")
        target = self.home / ".bashrc"
        target.symlink_to(original)
        self.shell('install_file "$ROOT_DIR/config/bash/bashrc" "$HOME/.bashrc"')
        self.assertFalse(target.is_symlink())
        self.assertEqual(original.read_text(), "private settings\n")
        backup = next(self.home.glob(".local/state/macos-setup/backups/*/.bashrc"))
        self.assertTrue(backup.is_symlink())
        self.assertEqual(backup.readlink(), original)

    def test_directory_target_is_rejected_without_changes(self):
        (self.home / ".bashrc").mkdir()
        self.shell('install_file "$ROOT_DIR/config/bash/bashrc" "$HOME/.bashrc"', success=False)
        self.assertTrue((self.home / ".bashrc").is_dir())
        self.assertFalse((self.home / ".local").exists())

    def test_configuration_preserves_private_and_active_karabiner_files(self):
        private = self.home / ".bashrc.local"
        private.write_text("private override\n")
        karabiner = self.home / ".config/karabiner"
        karabiner.mkdir(parents=True)
        active = karabiner / "karabiner.json"
        active.write_text('{"profiles": []}\n')
        self.shell("""
WORK_DIR=$(mktemp -d "$HOME/work.XXXXXX")
BASH_BIN=/opt/homebrew/bin/bash
install_configs
rm -rf "$WORK_DIR"
""")
        self.assertEqual(private.read_text(), "private override\n")
        self.assertEqual(active.read_text(), '{"profiles": []}\n')
        rules = list((karabiner / "assets/complex_modifications").glob("*.json"))
        self.assertEqual(len(rules), 2)
        for rule in rules:
            self.assertTrue(json.loads(rule.read_text())["rules"])
        profile = self.home / "Library/Application Support/iTerm2/DynamicProfiles/macos-setup.plist"
        data = plistlib.loads(profile.read_bytes())["Profiles"][0]
        self.assertEqual(data["Command"], "/opt/homebrew/bin/bash -l")
        self.assertIn("Ansi 15 Color", data)
        self.assertEqual((self.home / ".blerc").read_bytes(), (ROOT / "config/bash/blerc").read_bytes())

    def test_noninteractive_bashrc_is_quiet(self):
        result = self.shell('source "$ROOT_DIR/config/bash/bashrc"\nprintf ready')
        self.assertEqual(result.stdout, "ready")
        self.assertEqual(result.stderr, "")

    def test_ffmpeg_full_command_is_available_in_a_new_bash(self):
        prefix = self.base / "brew"
        binary = prefix / "opt/ffmpeg-full/bin"
        binary.mkdir(parents=True)
        executable = binary / "ffmpeg"
        executable.write_text("#!/bin/bash\nprintf full-version")
        executable.chmod(0o755)
        self.env.update(
            HOMEBREW_PREFIX=str(prefix), PATH="/usr/bin:/bin:/usr/sbin:/sbin",
            BASHRC_TEST=str(ROOT / "config/bash/bashrc"),
        )
        result = subprocess.run(
            ["/bin/bash", "--noprofile", "--norc", "-ic",
             'source "$BASHRC_TEST"; source "$BASHRC_TEST"; command -v ffmpeg; ffmpeg; printf "\\n%s" "$PATH"'],
            env=self.env, cwd=self.base, stdin=subprocess.DEVNULL,
            text=True, capture_output=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.splitlines()[0], str(executable))
        self.assertEqual(result.stdout.splitlines()[1], "full-version")
        self.assertEqual(result.stdout.splitlines()[2].split(":").count(str(binary)), 1)

    def test_bad_checksum_stops_before_configuration_writes(self):
        result = self.shell("""
WORK_DIR=$(mktemp -d "$HOME/work.XXXXXX")
BASH_BIN=/bin/bash
download() { printf corrupted > "$2"; }
install_blesh
""", success=False)
        self.assertIn("FAILED", result.stdout + result.stderr)
        self.assertFalse((self.home / ".local/share/blesh").exists())
        self.assertFalse((self.home / ".bashrc").exists())

    def test_shell_registration_and_change_are_idempotent(self):
        self.env.update(FAKE_SHELLS=str(self.base / "shells"), FAKE_LOGIN=str(self.base / "login"))
        (self.base / "shells").write_text("/bin/zsh\n")
        (self.base / "login").write_text("UserShell: /bin/zsh\n")
        self.shell("""
BASH_BIN=/opt/homebrew/bin/bash
grep() { command grep -Fxq "$BASH_BIN" "$FAKE_SHELLS"; }
sudo() { [[ $* == 'tee -a /etc/shells' ]]; cat >> "$FAKE_SHELLS"; }
dscl() { cat "$FAKE_LOGIN"; }
chsh() { [[ $1 == -s ]]; printf 'UserShell: %s\n' "$2" > "$FAKE_LOGIN"; }
setup_login_shell
setup_login_shell
""")
        self.assertEqual((self.base / "shells").read_text().splitlines(), ["/bin/zsh", "/opt/homebrew/bin/bash"])
        self.assertEqual((self.base / "login").read_text(), "UserShell: /opt/homebrew/bin/bash\n")

    def prepare_fake_install(self):
        modern_bash = next((path for path in ("/opt/homebrew/bin/bash", shutil.which("bash"))
                            if path and subprocess.run([path, "-c", "(( BASH_VERSINFO[0] >= 4 ))"],
                                                       capture_output=True).returncode == 0), None)
        if not modern_bash:
            self.skipTest("Mocked full installation requires Bash >= 4")
        prefix = self.base / "brew"
        binary = prefix / "bin"
        binary.mkdir(parents=True)
        (binary / "bash").symlink_to(modern_bash)
        completion = prefix / "etc/profile.d/bash_completion.sh"
        completion.parent.mkdir(parents=True)
        completion.write_text(":\n")
        scripts = {
            "brew": """printf '%s\n' "$*" >> "$CALL_LOG"
case $1 in
  shellenv) printf 'export HOMEBREW_PREFIX=%q\nexport PATH=%q:$PATH\n' "$FAKE_PREFIX" "$FAKE_PREFIX/bin" ;;
  --prefix) printf '%s\n' "$FAKE_PREFIX" ;;
  bundle) [[ ${FAIL_BUNDLE:-0} != 1 ]] || exit 37 ;;
  *) exit 96 ;;
esac
""",
            "vim": """printf 'vim %s\n' "$*" >> "$CALL_LOG"
[[ ${FAIL_VIM:-0} != 1 ]] || exit 38
mkdir -p "$HOME/.vim/plugged/vim-colors-solarized/colors" "$HOME/.vim/plugged/vim-autoformat/plugin"
touch "$HOME/.vim/plugged/vim-colors-solarized/colors/solarized.vim" "$HOME/.vim/plugged/vim-autoformat/plugin/autoformat.vim"
""",
        }
        for name in ("gls", "gdircolors", "gawk", "zoxide"):
            scripts[name] = "exit 0\n"
        for name, content in scripts.items():
            executable = binary / name
            executable.write_text("#!/bin/bash\nset -e\n" + content)
            executable.chmod(0o755)
        ble_script = b'''#!/bin/bash
case ${1-} in
  --version) echo 'ble.sh (Bash Line Editor), version 0.4.0-nightly+d81fd54' ;;
  --install) mkdir -p "$2/blesh"; cp "$0" "$2/blesh/ble.sh" ;;
esac
'''
        archive = self.base / "fixture.tar.xz"
        with tarfile.open(archive, "w:xz") as output:
            member = tarfile.TarInfo("ble-nightly/ble.sh")
            member.size = len(ble_script)
            output.addfile(member, io.BytesIO(ble_script))
        plug = self.base / "plug.vim"
        plug.write_text('" test fixture\n')
        self.env.update(
            FAKE_PREFIX=str(prefix), CALL_LOG=str(self.base / "calls"),
            BLE_FIXTURE=str(archive), PLUG_FIXTURE=str(plug),
            BLE_FIXTURE_SHA=hashlib.sha256(archive.read_bytes()).hexdigest(),
            PLUG_FIXTURE_SHA=hashlib.sha256(plug.read_bytes()).hexdigest(),
        )
        return """
preflight() { :; }
find_brew() { BREW_BIN="$FAKE_PREFIX/bin/brew"; }
download() {
    if [[ $1 == "$BLE_URL" ]]; then cp "$BLE_FIXTURE" "$2";
    elif [[ $1 == "$PLUG_URL" ]]; then cp "$PLUG_FIXTURE" "$2";
    else exit 97; fi
}
BLE_SHA256=$BLE_FIXTURE_SHA
PLUG_SHA256=$PLUG_FIXTURE_SHA
main --yes --no-change-shell
"""

    def test_full_mocked_install_and_rerun(self):
        script = self.prepare_fake_install()
        (self.home / ".bashrc").write_text("original\n")
        self.shell(script)
        modified = (self.home / ".bashrc").stat().st_mtime_ns
        self.shell(script)
        self.assertEqual((self.home / ".bashrc").stat().st_mtime_ns, modified)
        self.assertEqual(len(list(self.home.glob(".local/state/macos-setup/backups/*"))), 1)
        self.assertFalse(list(self.base.glob("macos-setup.*")))
        calls = (self.base / "calls").read_text()
        self.assertIn("bundle install --no-upgrade --file", calls)
        self.assertIn("PlugInstall --sync", calls)
        self.assertTrue((self.home / ".local/share/blesh/ble.sh").exists())

    def test_package_failure_stops_before_config_is_replaced(self):
        script = self.prepare_fake_install()
        self.env["FAIL_BUNDLE"] = "1"
        original = self.home / ".bashrc"
        original.write_text("original\n")
        self.shell(script, success=False)
        self.assertEqual(original.read_text(), "original\n")
        self.assertFalse((self.home / ".vimrc").exists())

    def test_vim_failure_does_not_report_success(self):
        script = self.prepare_fake_install()
        self.env["FAIL_VIM"] = "1"
        result = self.shell(script, success=False)
        self.assertNotIn("配置完成。", result.stdout)
        self.assertIn("失败", result.stderr)
        self.assertIn("38", result.stderr)
        logs = list(self.home.glob(".local/state/macos-setup/logs/vim-*.log"))
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0].stat().st_mode & 0o777, 0o600)
        self.assertIn(str(logs[0]), result.stderr)

    def test_existing_vim_plugin_loads_on_repeated_install(self):
        if not shutil.which("vim"):
            self.skipTest("Requires Vim")
        autoload = self.home / ".vim/autoload"
        autoload.mkdir(parents=True)
        # The manager fixture adds a plugin that uses Vim line continuations,
        # as vim-autoformat does. Ex mode with 'compatible' breaks this syntax.
        manager = autoload / "plug.vim"
        manager.write_text('''function! plug#begin(directory)
execute 'set runtimepath^=' . fnameescape(expand(a:directory) . '/vim-autoformat')
command! -nargs=+ Plug echo ''
command! -nargs=* PlugInstall echo 'Already installed'
endfunction
function! plug#end()
endfunction
''')
        plugin = self.home / ".vim/plugged/vim-autoformat/plugin/autoformat.vim"
        plugin.parent.mkdir(parents=True)
        plugin.write_text("let g:test_formatters = [\n    \\ 'formatter'\n    \\ ]\n")
        color = self.home / ".vim/plugged/vim-colors-solarized/colors/solarized.vim"
        color.parent.mkdir(parents=True)
        color.write_text('" installed fixture\n')
        shutil.copyfile(ROOT / "config/vim/vimrc", self.home / ".vimrc")
        self.env["MANAGER_SHA"] = hashlib.sha256(manager.read_bytes()).hexdigest()
        self.shell('''
WORK_DIR=$(mktemp -d "$HOME/work.XXXXXX")
PLUG_SHA256=$MANAGER_SHA
install_vim_plugins
install_vim_plugins
''')


if __name__ == "__main__":
    unittest.main()

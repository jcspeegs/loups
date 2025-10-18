# https://devenv.sh/reference/options/
{ pkgs, lib, config, inputs, ... }:

{
  # https://devenv.sh/binary-caching/
  cachix.enable = true;
  cachix.pull = [
    "pre-commit-hooks"
                ];

  # https://devenv.sh/basics/
  env.GREET = "devenv";

  # https://devenv.sh/packages/
  packages = with pkgs; [
    git
    nix-ld
    zlib

    # # To avoid using all of these, use opencv-python-headless
    # mesa
    # libglvnd
  ];

  languages.python = {
    enable = true;
    uv.enable = true;
  };

  # https://devenv.sh/processes/
  # processes.dev.exec = "${lib.getExe pkgs.watchexec} -n -- ls -la";

  # https://devenv.sh/services/
  # services.postgres.enable = true;

  # https://devenv.sh/scripts/
  scripts = {
    hello.exec = ''
      echo hello from $GREET
    '';
  };

  # https://devenv.sh/basics/
  enterShell = ''
    hello         # Run scripts directly
    git --version # Use packages
  '';

  # https://devenv.sh/tasks/
  # tasks = {
  #   "myproj:setup".exec = "mytool build";
  #   "devenv:enterShell".after = [ "myproj:setup" ];
  # };

  # https://devenv.sh/tests/
  enterTest = ''
    echo "Running tests"
    git --version | grep --color=auto "${pkgs.git.version}"
  '';

  # https://devenv.sh/git-hooks/
  # git-hooks.hooks.shellcheck.enable = true;
  git-hooks.hooks = {
    black.enable = true;
    flake8.enable = true;
    isort.enable = true;
  };

  # See full reference at https://devenv.sh/reference/options/
}

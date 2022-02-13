{
  description = "Lightweight ARTIQ communication tools";

  inputs.nixpkgs.url = github:NixOS/nixpkgs/nixos-21.11;
  inputs.sipyco.url = github:m-labs/sipyco;
  inputs.sipyco.inputs.nixpkgs.follows = "nixpkgs";

  outputs = { self, nixpkgs, sipyco }:
    let
      pkgs = import nixpkgs { system = "x86_64-linux"; };
      deps = [ pkgs.python3Packages.numpy pkgs.python3Packages.aiohttp sipyco.packages.x86_64-linux.sipyco ];
    in rec {
      packages.x86_64-linux = {
        artiq-comtools = pkgs.python3Packages.buildPythonPackage {
          pname = "artiq-comtools";
          version = "1.1";
          src = self;
          propagatedBuildInputs = deps;
        };
      };

      defaultPackage.x86_64-linux = packages.x86_64-linux.artiq-comtools;

      devShell.x86_64-linux = pkgs.mkShell {
        name = "artiq-comtools-dev-shell";
        buildInputs = [
          (pkgs.python3.withPackages(ps: deps))
        ];
      };
    };
}

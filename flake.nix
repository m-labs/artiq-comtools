{
  description = "Lightweight ARTIQ communication tools";

  inputs.nixpkgs.url = github:NixOS/nixpkgs/nixos-22.05;
  inputs.sipyco.url = github:m-labs/sipyco;
  inputs.sipyco.inputs.nixpkgs.follows = "nixpkgs";
  inputs.flake-utils.url = github:numtide/flake-utils;

  outputs = { self, nixpkgs, sipyco, flake-utils }:
    flake-utils.lib.eachSystem [ "x86_64-linux" "aarch64-linux" ] (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        deps = [ pkgs.python3Packages.numpy pkgs.python3Packages.aiohttp sipyco.packages.${system}.sipyco ];
      in rec {
        packages = {
          artiq-comtools = pkgs.python3Packages.buildPythonPackage {
            pname = "artiq-comtools";
            version = "1.1";
            src = self;
            propagatedBuildInputs = deps;
          };
        };

        defaultPackage = packages.artiq-comtools;

        devShell = pkgs.mkShell {
          name = "artiq-comtools-dev-shell";
          buildInputs = [
            (pkgs.python3.withPackages(ps: deps))
          ];
        };
      }
    );
  }

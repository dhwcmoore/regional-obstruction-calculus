# Pinned formal-verification environment for regional-obstruction-calculus.
#
# Reproduces exactly the versions REPRODUCIBILITY.md's own "Verified
# toolchain versions" table names -- Coq/Rocq 8.18.0, OCaml 4.14.1,
# Python 3.12 -- from Ubuntu 24.04 LTS's own apt archive, not opam.
# Confirmed by hand, on a real Ubuntu 24.04 system: `apt-get install
# coq ocaml` installs coq 8.18.0+dfsg-1build2 and ocaml
# 4.14.1-1ubuntu1 side by side, with no separate opam switch required
# -- unlike .github/workflows/formal-verification.yml's CI, which
# builds Coq inside a coqorg/coq:8.18.0 container (an internal OCaml
# switch, 4.13.1+flambda, used only to build Coq itself) and installs
# this project's own pinned OCaml 4.14.1 into a second, separate
# switch via the ocaml/setup-ocaml action. This Dockerfile is a second,
# independently reproducible route to the same pinned versions, not a
# copy of CI's own mechanism -- deliberately simpler, since an
# evaluator replaying this by hand does not need two OCaml switches.
#
# This file was written and its apt package names verified against a
# real Ubuntu 24.04 install with these exact versions present, but
# `docker build` itself was not run against it in the environment that
# wrote it (no Docker available there). The verify-versions step below
# exists precisely because of that gap: it fails the build loudly, at
# the versions it actually installed, rather than silently proceeding
# if Ubuntu's archive ever serves a different coq/ocaml build than the
# one this file was checked against.

FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
      coq \
      ocaml \
      python3 \
      python3-venv \
      python3-pip \
      make \
      git \
      ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Fail loudly, not silently, if the archive ever serves different
# pinned versions than the ones REPRODUCIBILITY.md names and this
# image was written against.
RUN coqc_version="$(coqc --version | head -1)" && \
    case "$coqc_version" in \
      *"version 8.18.0"*) ;; \
      *) echo "ERROR: expected Coq 8.18.0, got: $coqc_version" >&2; exit 1 ;; \
    esac && \
    ocaml_version="$(ocamlopt -version)" && \
    case "$ocaml_version" in \
      4.14.1) ;; \
      *) echo "ERROR: expected OCaml 4.14.1, got: $ocaml_version" >&2; exit 1 ;; \
    esac && \
    echo "verified: Coq/Rocq $coqc_version, OCaml $ocaml_version"

WORKDIR /repo
COPY . .

RUN python3 -m venv .venv \
    && .venv/bin/pip install --upgrade pip \
    && .venv/bin/pip install -r requirements.txt

# Runs every check make check-all runs, in the same order, stopping at
# the first failure -- see REPRODUCIBILITY.md for what each stage
# proves and does not prove. The default command; override with
# `docker run <image> make check-rocq-trust PYTHON=.venv/bin/python`
# (for example) to run one stage on its own.
CMD ["make", "check-all", "PYTHON=.venv/bin/python"]

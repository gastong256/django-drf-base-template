#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

SENTINEL=".initialized"

if [[ -f "$SENTINEL" ]]; then
    echo "Repository already initialized. Delete '$SENTINEL' to re-run bootstrap."
    exit 0
fi

# ── Collect values ────────────────────────────────────────────────────────────
# Accept values from env vars (for CI/non-interactive use) or prompt.

ask() {
    local var_name="$1"
    local prompt="$2"
    local default="${3:-}"

    if [[ -n "${!var_name:-}" ]]; then
        echo "  $prompt: ${!var_name} (from env)"
        return
    fi

    if [[ -n "$default" ]]; then
        read -rp "  $prompt [$default]: " value
        printf -v "$var_name" '%s' "${value:-$default}"
    else
        while [[ -z "${!var_name:-}" ]]; do
            read -rp "  $prompt: " value
            printf -v "$var_name" '%s' "$value"
        done
    fi
}

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║   Django DRF Template — Bootstrap Init   ║"
echo "╚══════════════════════════════════════════╝"
echo ""

ask PROJECT_NAME   "Project name (e.g. Acme API)"
ask PROJECT_SLUG   "Python package slug (e.g. acme_api)"
ask SERVICE_NAME   "Docker service name (e.g. acme-api)"
ask OWNER          "Owner / team"
ask DESCRIPTION    "Short description"
ask PORT           "Port" "8000"

# Validate slug: only lowercase letters, digits, underscores
if ! echo "$PROJECT_SLUG" | grep -qE '^[a-z][a-z0-9_]*$'; then
    echo "ERROR: PROJECT_SLUG must be lowercase letters, digits, and underscores only."
    exit 1
fi

# ── Generate secret key ───────────────────────────────────────────────────────
if command -v python3 &>/dev/null; then
    DJANGO_SECRET_KEY="$(python3 -c "
import secrets, string
chars = string.ascii_letters + string.digits + '!@#\$%^&*(-_=+)'
print(''.join(secrets.choice(chars) for _ in range(50)))
")"
else
    DJANGO_SECRET_KEY="$(head -c 50 /dev/urandom | base64 | tr -d '\n/+=' | head -c 50)"
fi

echo ""
echo "Replacing placeholders..."

# Files to process (exclude binary, git, .venv, node_modules)
INCLUDE_PATTERNS=(
    "*.py" "*.toml" "*.yml" "*.yaml" "*.md" "*.json" "*.sh"
    "*.txt" "*.cfg" "*.ini" "*.env" "*.example" "Makefile" "Dockerfile"
)

EXCLUDE_DIRS=(".git" ".venv" "node_modules" "__pycache__" "*.egg-info" "htmlcov")
EXCLUDE_FILES=("scripts/bootstrap.sh")

build_find_args() {
    FIND_EXCLUDE_ARGS=()
    for d in "${EXCLUDE_DIRS[@]}"; do
        FIND_EXCLUDE_ARGS+=(-not -path "*/$d/*" -not -path "*/$d")
    done
    for f in "${EXCLUDE_FILES[@]}"; do
        FIND_EXCLUDE_ARGS+=(-not -path "./$f")
    done
}

replace_in_files() {
    local placeholder="$1"
    local value="$2"

    # Escape replacement value for sed (`&` expands to the full match).
    local escaped_value
    escaped_value="$(printf '%s\n' "$value" | sed -e 's/[&|\\]/\\&/g')"

    for pattern in "${INCLUDE_PATTERNS[@]}"; do
        build_find_args
        find . "${FIND_EXCLUDE_ARGS[@]}" -type f -name "$pattern" \
            -exec grep -lF "$placeholder" {} \; \
            | while IFS= read -r file; do
                sed -i "s|${placeholder}|${escaped_value}|g" "$file"
                echo "  patched: $file"
            done
    done
}

replace_in_files "__PROJECT_NAME__"      "$PROJECT_NAME"
replace_in_files "__PROJECT_SLUG__"      "$PROJECT_SLUG"
replace_in_files "__SERVICE_NAME__"      "$SERVICE_NAME"
replace_in_files "__OWNER__"             "$OWNER"
replace_in_files "__DESCRIPTION__"       "$DESCRIPTION"
replace_in_files "__PORT__"              "$PORT"

cleanup_makefile() {
    local file="Makefile"
    [[ -f "$file" ]] || return 0

    awk '
      BEGIN {skip_init=0}
      {
        if ($0 ~ /^\.PHONY:/) {
          n = split($0, parts, /[[:space:]]+/)
          out = parts[1]
          for (i = 2; i <= n; i++) {
            if (parts[i] != "" && parts[i] != "init") {
              out = out " " parts[i]
            }
          }
          print out
          next
        }

        if ($0 ~ /^init:[[:space:]]*## /) {
          skip_init=1
          next
        }

        if (skip_init) {
          if ($0 ~ /^[a-zA-Z_-]+:[[:space:]]*## /) {
            skip_init=0
            print $0
          }
          next
        }

        print $0
      }
    ' "$file" > "${file}.tmp" && mv "${file}.tmp" "$file"
}

cleanup_readme_template_section() {
    local file="README.md"
    [[ -f "$file" ]] || return 0

    awk '
      BEGIN {skip_section=0}
      $0 == "- [Using This Template](#using-this-template)" {next}
      $0 == "## Using This Template" {skip_section=1; next}
      skip_section && $0 ~ /^## / {skip_section=0}
      !skip_section {print}
    ' "$file" > "${file}.tmp" && mv "${file}.tmp" "$file"
}

cleanup_template_artifacts() {
    local files=(
        "scripts/bootstrap.sh"
        ".github/workflows/template-only.yml"
    )

    echo ""
    echo "Cleaning template-only artifacts..."
    cleanup_makefile
    cleanup_readme_template_section

    for file in "${files[@]}"; do
        if [[ -f "$file" ]]; then
            rm -f "$file"
            echo "  removed: $file"
        fi
    done
}

run_non_blocking() {
    local description="$1"
    shift

    if "$@"; then
        return 0
    fi

    echo "WARNING: ${description} failed."
    return 1
}

# ── Rename postman files ──────────────────────────────────────────────────────
if ls postman/__PROJECT_SLUG__*.json &>/dev/null 2>&1; then
    :  # Already replaced above — nothing to rename
fi

# Rename any remaining __PROJECT_SLUG__ in filenames
find postman/ -name "*__PROJECT_SLUG__*" | while IFS= read -r f; do
    new_name="${f//__PROJECT_SLUG__/$PROJECT_SLUG}"
    mv "$f" "$new_name"
    echo "  renamed: $f → $new_name"
done

# ── Create .env from .env.example ─────────────────────────────────────────────
if [[ ! -f .env ]]; then
    cp .env.example .env
    echo "Created .env from .env.example"
fi
# Patch the generated secret key directly into .env (if placeholder is present)
sed -i "s|__DJANGO_SECRET_KEY__|${DJANGO_SECRET_KEY}|g" .env

# ── Stamp sentinel early (project is now initialized even if installs fail) ──
echo "$PROJECT_SLUG" > "$SENTINEL"
echo "timestamp=$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$SENTINEL"

BOOTSTRAP_SKIP_SYNC="${BOOTSTRAP_SKIP_SYNC:-false}"
BOOTSTRAP_SKIP_PRE_COMMIT="${BOOTSTRAP_SKIP_PRE_COMMIT:-false}"
BOOTSTRAP_CLEAN_TEMPLATE="${BOOTSTRAP_CLEAN_TEMPLATE:-true}"
if [[ "$BOOTSTRAP_CLEAN_TEMPLATE" == "true" ]]; then
    cleanup_template_artifacts
else
    echo "Skipping template artifact cleanup (BOOTSTRAP_CLEAN_TEMPLATE=false)."
fi

echo ""
# ── Install deps ──────────────────────────────────────────────────────────────
if [[ "$BOOTSTRAP_SKIP_SYNC" == "true" ]]; then
    echo "Skipping dependency installation (BOOTSTRAP_SKIP_SYNC=true)."
else
    echo "Installing dependencies..."
    if command -v uv &>/dev/null; then
        if ! run_non_blocking "Dependency installation (uv sync)" uv sync; then
            echo "  Run 'uv sync' manually to finish setup."
        fi
    else
        echo "WARNING: uv not found. Install uv and run 'uv sync' manually."
        echo "  curl -LsSf https://astral.sh/uv/install.sh | sh"
    fi
fi

# ── Install pre-commit hooks ──────────────────────────────────────────────────
if [[ "$BOOTSTRAP_SKIP_PRE_COMMIT" == "true" ]]; then
    echo "Skipping pre-commit hook installation (BOOTSTRAP_SKIP_PRE_COMMIT=true)."
elif [[ "$BOOTSTRAP_SKIP_SYNC" == "true" ]]; then
    echo "Skipping pre-commit hook installation because dependency sync was skipped."
elif command -v uv &>/dev/null; then
    echo "Installing pre-commit hooks..."
    if ! run_non_blocking "pre-commit hook installation" uv run pre-commit install; then
        echo "  Run 'uv run pre-commit install' manually."
    fi
fi

echo ""
echo "✓ Bootstrap complete."
echo ""
echo "Next steps:"
echo "  docker compose up -d postgres"
echo "  make migrate"
echo "  make run"

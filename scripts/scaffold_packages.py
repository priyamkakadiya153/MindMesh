import os
import shutil

script_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(script_dir)
packages_dir = os.path.join(root_dir, "packages")
shared_dir = os.path.join(packages_dir, "shared")

# Define target package names
pkg_types = os.path.join(packages_dir, "types")
pkg_utils = os.path.join(packages_dir, "utils")
pkg_ui = os.path.join(packages_dir, "ui")
pkg_config = os.path.join(packages_dir, "config")
pkg_eslint = os.path.join(packages_dir, "eslint-config")

# Standard package structure
tsconfig_content = """{
  "extends": "../../tsconfig.json",
  "compilerOptions": {
    "outDir": "./dist",
    "rootDir": "./src"
  },
  "include": ["src/**/*"]
}
"""

print("Starting package scaffolding...")

# 1. Create directory structures
for pkg in [pkg_types, pkg_utils, pkg_ui, pkg_config, pkg_eslint]:
    os.makedirs(pkg, exist_ok=True)
    if pkg != pkg_eslint:
        os.makedirs(os.path.join(pkg, "src"), exist_ok=True)

# 2. Setup packages/types (migrate shared schema)
types_pkg_json = """{
  "name": "@mindmesh/types",
  "version": "1.0.0",
  "private": true,
  "main": "./dist/index.js",
  "types": "./dist/index.d.ts",
  "scripts": {
    "build": "tsc"
  },
  "dependencies": {
    "zod": "^3.22.4"
  },
  "devDependencies": {
    "typescript": "^5.0.0"
  }
}
"""
with open(os.path.join(pkg_types, "package.json"), "w") as f:
    f.write(types_pkg_json)
with open(os.path.join(pkg_types, "tsconfig.json"), "w") as f:
    f.write(tsconfig_content)

# Copy old index.ts schema code to packages/types/src/index.ts
src_shared_file = os.path.join(shared_dir, "src", "index.ts")
dest_types_file = os.path.join(pkg_types, "src", "index.ts")
if os.path.exists(src_shared_file):
    shutil.copyfile(src_shared_file, dest_types_file)
    print(f"Migrated types from shared into types: {dest_types_file}")
else:
    # Fallback placeholder if shared does not exist
    with open(dest_types_file, "w") as f:
        f.write("// Shared Types\n")
    print(f"Created fallback: {dest_types_file}")

# 3. Setup packages/utils
utils_pkg_json = """{
  "name": "@mindmesh/utils",
  "version": "1.0.0",
  "private": true,
  "main": "./dist/index.js",
  "types": "./dist/index.d.ts",
  "scripts": {
    "build": "tsc"
  },
  "devDependencies": {
    "typescript": "^5.0.0"
  }
}
"""
with open(os.path.join(pkg_utils, "package.json"), "w") as f:
    f.write(utils_pkg_json)
with open(os.path.join(pkg_utils, "tsconfig.json"), "w") as f:
    f.write(tsconfig_content)
with open(os.path.join(pkg_utils, "src", "index.ts"), "w") as f:
    f.write("// Reusable pure utility functions\nexport const formatSize = (bytes: number) => `${(bytes / 1024).toFixed(2)} KB`;\n")

# 4. Setup packages/ui
ui_pkg_json = """{
  "name": "@mindmesh/ui",
  "version": "1.0.0",
  "private": true,
  "main": "./dist/index.js",
  "types": "./dist/index.d.ts",
  "scripts": {
    "build": "tsc"
  },
  "dependencies": {
    "react": "^18.2.0"
  },
  "devDependencies": {
    "typescript": "^5.0.0"
  }
}
"""
with open(os.path.join(pkg_ui, "package.json"), "w") as f:
    f.write(ui_pkg_json)
with open(os.path.join(pkg_ui, "tsconfig.json"), "w") as f:
    f.write(tsconfig_content)
with open(os.path.join(pkg_ui, "src", "index.ts"), "w") as f:
    f.write("// Reusable pure UI component library\nexport const ButtonPlaceholder = () => null;\n")

# 5. Setup packages/config
config_pkg_json = """{
  "name": "@mindmesh/config",
  "version": "1.0.0",
  "private": true,
  "main": "./dist/index.js",
  "types": "./dist/index.d.ts",
  "scripts": {
    "build": "tsc"
  },
  "devDependencies": {
    "typescript": "^5.0.0"
  }
}
"""
with open(os.path.join(pkg_config, "package.json"), "w") as f:
    f.write(config_pkg_json)
with open(os.path.join(pkg_config, "tsconfig.json"), "w") as f:
    f.write(tsconfig_content)
with open(os.path.join(pkg_config, "src", "index.ts"), "w") as f:
    f.write("// Shared constants and configuration settings\nexport const APP_VERSION = '1.0.0';\n")

# 6. Setup packages/eslint-config
eslint_pkg_json = """{
  "name": "@mindmesh/eslint-config",
  "version": "1.0.0",
  "private": true,
  "main": "./index.js"
}
"""
with open(os.path.join(pkg_eslint, "package.json"), "w") as f:
    f.write(eslint_pkg_json)
with open(os.path.join(pkg_eslint, "index.js"), "w") as f:
    f.write("module.exports = {\n  rules: {}\n};\n")

# 7. Remove packages/shared folder safely
if os.path.exists(shared_dir):
    shutil.rmtree(shared_dir)
    print("Deleted deprecated packages/shared directory.")

print("All package folders initialized successfully.")

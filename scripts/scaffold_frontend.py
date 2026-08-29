import os

# Calculate absolute paths relative to the monorepo root
script_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(script_dir)
frontend_src = os.path.join(root_dir, "apps", "web", "src")

directories = [
    os.path.join(frontend_src, "app"),
    os.path.join(frontend_src, "domains", "authentication"),
    os.path.join(frontend_src, "domains", "users"),
    os.path.join(frontend_src, "domains", "conversations"),
    os.path.join(frontend_src, "domains", "messages"),
    os.path.join(frontend_src, "domains", "files"),
    os.path.join(frontend_src, "domains", "knowledge"),
    os.path.join(frontend_src, "domains", "search"),
    os.path.join(frontend_src, "domains", "notifications"),
    os.path.join(frontend_src, "domains", "dashboard"),
    os.path.join(frontend_src, "domains", "settings"),
    os.path.join(frontend_src, "shared", "components"),
    os.path.join(frontend_src, "shared", "ui"),
    os.path.join(frontend_src, "layouts"),
    os.path.join(frontend_src, "hooks"),
    os.path.join(frontend_src, "services"),
    os.path.join(frontend_src, "providers"),
    os.path.join(frontend_src, "assets"),
    os.path.join(frontend_src, "styles"),
    os.path.join(frontend_src, "types"),
    os.path.join(frontend_src, "utils"),
    os.path.join(frontend_src, "constants"),
    os.path.join(frontend_src, "config"),
    os.path.join(frontend_src, "routes"),
    os.path.join(frontend_src, "lib"),
]

print("Starting frontend folder structure scaffolding using absolute paths...")

for folder in directories:
    os.makedirs(folder, exist_ok=True)
    keep_file = os.path.join(folder, ".gitkeep")
    if not os.path.exists(keep_file):
        with open(keep_file, "w") as f:
            f.write("# Keep directory structure tracked by Git\n")
        print(f"Created: {keep_file}")

print("Folder scaffolding successfully completed.")

import os

# Calculate absolute paths relative to the monorepo root
script_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(script_dir)
backend_app = os.path.join(root_dir, "apps", "api", "app")
backend_tests = os.path.join(root_dir, "apps", "api", "tests")
backend_alembic = os.path.join(root_dir, "apps", "api", "alembic")

# Core directories inside app/
core_directories = [
    os.path.join(backend_app, "core"),
    os.path.join(backend_app, "shared"),
    os.path.join(backend_app, "ai"),
    os.path.join(backend_app, "api", "v1"),
    os.path.join(backend_app, "middleware"),
    os.path.join(backend_app, "websocket"),
    os.path.join(backend_app, "workers"),
    os.path.join(backend_app, "database"),
    os.path.join(backend_app, "storage"),
    os.path.join(backend_app, "config"),
    os.path.join(backend_app, "utils"),
    backend_tests,
    backend_alembic
]

# Domain names to scaffold
domains = [
    "authentication",
    "users",
    "conversations",
    "messages",
    "files",
    "knowledge",
    "search",
    "notifications",
    "dashboard",
    "settings",
    "administration"
]

# Inner folders for each domain
domain_subfolders = [
    "api",
    "services",
    "repositories",
    "models",
    "schemas",
    "validators",
    "dependencies",
    "events",
    "exceptions",
    "constants"
]

print("Starting backend modular clean architecture scaffolding...")

# 1. Create Core Folders
for folder in core_directories:
    os.makedirs(folder, exist_ok=True)
    # create __init__.py in python package directories
    if "alembic" not in folder and "tests" not in folder:
        init_file = os.path.join(folder, "__init__.py")
        if not os.path.exists(init_file):
            with open(init_file, "w") as f:
                f.write(f"# Initialize {os.path.basename(folder)} module\n")
            print(f"Created package: {init_file}")
    
    keep_file = os.path.join(folder, ".gitkeep")
    if not os.path.exists(keep_file):
        with open(keep_file, "w") as f:
            f.write("# Keep directory structure tracked by Git\n")
        print(f"Created: {keep_file}")

# 2. Create Domain Folders with Subfolders
for domain in domains:
    domain_root = os.path.join(backend_app, "domains", domain)
    os.makedirs(domain_root, exist_ok=True)
    
    # Init for the domain root
    domain_init = os.path.join(domain_root, "__init__.py")
    if not os.path.exists(domain_init):
        with open(domain_init, "w") as f:
            f.write(f"# {domain.capitalize()} Domain Module\n")
        print(f"Created domain root: {domain_init}")
        
    for sub in domain_subfolders:
        sub_folder = os.path.join(domain_root, sub)
        os.makedirs(sub_folder, exist_ok=True)
        
        # Init inside subfolder
        sub_init = os.path.join(sub_folder, "__init__.py")
        if not os.path.exists(sub_init):
            with open(sub_init, "w") as f:
                f.write(f"# {domain.capitalize()} {sub.capitalize()} Layer\n")
        
        keep_file = os.path.join(sub_folder, ".gitkeep")
        if not os.path.exists(keep_file):
            with open(keep_file, "w") as f:
                f.write("# Keep directory structure tracked by Git\n")
            print(f"Created: {keep_file}")

print("Backend scaffolding successfully completed.")

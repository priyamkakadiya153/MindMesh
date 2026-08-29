MIME_TYPE_MAPPING = {
    # Documents
    "application/pdf": "pdf",
    "application/msword": "doc",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
    "text/plain": "txt",
    "text/markdown": "md",
    "text/x-markdown": "md",
    "application/rtf": "rtf",
    "text/rtf": "rtf",
    "application/vnd.oasis.opendocument.text": "odt",
    
    # Spreadsheets
    "application/vnd.ms-excel": "xls",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "xlsx",
    "text/csv": "csv",
    "application/csv": "csv",
    
    # Presentations
    "application/vnd.ms-powerpoint": "ppt",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation": "pptx",
    
    # Images
    "image/png": "png",
    "image/jpeg": "jpeg",
    "image/jpg": "jpg",
    "image/gif": "gif",
    "image/webp": "webp",
    
    # Code
    "text/x-java-source": "java",
    "text/x-java": "java",
    "text/x-python": "py",
    "application/x-python": "py",
    "text/javascript": "js",
    "application/javascript": "js",
    "text/typescript": "ts",
    "application/typescript": "ts",
    "text/x-c": "c",
    "text/x-c++": "cpp",
    "text/html": "html",
    "text/css": "css",
    "application/json": "json",
    "text/json": "json",
    "application/xml": "xml",
    "text/xml": "xml",
    "application/x-yaml": "yaml",
    "text/yaml": "yaml",
    "text/x-yaml": "yaml",
    "application/sql": "sql",
    "text/x-sql": "sql",
    
    # Archives
    "application/zip": "zip",
    "application/x-zip-compressed": "zip",
    "application/x-tar": "tar",
    "application/gzip": "gz",
    "application/x-gzip": "gz",

    # Specialized Formats
    "application/x-tajima-dst": "dst",
    "application/x-brother-pes": "pes",
    "application/x-janome-jef": "jef",
    "application/x-melco-exp": "exp"
}

ALLOWED_EXTENSIONS = {
    "pdf", "doc", "docx", "txt", "rtf", "odt", "md",
    "xls", "xlsx", "csv",
    "ppt", "pptx",
    "png", "jpg", "jpeg", "gif", "webp",
    "java", "py", "js", "ts", "c", "cpp", "html", "css", "json", "xml", "yaml", "yml", "sql",
    "zip", "tar", "gz",
    "dst", "pes", "jef", "exp"
}

REJECTED_EXECUTABLE_EXTENSIONS = {
    "exe", "dll", "bat", "cmd", "sh", "bash", "vbs", "ps1", "scr", "com", "bin", "msi", "app", "dmg"
}


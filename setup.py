install_requires=[
    line.strip()
    for line in open("requirements.txt", "r", encoding="utf-8").readlines()
    if not line.startswith("#") and line.strip()
],
import os

os.environ.setdefault("LOKY_MAX_CPU_COUNT", "1")

from mining_system.cli import main


if __name__ == "__main__":
    main()

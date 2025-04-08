#!/bin/bash

# Simple installation script for textcleaner
set -e

# Determine the directory where the script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Create the global executable
echo "Creating global 'textcleaner' command..."
cat > /usr/local/bin/textcleaner << EOF
#!/bin/bash

# Activate the virtual environment
source "${SCRIPT_DIR}/venv/bin/activate"

# Run the text processor CLI with all arguments
python -m textcleaner.cli "\$@"
EOF

# Make the command executable
chmod +x /usr/local/bin/textcleaner

echo "Installation complete! You can now use 'textcleaner' from anywhere."
echo "Example usage: textcleaner process your_directory/"

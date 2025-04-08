# Homebrew Tap for TextCleaner

This directory contains the Homebrew formula for installing the LLM Text Preprocessing Tool under the snappier name "textcleaner".

## Installation Instructions

```bash
# Add this tap to your Homebrew
brew tap emil7051/textcleaner https://github.com/emil7051/llm-text-processor

# Install textcleaner
brew install textcleaner
```

After installation, you can use the tool with the simple command:

```bash
textcleaner process myfile.pdf
```

## Updating

To update the formula when new versions are released:

```bash
brew update
brew upgrade textcleaner
```

## Uninstalling

```bash
brew uninstall textcleaner
brew untap emil7051/textcleaner
```

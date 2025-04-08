class Textcleaner < Formula
  include Language::Python::Virtualenv

  desc "Text cleaning tool for LLM processing"
  homepage "https://github.com/emil7051/textcleaner"
  url "https://github.com/emil7051/textcleaner/archive/refs/tags/v0.1.0.tar.gz"
  sha256 "TBD" # Will be updated when you create the release
  license "MIT"
  head "https://github.com/emil7051/textcleaner.git", branch: "main"

  depends_on "python@3.9"
  
  resource "beautifulsoup4" do
    url "https://files.pythonhosted.org/packages/af/0b/44c39cf3b18a9280950ad63a579ce395dda4c32193ee9da7ff0aed547094/beautifulsoup4-4.12.2.tar.gz"
    sha256 "492bbc69dca35d12daac71c4db1bfff0c876c00ef4a2ffacce226d4638eb72da"
  end

  resource "click" do
    url "https://files.pythonhosted.org/packages/96/d3/f04c7bfcf5c1862a2a5b845c6b2b360488cf47af55dfa79c98f6a6bf98b5/click-8.1.7.tar.gz"
    sha256 "ca9853ad459e787e2192211578cc907e7594e294c7ccc834310722b41b9ca6de"
  end

  resource "pypdf" do
    url "https://files.pythonhosted.org/packages/23/38/5e123ad1b071f6aa068d6c39ddc2993ce9355bb8403b40d7feb564b9abb8/pypdf-3.17.4.tar.gz"
    sha256 "ddb115c11b998d1b59e5998255b18c0d1f3822f5c35b51eaa880e3a31c91fd9d"
  end

  resource "pyyaml" do
    url "https://files.pythonhosted.org/packages/cd/e5/af35f7ea75cf72f2cd079c95ee16797de7cd71f29ea7c68ae5ce7be1eda0/PyYAML-6.0.1.tar.gz"
    sha256 "bfdf460b1736c775f2ba9f6a92bca30bc2095067b8a9d77876d1fad6cc3b4a43"
  end

  def install
    virtualenv_install_with_resources
    
    # Create a wrapper script to invoke the CLI
    (bin/"textcleaner").write <<~EOS
      #!/bin/bash
      exec "#{libexec}/bin/python" -m textcleaner.cli "$@"
    EOS
  end

  test do
    system "#{bin}/textcleaner", "--version"
  end
end

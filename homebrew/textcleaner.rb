class Textcleaner < Formula
  include Language::Python::Virtualenv
  
  desc "Text preprocessing tool for Large Language Models"
  homepage "https://github.com/emil7051/llm-text-processor"
  url "https://github.com/emil7051/llm-text-processor/archive/refs/heads/main.zip"
  version "0.1.0"
  sha256 "" # This will be filled automatically by brew when auditing
  license "MIT"

  depends_on "python@3.9"
  depends_on "tesseract" => :recommended
  depends_on "poppler" => :recommended
  depends_on "lxml" => :recommended

  def install
    virtualenv_install_with_resources
    
    # Add CLI shortcut
    bin.install_symlink "#{libexec}/bin/llm-text-processor" => "textcleaner"
  end

  test do
    system "#{bin}/textcleaner", "--version"
  end
end

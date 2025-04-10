class Textcleaner < Formula
  include Language::Python::Virtualenv

  desc "Text cleaning tool for LLM processing"
  homepage "https://github.com/emil7051/textcleaner"
  url "https://github.com/emil7051/textcleaner/archive/refs/tags/v0.5.8.tar.gz"
  sha256 "1710253c1598de31c1d5e7fd41d71b115988b7d4ffbd344a08e4ab554c3dc8f4"
  license "MIT"
  head "https://github.com/emil7051/textcleaner.git", branch: "main"

  depends_on "python@3.11"

  # Dependencies are now installed directly from pyproject.toml via pip

  def install
    # Create venv
    venv = virtualenv_create(libexec, "python3.11")

    # Install the package itself along with dependencies specified in pyproject.toml
    venv.pip_install_and_link "."

    # Ensure the executable script is created and linked
    (bin/"textcleaner").write_env_script libexec/"bin/textcleaner", PATH: "#{libexec}/bin:$PATH"
  end

  test do
    system "#{bin}/textcleaner", "--version"
  end
end

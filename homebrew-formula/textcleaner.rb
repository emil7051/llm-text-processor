class Textcleaner < Formula
  include Language::Python::Virtualenv

  desc "Text cleaning tool for LLM processing"
  homepage "https://github.com/emil7051/textcleaner"
  url "https://github.com/emil7051/textcleaner/archive/refs/tags/v0.5.4.tar.gz"
  sha256 "db16005706c5f45d1d504b69f8ae4866472653975f45cc106a0635e23cbafb4a"
  license "MIT"
  head "https://github.com/emil7051/textcleaner.git", branch: "main"

  depends_on "python@3.11"
  
  resource "pyyaml" do
    url "https://files.pythonhosted.org/packages/cd/e5/af35f7ea75cf72f2cd079c95ee16797de7cd71f29ea7c68ae5ce7be1eda0/PyYAML-6.0.1.tar.gz"
    sha256 "bfdf460b1736c775f2ba9f6a92bca30bc2095067b8a9d77876d1fad6cc3b4a43"
  end

  def install
    venv = virtualenv_create(libexec, "/opt/homebrew/bin/python3.11")
    resources.each do |r|
      r.stage do
        venv.pip_install_and_link(Pathname.pwd)
      end
    end
    venv.pip_install buildpath

    (bin/"textcleaner").write_env_script "#{libexec}/bin/textcleaner", PATH: "#{libexec}/bin:$PATH"
  end

  test do
    system "#{bin}/textcleaner", "--version"
  end
end

class Textcleaner < Formula
  include Language::Python::Virtualenv

  desc "Text cleaning tool for LLM processing"
  homepage "https://github.com/emil7051/textcleaner"
  url "https://github.com/emil7051/textcleaner/archive/refs/tags/v0.5.4.tar.gz"
  sha256 "db16005706c5f45d1d504b69f8ae4866472653975f45cc106a0635e23cbafb4a"
  license "MIT"
  head "https://github.com/emil7051/textcleaner.git", branch: "main"

  depends_on "python@3.11"
  
  def install
    venv = virtualenv_create(libexec, Formula["python@3.11"].opt_bin/"python3")
    venv.pip_install buildpath

    (bin/"textcleaner").write_env_script "#{libexec}/bin/textcleaner", PATH: "#{libexec}/bin:$PATH"
  end

  test do
    system "#{bin}/textcleaner", "--version"
  end
end

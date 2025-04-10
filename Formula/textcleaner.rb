class Textcleaner < Formula
  desc "Convert various file formats to clean, LLM-friendly text"
  homepage "https://github.com/emil7051/textcleaner"
  url "https://github.com/emil7051/textcleaner/archive/refs/tags/v0.5.4.tar.gz"
  sha256 "db16005706c5f45d1d504b69f8ae4866472653975f45cc106a0635e23cbafb4a"
  license "MIT"
  version "0.5.4"

  depends_on "python@3.11"
  depends_on "pypdf"

  def install
    # ... existing install code ...
  end

  test do
    # ... existing test code ...
  end
end 
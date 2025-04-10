class Textcleaner < Formula
  include Language::Python::Virtualenv

  desc "Text cleaning tool for LLM processing"
  homepage "https://github.com/emil7051/textcleaner"
  url "https://github.com/emil7051/textcleaner/archive/refs/tags/v0.5.7.tar.gz"
  sha256 "fb997e7b9c8bb0913cfb776213fc862cf38e57790e62995a2e97ffe52e4de111"
  license "MIT"
  head "https://github.com/emil7051/textcleaner.git", branch: "main"

  depends_on "python@3.11"

  # Define resources for all dependencies from pyproject.toml
  resource "pypdf" do
    url "https://files.pythonhosted.org/packages/source/p/pypdf/pypdf-4.3.1.tar.gz"
    sha256 "2ddc1e31b0d49f1de0b38681e30fcc5697732f1a46622204074b9839c4897d1c"
  end

  resource "pdfminer.six" do
    url "https://files.pythonhosted.org/packages/source/p/pdfminer.six/pdfminer.six-20240701.tar.gz"
    sha256 "622c618417cd37c32a1a6257b6d61d3d8d701b601939172ec924a84cb6d16a48"
  end

  resource "python-docx" do
    url "https://files.pythonhosted.org/packages/source/p/python-docx/python_docx-1.1.2.tar.gz"
    sha256 "e15912c39365eb8d327f767ebd6635977c41fe52a55856a279395a871f483e74"
  end

  resource "openpyxl" do
    url "https://files.pythonhosted.org/packages/source/o/openpyxl/openpyxl-3.1.5.tar.gz"
    sha256 "f8b8c245679c6cb97193583a6f2e08b631806186bb958b612b08a31cf01cf5c2"
  end

  resource "python-pptx" do
    url "https://files.pythonhosted.org/packages/source/p/python-pptx/python-pptx-0.6.23.tar.gz"
    sha256 "855d864804d09352b60b0405389719f508247080f637e6116a5f3a2a1fd45f61"
  end

  resource "pandas" do
    url "https://files.pythonhosted.org/packages/source/p/pandas/pandas-2.2.2.tar.gz"
    sha256 "779ea8595a8170913979350f21c1f87d31b8be986f4799eef5c796af69d7919b"
  end

  resource "beautifulsoup4" do
    url "https://files.pythonhosted.org/packages/source/b/beautifulsoup4/beautifulsoup4-4.12.3.tar.gz"
    sha256 "968845a2675748121103b684d544a1162e59723e08ce68a1844cb924159909a2"
  end

  resource "nltk" do
    url "https://files.pythonhosted.org/packages/source/n/nltk/nltk-3.8.1.tar.gz"
    sha256 "4881d00d8c98613fce937b00b1b425b7528f821da15b82c2044c65709e647565"
  end

  resource "pyyaml" do
    url "https://files.pythonhosted.org/packages/source/P/PyYAML/PyYAML-6.0.1.tar.gz"
    sha256 "cdF91fe81d94e04610b95474ab9b4e4bd2f5d09129334a4b284f7e6e6c656030"
  end

  resource "click" do
    url "https://files.pythonhosted.org/packages/source/c/click/click-8.1.7.tar.gz"
    sha256 "ca98ea624a4f809e323257804655fadb1eda59c08a253d10340d8d2704195e01"
  end

  resource "tqdm" do
    url "https://files.pythonhosted.org/packages/source/t/tqdm/tqdm-4.66.4.tar.gz"
    sha256 "c49b2e56f91613d7a8698d0a248598e2a516e3bd69c93796688cd6964e17e3a7"
  end

  resource "xlrd" do
    url "https://files.pythonhosted.org/packages/source/x/xlrd/xlrd-2.0.1.tar.gz"
    sha256 "5fee6e10409c92538617c8d583a27415743491b399197f2602011589316f65c8"
  end

  resource "lxml" do
    url "https://files.pythonhosted.org/packages/source/l/lxml/lxml-5.2.2.tar.gz"
    sha256 "f29a7607139a363adc4e75c8e3a74802f46a1139ff7a422e67f08ce4180d540d"
  end

  resource "requests" do
    url "https://files.pythonhosted.org/packages/source/r/requests/requests-2.32.3.tar.gz"
    sha256 "6128b1e3d5e1c96a834b2a3e1357a6e8af7e185f5251c69f04cab6350b800c99"
  end

  resource "regex" do
    url "https://files.pythonhosted.org/packages/source/r/regex/regex-2024.7.24.tar.gz"
    sha256 "c0b63735f997f1b1a8180e3904311b3d06883dd002a61a1d9f15c23b565315a4"
  end

  resource "psutil" do
    url "https://files.pythonhosted.org/packages/source/p/psutil/psutil-6.0.0.tar.gz"
    sha256 "c98913204b71576016b9d78501762231e9e561509118e3887b95592da1634910"
  end

  resource "tiktoken" do
    url "https://files.pythonhosted.org/packages/source/t/tiktoken/tiktoken-0.7.0.tar.gz"
    sha256 "c90192d314d9a824de319c1b74a85c2c58a05d414f212db465233c8bec689b95"
  end

  resource "markdown-it-py" do
    url "https://files.pythonhosted.org/packages/source/m/markdown-it-py/markdown-it-py-3.0.0.tar.gz"
    sha256 "e0ab0cf7a77f0c28bb0dde7075c47213548ac658388e434e7b1e11b87142f7a7"
  end

  resource "bleach" do
    url "https://files.pythonhosted.org/packages/source/b/bleach/bleach-6.1.0.tar.gz"
    sha256 "e0a2f13f08e81080c80788e3449b2e53a2696a61131e633db2b87d32221f105a"
  end

  # Dependencies of dependencies (add as needed based on install errors)
  resource "soupsieve" do
    url "https://files.pythonhosted.org/packages/source/s/soupsieve/soupsieve-2.5.tar.gz"
    sha256 "bb7b76435d583347e44a7c0c2c9d2108565e052d08a9b1d4456e8d7cc59720c8"
  end

  resource "webencodings" do
    url "https://files.pythonhosted.org/packages/source/w/webencodings/webencodings-0.5.1.tar.gz"
    sha256 "b36a1c245f2d304965eb4e0a82848379241dc04b865afcc4aab16748686e0fc9"
  end

  resource "charset-normalizer" do
    url "https://files.pythonhosted.org/packages/source/c/charset-normalizer/charset-normalizer-3.3.2.tar.gz"
    sha256 "89757a696a1a5188a34e8003c627420b8a887f5a684745d419f2842e0d98c6c5"
  end

  resource "idna" do
    url "https://files.pythonhosted.org/packages/source/i/idna/idna-3.7.tar.gz"
    sha256 "d90a95b91187f7ef604e655e74348f80f2333d9c36c77e8bb90595111a522a17"
  end

  resource "urllib3" do
    url "https://files.pythonhosted.org/packages/source/u/urllib3/urllib3-2.2.2.tar.gz"
    sha256 "58998a22055801b0e8182e2f48d3f388f23f501e9a82d40d0308d4c85abfd680"
  end

  resource "certifi" do
    url "https://files.pythonhosted.org/packages/source/c/certifi/certifi-2024.7.4.tar.gz"
    sha256 "e8b8614350767a196095e1043a601528a5564207bd2812f0e85a89a4d96f0379"
  end

  resource "six" do
    url "https://files.pythonhosted.org/packages/source/s/six/six-1.16.0.tar.gz"
    sha256 "1e61c37477a1626458e36f7b1d82aa5c9b094fa4802892072e49de9c60c4c926"
  end

  resource "numpy" do
    url "https://files.pythonhosted.org/packages/source/n/numpy/numpy-1.26.4.tar.gz"
    sha256 "3a06b4411688628a415d775672c9e870c39fe1b4a06d9117d8b8ca4b46e00a7d"
  end

  resource "python-dateutil" do
    url "https://files.pythonhosted.org/packages/source/p/python-dateutil/python-dateutil-2.9.0.post0.tar.gz"
    sha256 "015e76b526736a92a13d66a452a15ee745f8e69a3a91719b5ae3a7173a0a7d77"
  end

  resource "pytz" do
    url "https://files.pythonhosted.org/packages/source/p/pytz/pytz-2024.1.tar.gz"
    sha256 "4d37759d701d3b7384f5f075e157469f1f979171312c6f37f9c4537e793e9a8c"
  end

  resource "tzdata" do
    url "https://files.pythonhosted.org/packages/source/t/tzdata/tzdata-2024.1.tar.gz"
    sha256 "35d0a9057e47980771380a03481c815f3709438a7144a32e9b687961b0771369"
  end

  resource "joblib" do
    url "https://files.pythonhosted.org/packages/source/j/joblib/joblib-1.4.2.tar.gz"
    sha256 "8d4f0a7b832e29d0c5cd19128677e7b7b719b2179389e59e67d795eb9a8f2763"
  end

  resource "mdurl" do
    url "https://files.pythonhosted.org/packages/source/m/mdurl/mdurl-0.1.2.tar.gz"
    sha256 "90b88a05819e04a46d0f11e849a9f0d3d8e056673892e7e3d842916e691713e8"
  end

  resource "pillow" do
    url "https://files.pythonhosted.org/packages/source/p/pillow/pillow-10.4.0.tar.gz"
    sha256 "e71ce8257540682d723da8f389d40e1a3d3813800d17a118680a5d1b7b4e079f"
  end

  resource "et-xmlfile" do
    url "https://files.pythonhosted.org/packages/source/e/et_xmlfile/et_xmlfile-1.1.0.tar.gz"
    sha256 "7a71d140ee0a8b626c914030774860f51945545fd00f85a45e6bd559c5d19957"
  end

  def install
    # Create venv
    venv = virtualenv_create(libexec, "python3.11")

    # Install all resources
    resources.each do |r|
      venv.pip_install r
    end

    # Install the package itself (dependencies should already be installed)
    venv.pip_install_and_link "."

    # Ensure the executable script is created (pip_install_and_link might handle this, but explicit is safer)
    (bin/"textcleaner").write_env_script libexec/"bin/textcleaner", PATH: "#{libexec}/bin:$PATH"
  end

  test do
    system "#{bin}/textcleaner", "--version"
  end
end

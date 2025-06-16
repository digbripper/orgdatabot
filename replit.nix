{ pkgs }: {
  deps = [
    pkgs.bash
    pkgs.glibcLocales
    pkgs.rustc
    pkgs.libiconv
    pkgs.cargo
    pkgs.python311Full
    pkgs.python311Packages.streamlit
    pkgs.python311Packages.pandas
    pkgs.python311Packages.requests
    pkgs.python311Packages.openai
    pkgs.python311Packages.faiss
    pkgs.python311Packages.setuptools
  ];
}

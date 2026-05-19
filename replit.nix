{pkgs}: {
  deps = [
    pkgs.python312Packages.opencv4
    pkgs.python312Packages.face-recognition
    pkgs.python312Packages.dlib
    pkgs.libgcc
    pkgs.gcc
    pkgs.dlib
    pkgs.cmake
  ];
}

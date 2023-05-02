import sys
from distutils.command.build_ext import build_ext

from setuptools import find_packages
import subprocess
from difflib import get_close_matches
from glob import glob
import os
import platform

from distutils.core import setup, Extension

# read the contents of your README file
from pathlib import Path
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()


def find_pkg_dirs(package):
    close_matches = get_close_matches(package.lower(),
                                      os.environ["PATH"].lower().split(';'),
                                      cutoff=0)
    dll_dir = None
    for close_match in close_matches:
        if (os.path.exists(close_match)
                and glob(os.path.join(close_match, '*.dll'))):
            dll_dir = close_match
            break
    if dll_dir is None:
        raise Exception(
            f"Could not find required package: {package}. "
            "Add directory containing .dll files to system environment path."
        )
    dll_dir_split = dll_dir.replace('\\', '/').split('/')
    root = get_close_matches(package.lower(), dll_dir_split, cutoff=0)[0]
    root_dir = '/'.join(dll_dir_split[:dll_dir_split.index(root) + 1])
    return os.path.normpath(root_dir), os.path.normpath(dll_dir)


def pkgconfig_windows(package, kw):
    is_x64 = platform.machine().endswith('64')
    root_dir, dll_dir = find_pkg_dirs(package)
    include_dir = None
    library_dir = None
    parent = None
    while parent != root_dir:
        parent = os.path.dirname(dll_dir if parent is None else parent)
        if include_dir is None and os.path.exists(os.path.join(parent, 'include')):
            include_dir = os.path.join(parent, 'include')
        library_dirs = set()
        libraries = glob(os.path.join(parent, '**', 'lib', '**', '*.lib'),
                         recursive=True)
        for library in libraries:
            if ((is_x64 and 'x86' in library)
                    or (not is_x64 and 'x64' in library)):
                continue
            library_dirs.add(os.path.dirname(library))
        if library_dir is None and library_dirs:
            library_dir = sorted(library_dirs)[-1]
        if include_dir and library_dir:
            libraries = [os.path.splitext(library)[0]
                         for library in glob(os.path.join(library_dir, '*.lib'))]
            break
    if not include_dir or not library_dir:
        raise Exception(f"Could not find required package: {package}.")
    kw.setdefault('include_dirs', []).append(include_dir)
    kw.setdefault('library_dirs', []).append(library_dir)
    kw.setdefault('libraries', []).extend(libraries)
    return kw


def pkgconfig(package, kw):
    flag_map = {'-I': 'include_dirs', '-L': 'library_dirs', '-l': 'libraries'}
    output = subprocess.getoutput(
        'pkg-config --cflags --libs {}'.format(package))
    if 'not found' in output:
        raise RuntimeError(f"Could not find required package: {package}.")
    for token in output.strip().split():
        kw.setdefault(flag_map.get(token[:2]), []).append(token[2:])
    return kw


# sources = ['./libffcv/libffcv.cpp']
#
# extension_kwargs = {
#     'sources': sources,
#     'include_dirs': []
# }
# if platform.system() == 'Windows':
#     extension_kwargs = pkgconfig_windows('opencv4', extension_kwargs)
#     extension_kwargs = pkgconfig_windows('libturbojpeg', extension_kwargs)
#
#     extension_kwargs = pkgconfig_windows('pthread', extension_kwargs)
# else:
#     try:
#         extension_kwargs = pkgconfig('opencv4', extension_kwargs)
#     except RuntimeError:
#         extension_kwargs = pkgconfig('opencv', extension_kwargs)
#     extension_kwargs = pkgconfig('libturbojpeg', extension_kwargs)
#
#     extension_kwargs['libraries'].append('pthread')
#
#
# libffcv = Extension('ffcv._libffcv',
#                     **extension_kwargs)

class CMakeExtension(Extension):
    def __init__(self, name, cmake_lists_dir='.', sources=[], **kwa):
        Extension.__init__(self, name, sources=sources, **kwa)
        self.cmake_lists_dir = os.path.abspath(cmake_lists_dir)


class CMakeBuild(build_ext):
    def build_extensions(self):
        try:
            out = subprocess.check_output(['cmake', '--version'])
        except OSError:
            raise RuntimeError('Cannot find CMake executable')

        for ext in self.extensions:
            extdir = os.path.abspath(os.path.dirname(self.get_ext_fullpath(ext.name)))

            cmake_args = [
                '-DCMAKE_LIBRARY_OUTPUT_DIRECTORY={}'.format(extdir),
                '-DCMAKE_ARCHIVE_OUTPUT_DIRECTORY={}'.format(self.build_temp),
            ]

            if not os.path.exists(self.build_temp):
                os.makedirs(self.build_temp)

            # Config and build the extension
            subprocess.check_call(['cmake', ext.cmake_lists_dir] + cmake_args,
                                  cwd=self.build_temp)
            subprocess.check_call(['cmake', '--build', '.'],
                                  cwd=self.build_temp)


libffcv = CMakeExtension('ffcv._libffcv')


setup(name='ffcv',
      version='1.0.1',
      description=' FFCV: Fast Forward Computer Vision ',
      author='MadryLab',
      author_email='ffcv@mit.edu',
      url='https://github.com/libffcv/ffcv',
      license_files = ('LICENSE.txt',),
      packages=find_packages(),
      long_description=long_description,
      long_description_content_type='text/markdown',
      ext_modules=[libffcv],
      cmdclass={'build_ext': CMakeBuild},
      install_requires=[
          'terminaltables',
          'pytorch_pfn_extras',
          'fastargs',
          'opencv-python',
          'assertpy',
          'tqdm',
          'psutil',
          'numba',
      ])

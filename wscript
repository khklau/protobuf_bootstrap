import hashlib
import os
import shutil
import subprocess
import tarfile
import urllib
import zipfile
from waflib import Logs
from waflib.extras.preparation import PreparationContext
from waflib.extras.build_status import BuildStatus
from waflib.extras.filesystem_utils import removeSubdir
from waflib.extras.mirror import MirroredTarFile, MirroredZipFile

__downloadUrl = 'https://protobuf.googlecode.com/files/%s'
__posixFile = 'protobuf-2.5.0.tar.gz'
__posixSha256Checksum = '\xc5\x5a\xa3\xdc\x53\x8e\x6f\xd5\xea\xf7\x32\xf4\xeb\x6b\x98\xbd\xcb\x7c\xed\xb5\xb9\x1d\x3b\x5b\xdc\xf2\x9c\x98\xc2\x93\xf5\x8e'
__ntFile = 'protobuf-2.5.0.zip'
__ntSha256Checksum = '\x25\xab\xfc\x11\x5e\x90\x44\xe9\xb3\xf5\x75\x59\xec\xef\x7d\xa2\xb5\xbc\x9f\xa0\x6c\x22\xe1\xa4\xab\x2c\xf7\x9a\xff\xe2\x93\x45'
__srcDir = 'src'

def options(optCtx):
    optCtx.load('dep_resolver')

def prepare(prepCtx):
    prepCtx.options.dep_base_dir = prepCtx.srcnode.find_dir('..').abspath()
    prepCtx.load('dep_resolver')
    status = BuildStatus.init(prepCtx.path.abspath())
    if status.isSuccess():
	prepCtx.msg('Preparation already complete', 'skipping')
	return
    if os.name == 'posix':
	file = MirroredTarFile(
		__posixSha256Checksum,
		__downloadUrl % __posixFile,
		os.path.join(prepCtx.path.abspath(), __posixFile))
    elif os.name == 'nt':
	file = MirroredZipFile(
		__ntSha256Checksum,
		__downloadUrl % __ntFile,
		os.path.join(prepCtx.path.abspath(), __ntFile))
    else:
	prepCtx.fatal('Unsupported OS %s' % os.name)
    prepCtx.msg('Synchronising', file.getSrcUrl())
    if file.sync(10):
	prepCtx.msg('Saved to', file.getTgtPath())
    else:
	prepCtx.fatal('Synchronisation failed')
    extractDir = 'protobuf-2.5.0'
    removeSubdir(prepCtx.path.abspath(), __srcDir, extractDir, 'bin', 'lib', 'include')
    prepCtx.start_msg('Extracting files to')
    file.extract(prepCtx.path.abspath())
    os.rename(extractDir, __srcDir)
    prepCtx.end_msg(os.path.join(prepCtx.path.abspath(), __srcDir))

def configure(confCtx):
    confCtx.load('dep_resolver')
    status = BuildStatus.init(confCtx.path.abspath())
    if status.isSuccess():
	confCtx.msg('Configuration already complete', 'skipping')
	return
    srcPath = os.path.join(confCtx.path.abspath(), __srcDir)
    os.chdir(srcPath)
    if os.name == 'posix':
	returnCode = subprocess.call([
		'sh',
		os.path.join(srcPath, 'configure'),
		'--prefix=%s' % confCtx.srcnode.abspath()])
	if returnCode != 0:
	    confCtx.fatal('Protobuf configure failed: %d' % returnCode)
    elif os.name == 'nt':
	# Nothing to do, just use the provided VS solution
	return
    else:
	confCtx.fatal('Unsupported OS %s' % os.name)

def build(buildCtx):
    status = BuildStatus.load(buildCtx.path.abspath())
    if status.isSuccess():
	Logs.pprint('NORMAL', 'Build already complete                   :', sep='')
	Logs.pprint('GREEN', 'skipping')
	return
    srcPath = os.path.join(buildCtx.path.abspath(), __srcDir)
    os.chdir(srcPath)
    if os.name == 'posix':
	returnCode = subprocess.call([
		'make',
		'install'])
    elif os.name == 'nt':
	returnCode = subprocess.call([
		'devenv.com',
		os.path.join(srcPath, 'vsprojects', 'protobuf.sln')])
    else:
	confCtx.fatal('Unsupported OS %s' % os.name)
    if returnCode != 0:
	buildCtx.fatal('Protobuf build failed: %d' % returnCode)
    status.setSuccess()

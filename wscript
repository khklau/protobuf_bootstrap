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

__downloadUrl = 'https://protobuf.googlecode.com/files/%s'
__posixFile = 'protobuf-2.5.0.tar.gz'
__posixSha256Checksum = '\xc5\x5a\xa3\xdc\x53\x8e\x6f\xd5\xea\xf7\x32\xf4\xeb\x6b\x98\xbd\xcb\x7c\xed\xb5\xb9\x1d\x3b\x5b\xdc\xf2\x9c\x98\xc2\x93\xf5\x8e'
__ntFile = 'protobuf-2.5.0.zip'
__ntSha256Checksum = '\x25\xab\xfc\x11\x5e\x90\x44\xe9\xb3\xf5\x75\x59\xec\xef\x7d\xa2\xb5\xbc\x9f\xa0\x6c\x22\xe1\xa4\xab\x2c\xf7\x9a\xff\xe2\x93\x45'
__srcDir = 'src'

def options(optCtx):
    optCtx.load('dep_resolver')

def prepare(prepCtx):
    prepCtx.load('dep_resolver')
    status = BuildStatus.init(prepCtx.path.abspath())
    if status.isSuccess():
	prepCtx.msg('Preparation already complete', 'skipping')
	return
    if os.name == 'posix':
	filePath = os.path.join(prepCtx.path.abspath(), __posixFile)
	url = __downloadUrl % __posixFile
	sha256Checksum = __posixSha256Checksum
    elif os.name == 'nt':
	filePath = os.path.join(prepCtx.path.abspath(), __ntFile)
	url = __downloadUrl % __ntFile
	sha256Checksum = __ntSha256Checksum
    else:
	prepCtx.fatal('Unsupported OS %s' % os.name)
    if os.access(filePath, os.R_OK):
	hasher = hashlib.sha256()
	handle = open(filePath, 'rb')
	try:
	    hasher.update(handle.read())
	finally:
	    handle.close()
	if hasher.digest() != sha256Checksum:
	    os.remove(filePath)
    if os.access(filePath, os.R_OK):
	prepCtx.start_msg('Using existing source file')
	prepCtx.end_msg(filePath)
    else:
	prepCtx.start_msg('Downloading %s' % url)
	triesRemaining = 10
	while triesRemaining > 1:
	    try:
		urllib.urlretrieve(url, filePath)
		break
	    except urllib.ContentTooShortError:
		triesRemaining -= 1
		if os.path.exists(filePath):
		    os.remove(filePath)
	else:
	    prepCtx.fatal('Could not download %s' % url)
	prepCtx.end_msg('Saved to %s' % filePath)
    srcPath = os.path.join(prepCtx.path.abspath(), __srcDir)
    extractPath = os.path.join(prepCtx.path.abspath(), 'protobuf-2.5.0')
    binPath = os.path.join(prepCtx.path.abspath(), 'bin')
    libPath = os.path.join(prepCtx.path.abspath(), 'lib')
    includePath = os.path.join(prepCtx.path.abspath(), 'include')
    for path in [srcPath, extractPath, binPath, libPath, includePath]:
	if os.path.exists(path):
	    if os.path.isdir(path):
		shutil.rmtree(path)
	    else:
		os.remove(path)
    prepCtx.start_msg('Extracting files to')
    if os.name == 'posix':
	handle = tarfile.open(filePath, 'r:*')
	handle.extractall(prepCtx.path.abspath())
    elif os.name == 'nt':
	handle = zipfile.Zipfile(filePath, 'r')
	handle.extractall(prepCtx.path.abspath())
    else:
	prepCtx.fatal('Unsupported OS %s' % os.name)
    os.rename(extractPath, srcPath)
    prepCtx.end_msg(srcPath)

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

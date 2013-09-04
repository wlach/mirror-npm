#!/usr/bin/env python

import httplib2
import json
import os
import sys

http = httplib2.Http()

if len(sys.argv) < 5:
    print "Usage: %s <npm server> <output dir> <server url> [PACKAGE1] [PACKAGE2] ..." % sys.argv[0]
(npmserver, outputdir, serverurl) = sys.argv[1:4]
original_packages_to_mirror = sys.argv[4:]
packages_to_mirror = list(original_packages_to_mirror)

def get_package_url(serverurl, packagename, packagefilename):
    return "%s/%s/-/%s" % (serverurl, packagename, packagefilename)

mirrored_packages = []

while len(packages_to_mirror) > 0:
    packagename = packages_to_mirror.pop()
    mirrored_packages.append(packagename)
    print "Downloading %s (currently remaining: %s)" % (packagename, len(packages_to_mirror))

    # get package info
    packageinfourl = "%s/%s" % (npmserver, packagename)
    (response, packageinfocontent) = http.request(packageinfourl, 'GET')
    packageinfo = json.loads(packageinfocontent)

    # no longer-existent package
    if not packageinfo.get('versions'):
        continue

    for version in packageinfo['versions'].keys():
        packagefilename = os.path.basename(packageinfo['versions'][version]['dist']['tarball'])
        packageinfo['versions'][version]['dist']['tarball'] = get_package_url(
            serverurl, packagename, packagefilename)
        packagebasepath = os.path.join(outputdir, packagename)
        if not os.path.isdir(packagebasepath):
            os.makedirs(packagebasepath)
        with open(os.path.join(packagebasepath, 'index.json'), 'w') as f:
            f.write(json.dumps(packageinfo))

    # get actual packages
    for version in packageinfo['versions']:
        print "--> %s" % version
        versioninfopath = os.path.join(outputdir, packagename)
        if not os.path.isdir(versioninfopath):
            os.mkdir(versioninfopath)
        versionurl = "%s/%s/%s" % (npmserver, packagename, version)
        (response, versioncontent) = http.request(versionurl, 'GET')
        versioninfo = json.loads(versioncontent)
        packageurl = versioninfo['dist']['tarball']
        packagepath = os.path.join(outputdir, packagename, '-')
        if not os.path.isdir(packagepath):
            os.makedirs(packagepath)
        packagefilename = os.path.join(packagepath, os.path.basename(packageurl))
        if not os.path.isfile(packagefilename):
            # redownloading full .tar.gz's is expensive, so only do this if we
            # haven't downloaded the file already
            (response, packagecontent) = http.request(packageurl, 'GET')
            print "---> %s -> %s" % (packageurl, packagefilename)
            with open(packagefilename, 'w') as f:
                f.write(packagecontent)
        versioninfo['dist']['tarball'] = get_package_url(serverurl,
                                                         packagename,
                                                         os.path.basename(packageurl))
        with open(os.path.join(versioninfopath, version), 'w') as f:
            f.write(json.dumps(versioninfo))
        versioninfo = packageinfo['versions'][version]
        dependencies = versioninfo.get('dependencies', {}).keys()
        if packagename in original_packages_to_mirror:
            dependencies += versioninfo.get('devDependencies', {}).keys()
        for dependency in dependencies:
            if dependency not in mirrored_packages and dependency not in packages_to_mirror:
                packages_to_mirror.append(dependency)

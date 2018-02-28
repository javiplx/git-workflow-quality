#!/usr/bin/python

from distutils.core import setup

setup(
    name = 'git-workflow-quality',
    version = '0.99',
    description = 'Quality assessment of git workflows & repositories',
    author = 'Javier Palacios',
    author_email = 'javiplx@gmail.com',
    license = 'GPLv2',
    url = 'http://github.com/javiplx/git-workflow-quality',
    scripts = [ 'git-workflow-quality' ],
    packages = [ 'git_workflow_quality' ]
    )



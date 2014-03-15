Git Time
========

Estimate time spent programming with git metadata. Gittime shows u metadata.
You make guesses.

UI cues taken from [acoomans](https://github.com/acoomans)'s similarly named
[gittime](https://github.com/acoomans/gittime).


Install
-------

Requires [pygit2](https://github.com/libgit2/pygit2). On linux, if you like
virtualenv, save yourself a headache with [venvgit2](https://github.com/uniphil/venvgit2).

No current plans to throw this on pypi or anything, it's mostly a one-off (which
may become a several-off) for myself to come up with some hours on some projects.


Usage
-----

```bash
$ ./gittime <repository> [<tree-ish first> [<tree-ish last>]] [-u <email>]
```

### Example

```
$ ./gittime git@github.com:uniphil/commit--blog.git

* ff228dc initial sketch with github oauth
  Sunday, Feb 16, 2:13pm by uniphil@gmail.com
  Total line changes: +166 -0.
    +127 commitblog.py
    +24 manage.py
    +11 dev-requirements.txt
    +4 .gitignore
  Time since previous commit: (n/a; first commit)
  
Estimate time spent: 3h

* 7da8a0a Add requirements for production
  Sunday, Feb 16, 2:14pm by uniphil@gmail.com
  Total line changes: +11 -3
    +11 requirements.txt
    -3 dev-requirements.txt
  Time since previous commit 1m

Estimate time spent[1m]:

... and so on
```
